import os
import json
from typing import Dict, List, Any, Optional
import traceback
from pymongo import MongoClient
from bson import ObjectId
import googlemaps


def extract_address_components(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrai componentes do endereço do resultado do Google Maps Geocoding.
    """
    address_data = {
        "street": {"id": -1, "name": ""},
        "neighborhood": {"id": "", "name": ""},
        "city": "",
        "state": "",
        "address": {"street": "", "number": "", "city": "", "state": ""},
    }

    if not result or "address_components" not in result:
        return address_data

    # Mapeamento de tipos do Google para nossos campos
    for component in result["address_components"]:
        types = component["types"]

        if "route" in types:
            address_data["street"]["name"] = component["long_name"]
            address_data["address"]["street"] = component["long_name"]

        elif "street_number" in types:
            address_data["address"]["number"] = component["long_name"]

        elif "sublocality_level_1" in types or "sublocality" in types:
            address_data["neighborhood"]["name"] = component["long_name"]

        elif "administrative_area_level_2" in types:
            address_data["city"] = component["long_name"]
            address_data["address"]["city"] = component["long_name"]

        elif "administrative_area_level_1" in types:
            address_data["state"] = component["short_name"]
            address_data["address"]["state"] = component["short_name"]

    return address_data


def process_lot_address(
    mongodb_uri: str,
    google_maps_api_key: str,
    doc_id: Optional[str] = None,
    confidence: float = 0.62,
) -> List[Dict]:
    """
    Processa o endereço dos lotes usando Google Maps Geocoding.

    Args:
        mongodb_uri (str): URI de conexão com MongoDB
        google_maps_api_key (str): Chave da API do Google Maps
        doc_id (Optional[str]): ID específico do documento
        confidence (float): Valor mínimo de confiança

    Returns:
        List[Dict]: Lista de documentos processados
    """
    print("\n=== Iniciando processamento de endereços ===")
    print(f"Filtro de confiança: >= {confidence}")

    client = None
    try:
        # Inicializa cliente do Google Maps
        gmaps = googlemaps.Client(key=google_maps_api_key)

        # Estabelece conexão com MongoDB
        client = MongoClient(mongodb_uri)
        db = client["gethome-01-hml"]
        collection = db["lots_detections_details_hmg"]

        # Define query base
        query = {
            "$and": [
                {"coordinates": {"$exists": True}},
                {"detection_result.confidence": {"$gte": confidence}},
            ]
        }

        # Se foi especificado um ID, adiciona à query
        if doc_id:
            query["_id"] = ObjectId(doc_id)

        total_docs = collection.count_documents(query)
        print(f"\nTotal de documentos para processar: {total_docs}")

        if total_docs == 0:
            print("Nenhum documento encontrado para processar")
            return []

        processed_docs = []
        errors = 0

        for doc in collection.find(query):
            try:
                current_doc_id = str(doc["_id"])
                print(f"\nProcessando documento {current_doc_id}")

                # Obtém coordenadas
                coordinates = doc.get("coordinates", {})
                lat = coordinates.get("lat")
                lon = coordinates.get("lon")

                if not lat or not lon:
                    print(f"Coordenadas não encontradas para {current_doc_id}")
                    errors += 1
                    continue

                # Faz geocoding reverso
                result = gmaps.reverse_geocode((lat, lon))[0]

                print(result)

                # Extrai componentes do endereço
                address_data = extract_address_components(result)

                # Atualiza o documento
                update_data = {
                    "city": address_data["city"],
                    "state": address_data["state"],
                    "street": address_data["street"],
                    "neighborhood": address_data["neighborhood"],
                    "lot_details.address": [address_data["address"]],
                }

                result = collection.update_one(
                    {"_id": doc["_id"]}, {"$set": update_data}
                )

                if result.modified_count > 0:
                    print(f"✓ Endereço atualizado para {current_doc_id}")
                    print(f"  Rua: {address_data['street']['name']}")
                    print(f"  Bairro: {address_data['neighborhood']['name']}")
                    print(f"  Cidade: {address_data['city']}")
                    print(f"  Estado: {address_data['state']}")

                    # Obtém o documento atualizado
                    updated_doc = collection.find_one({"_id": doc["_id"]})
                    processed_docs.append(updated_doc)
                else:
                    print(f"⚠️ Documento {current_doc_id} não foi atualizado")
                    errors += 1

            except Exception as e:
                errors += 1
                print(f"Erro ao processar documento {current_doc_id}: {str(e)}")
                traceback.print_exc()
                continue

        print("\n=== Resumo do processamento ===")
        print(f"Total de documentos: {total_docs}")
        print(f"Processados com sucesso: {len(processed_docs)}")
        print(f"Erros: {errors}")

        return processed_docs

    except Exception as e:
        print(f"Erro durante o processamento: {str(e)}")
        return []

    finally:
        if client:
            try:
                client.close()
                print("✅ Conexão com MongoDB fechada com sucesso")
            except Exception as e:
                print(f"⚠️ Erro ao fechar conexão com MongoDB: {e}")
