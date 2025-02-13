import os
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
import pyproj
import traceback
import utm
from pymongo import MongoClient
from bson import ObjectId


def convert_to_utm(lat: float, lon: float) -> Tuple[float, float, int]:
    """
    Convert lat/lon to UTM coordinates.

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        Tuple of (easting, northing, zone)
    """
    # Get UTM zone
    zone = int((lon + 180) / 6) + 1

    # Create projections
    wgs84 = pyproj.CRS("EPSG:4326")  # WGS84
    utm = pyproj.CRS(f"+proj=utm +zone={zone} +datum=WGS84")

    # Create transformer
    transformer = pyproj.Transformer.from_crs(wgs84, utm, always_xy=True)

    # Convert coordinates
    easting, northing = transformer.transform(lon, lat)

    return easting, northing, zone


def process_lots_utm_coordinates(
    mongodb_uri: str,
    google_place_id: str = None,
    doc_id: str = None,
    confidence: float = 0.62,
) -> List[Dict]:
    """
    Processa coordenadas UTM para pontos de lotes que já possuem lat/lon e elevação.

    Args:
        mongodb_uri (str): URI de conexão com MongoDB
        google_place_id (str): ID do local Google para filtrar
        doc_id (str): ID específico do documento (opcional)
        confidence (float): Valor mínimo de confiança para processar o documento (default: 0.62)

    Returns:
        List[Dict]: Lista de documentos processados
    """
    print("\n=== Iniciando processamento de coordenadas UTM ===")
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
                {"lot_details.elevations": {"$exists": True}},
                {"lot_details.points_utm": {"$exists": False}},
                {"detection_result.confidence": {"$gte": confidence}},
            ]
        }

        # Se foi especificado um ID ou google_place_id, adiciona à query
        if doc_id:
            query["_id"] = ObjectId(doc_id)
            print(f"Processando documento específico: {doc_id}")
        elif google_place_id:
            query["google_place_id"] = google_place_id
            print(f"Processando todos os documentos para: {google_place_id}")

        total_docs = collection.count_documents(query)
        print(f"Total de documentos para processar: {total_docs}")

        if total_docs == 0:
            print("Nenhum documento encontrado para processar")
            return []

        processed_docs = []
        errors = 0

        for i, doc in enumerate(collection.find(query), 1):
            try:
                print(f"\nProcessando documento {i}/{total_docs}")
                print(f"ID: {doc['_id']}")
                print(f"Rua: {doc.get('street_name', 'N/A')}")

                # Obtém pontos lat/lon e elevações do novo formato
                points_lat_lon = (
                    doc.get("lot_details", {})
                    .get("point_colors", {})
                    .get("points_lat_lon", [])
                )
                elevations = doc.get("lot_details", {}).get("elevations", [])

                if len(points_lat_lon) != len(elevations):
                    print(
                        f"ERRO: Número diferente de pontos ({len(points_lat_lon)}) e elevações ({len(elevations)})"
                    )
                    errors += 1
                    continue

                print(f"Processando {len(points_lat_lon)} pontos...")

                # Lista para armazenar coordenadas UTM
                points_utm = []

                # Processa cada ponto
                for (lat, lon), elevation in zip(points_lat_lon, elevations):
                    try:
                        # Converte para UTM
                        easting, northing, zone_number, zone_letter = (
                            utm.from_latlon(lat, lon)
                        )

                        # Armazena como [x, y, z, zone_number, zone_letter]
                        points_utm.append(
                            [
                                round(easting, 3),  # x
                                round(northing, 3),  # y
                                round(float(elevation), 3),  # z
                                zone_number,  # zone_number
                                zone_letter,  # zone_letter
                            ]
                        )

                    except Exception as e:
                        print(
                            f"ERRO ao converter ponto ({lat}, {lon}): {str(e)}"
                        )
                        points_utm.append([None, None, None, None, None])

                # Verifica se todos os pontos têm a mesma zona UTM
                unique_zones = set(
                    (p[3], p[4]) for p in points_utm if p[3] is not None
                )
                if len(unique_zones) > 1:
                    print(
                        f"AVISO: Pontos em diferentes zonas UTM: {unique_zones}"
                    )

                # Atualiza documento com as coordenadas UTM no novo formato
                if "lot_details" not in doc:
                    doc["lot_details"] = {}
                if "point_colors" not in doc["lot_details"]:
                    doc["lot_details"]["point_colors"] = {}

                result = collection.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"lot_details.points_utm": points_utm}},
                )

                if result.modified_count > 0:
                    doc["lot_details"]["points_utm"] = points_utm
                    processed_docs.append(doc)
                    print(f"Documento {doc['_id']} atualizado com sucesso")

                    # Calcula estatísticas das coordenadas
                    valid_points = [p for p in points_utm if p[0] is not None]
                    if valid_points:
                        x_coords = [p[0] for p in valid_points]
                        y_coords = [p[1] for p in valid_points]
                        z_coords = [p[2] for p in valid_points]
                        print(f"Estatísticas UTM:")
                        print(
                            f"X: min={min(x_coords):.1f}, max={max(x_coords):.1f}"
                        )
                        print(
                            f"Y: min={min(y_coords):.1f}, max={max(y_coords):.1f}"
                        )
                        print(
                            f"Z: min={min(z_coords):.1f}, max={max(z_coords):.1f}"
                        )

            except Exception as e:
                errors += 1
                print(f"ERRO ao processar documento {doc.get('_id')}: {str(e)}")
                traceback.print_exc()
                continue

        print("\n=== Resumo do processamento UTM ===")
        if google_place_id:
            print(f"Google Place ID: {google_place_id}")
        if doc_id:
            print(f"ID do documento: {doc_id}")
        print(f"Total de documentos: {total_docs}")
        print(f"Processados com sucesso: {len(processed_docs)}")
        print(f"Erros: {errors}")
        print("================================\n")

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
