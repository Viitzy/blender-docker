import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np
import traceback
from pymongo import MongoClient
from bson import ObjectId
from geopy.distance import geodesic


def calculate_cardinal_points(
    center_lat: float, center_lon: float, distance_meters: float
) -> Dict[str, List[float]]:
    """
    Calcula pontos cardeais a partir de um ponto central.

    Args:
        center_lat (float): Latitude do centro
        center_lon (float): Longitude do centro
        distance_meters (float): Distância em metros

    Returns:
        Dict[str, List[float]]: Dicionário com pontos cardeais
    """
    # Converte distância para graus (aproximadamente)
    distance_deg = distance_meters / 111320  # 1 grau ≈ 111.32 km no equador

    # Calcula pontos cardeais
    cardinal_points = {
        "north": [center_lat + distance_deg, center_lon],
        "south": [center_lat - distance_deg, center_lon],
        "east": [
            center_lat,
            center_lon + distance_deg / np.cos(np.radians(center_lat)),
        ],
        "west": [
            center_lat,
            center_lon - distance_deg / np.cos(np.radians(center_lat)),
        ],
    }

    return cardinal_points


def process_cardinal_points(
    mongodb_uri: str,
    distance_meters: float = 5.0,
    doc_id: Optional[str] = None,
    confidence: float = 0.62,
) -> List[Dict]:
    """
    Processa e adiciona pontos cardeais para lotes.

    Args:
        mongodb_uri (str): URI de conexão com MongoDB
        distance_meters (float): Distância em metros para os pontos cardeais
        doc_id (Optional[str]): ID opcional do documento específico
        confidence (float): Valor mínimo de confiança para processar o documento (default: 0.62)

    Returns:
        List[Dict]: Lista de documentos processados
    """
    print("\n=== Iniciando processamento de pontos cardeais ===")
    print(f"Distância: {distance_meters}m")
    print(f"Filtro de confiança: >= {confidence}")

    client = None
    try:
        # Estabelece conexão com MongoDB
        client = MongoClient(mongodb_uri)
        db = client["gethome-01-hml"]
        collection = db["lots_detections_details_hmg"]

        # Monta a query base
        query = {
            "$and": [
                {"lot_details.point_colors.points_lat_lon": {"$exists": True}},
                {"lot_details.cardinal_points": {"$exists": False}},
                {"detection_result.confidence": {"$gte": confidence}},
            ]
        }

        # Se foi especificado um ID, adiciona à query
        if doc_id:
            query["_id"] = ObjectId(doc_id)
            print(f"Processando documento específico: {doc_id}")

        total_docs = collection.count_documents(query)
        print(f"Total de documentos para processar: {total_docs}")

        if total_docs == 0:
            print("Nenhum documento encontrado")
            return []

        processed_docs = []
        errors = 0

        for doc in collection.find(query):
            try:
                doc_id = str(doc["_id"])
                print(f"\nProcessando documento: {doc_id}")
                print(f"Rua: {doc.get('street_name', 'N/A')}")

                # Verifica se já tem point_colors
                points_lat_lon = (
                    doc.get("lot_details", {})
                    .get("point_colors", {})
                    .get("points_lat_lon", [])
                )

                # Calcula centro do polígono se houver pontos
                if points_lat_lon:
                    points = np.array(points_lat_lon)
                    center_lat = np.mean(points[:, 0])
                    center_lon = np.mean(points[:, 1])
                    print(
                        f"Centro calculado: ({center_lat:.6f}, {center_lon:.6f})"
                    )
                else:
                    print("AVISO: Usando coordenadas do documento como centro")
                    center_lat = doc.get("latitude")
                    center_lon = doc.get("longitude")

                if not (center_lat and center_lon):
                    print("ERRO: Não foi possível determinar o centro")
                    errors += 1
                    continue

                # Calcula pontos cardeais
                cardinal_points = calculate_cardinal_points(
                    center_lat, center_lon, distance_meters
                )

                # Adiciona pontos cardeais ao point_colors
                # Atualiza documento com os pontos cardeais no novo formato
                if "lot_details" not in doc:
                    doc["lot_details"] = {}

                # Atualiza documento
                result = collection.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"lot_details.cardinal_points": cardinal_points}},
                )

                if result.modified_count > 0:
                    doc["lot_details"]["cardinal_points"] = cardinal_points
                    processed_docs.append(doc)
                    print("Documento atualizado com sucesso")
                    print("Pontos cardeais adicionados:")
                    for direction, point in cardinal_points.items():
                        print(
                            f"  {direction}: ({point[0]:.6f}, {point[1]:.6f})"
                        )
                else:
                    print("AVISO: Documento não foi modificado")

            except Exception as e:
                errors += 1
                print(f"ERRO ao processar documento {doc.get('_id')}: {str(e)}")
                traceback.print_exc()

        print("\n=== Resumo do processamento ===")
        if doc_id:
            print(f"ID do documento: {doc_id}")
        print(f"Total processado: {len(processed_docs)}")
        print(f"Erros: {errors}")
        print("============================\n")

        return processed_docs

    except Exception as e:
        print(f"Erro durante o processamento: {str(e)}")
        raise

    finally:
        # Fecha a conexão com segurança
        if client:
            try:
                client.close()
                print("✅ Conexão com MongoDB fechada com sucesso")
            except Exception as e:
                print(f"⚠️ Erro ao fechar conexão com MongoDB: {e}")
