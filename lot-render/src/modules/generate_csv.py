from typing import Dict, Any, List, Optional
import pandas as pd
import os
import utm
import json
import traceback
from pathlib import Path
import numpy as np
from pymongo import MongoClient
from bson import ObjectId
from google.cloud import storage
import tempfile


def find_nearest_point_color(
    x: float, y: float, points_data: List[Dict]
) -> str:
    """
    Encontra a cor do ponto mais próximo.

    Args:
        x: Coordenada X do ponto
        y: Coordenada Y do ponto
        points_data: Lista de pontos com suas cores

    Returns:
        str: Cor em formato hexadecimal
    """
    min_dist = float("inf")
    nearest_color = "#000000"

    for point in points_data:
        if point.get("front", 0) == 1:  # Ignora outros pontos da frente
            continue

        dist = ((point["x"] - x) ** 2 + (point["y"] - y) ** 2) ** 0.5
        if dist < min_dist:
            min_dist = dist
            nearest_color = point["hex_color"]

    return nearest_color


def generate_lot_csv(lot_data: Dict[str, Any]) -> pd.DataFrame:
    """
    Gera DataFrame com os pontos do lote formatados.
    """
    points_data = []

    # Verifica se os dados necessários existem
    if "point_colors" not in lot_data:
        raise Exception("Documento não contém a chave 'point_colors'")

    point_colors = lot_data["point_colors"]

    # Verifica se temos as cores ajustadas
    if "colors_adjusted" not in point_colors:
        raise Exception("Documento não contém a chave 'colors_adjusted'")

    # Adiciona pontos principais do lote
    if "points_utm" not in point_colors:
        raise Exception("Documento não contém a chave 'points_utm'")

    print(f"Processando {len(point_colors['points_utm'])} pontos principais...")
    for idx, point in enumerate(point_colors["points_utm"]):
        if len(point) < 3:
            print(f"⚠️ Ponto ignorado - formato inválido: {point}")
            continue

        x, y, z = point[:3]

        # Obtém a cor do array colors_adjusted usando o mesmo índice
        if idx < len(point_colors["colors_adjusted"]):
            hex_color = point_colors["colors_adjusted"][idx]
            # Converte hex para RGB
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
        else:
            print(f"⚠️ Cor não encontrada para o ponto {idx}, usando preto")
            r, g, b = (0, 0, 0)
            hex_color = "#000000"

        # Converte UTM para lat/lon para obter a zona correta
        lat, lon = utm.to_latlon(x, y, 23, "K")  # Usa zona temporária
        # Converte de volta para UTM para obter a zona correta
        x, y, zone_number, zone_letter = utm.from_latlon(lat, lon)

        points_data.append(
            {
                "x": x,
                "y": y,
                "z": z,
                "zone_number": zone_number,
                "zone_letter": zone_letter,
                "r": r,
                "g": g,
                "b": b,
                "hex_color": hex_color,
                "front": 0,
                "road": 0,
            }
        )

    # Processa pontos da frente, se existirem
    if "front_points_lat_lon" in point_colors:
        print(
            f"Processando {len(point_colors['front_points_lat_lon'])} pontos da frente..."
        )
        for point in point_colors["front_points_lat_lon"]:
            if (
                not isinstance(point, dict)
                or "lat" not in point
                or "lng" not in point
            ):
                print(f"⚠️ Ponto da frente ignorado - formato inválido: {point}")
                continue

            lat, lng = point["lat"], point["lng"]
            if not isinstance(lat, (int, float)) or not isinstance(
                lng, (int, float)
            ):
                print(f"⚠️ Ponto da frente ignorado - formato inválido: {point}")
                continue

            # Converte para UTM
            x, y, zone_number, zone_letter = utm.from_latlon(lat, lng)

            # Encontra a cor do ponto mais próximo
            hex_color = find_nearest_point_color(x, y, points_data)
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)

            points_data.append(
                {
                    "x": x,
                    "y": y,
                    "z": (
                        points_data[0]["z"] if points_data else 0
                    ),  # Usa a elevação do primeiro ponto ou 0
                    "zone_number": zone_number,
                    "zone_letter": zone_letter,
                    "r": r,
                    "g": g,
                    "b": b,
                    "hex_color": hex_color,
                    "front": 1,
                    "road": 0,
                }
            )

    if not points_data:
        raise Exception("Nenhum ponto válido encontrado no documento")

    df = pd.DataFrame(points_data)
    print(f"✓ DataFrame gerado com {len(df)} pontos no total")
    return df


def process_lot_csv(client: MongoClient, doc_id: str, bucket_name: str) -> None:
    """
    Processa um lote específico e salva o CSV no Google Cloud Storage.

    Args:
        client (MongoClient): Cliente MongoDB
        doc_id (str): ID do documento
        bucket_name (str): Nome do bucket GCS
    """
    try:
        # Obtém o documento
        db = client["gethome-01-hml"]
        collection = db["lots_detections_details_hmg"]
        doc = collection.find_one({"_id": ObjectId(doc_id)})

        if not doc:
            raise ValueError(f"Documento {doc_id} não encontrado")

        # Verifica se tem os dados necessários
        lot_details = doc.get("lot_details", {})
        points_utm = lot_details.get("points_utm", [])
        elevations = lot_details.get("elevations", [])
        point_colors = lot_details.get("point_colors", {})
        colors_adjusted = point_colors.get("colors_adjusted", [])

        if not points_utm or not elevations:
            raise ValueError("Dados de UTM ou elevações não encontrados")

        if len(points_utm) != len(elevations):
            raise ValueError("Número diferente de pontos UTM e elevações")

        # Prepara os dados para o CSV
        data = []
        for i, (utm_point, elevation) in enumerate(zip(points_utm, elevations)):
            if not all(
                x is not None for x in utm_point[:3]
            ):  # Verifica x, y, z
                continue

            # Pega a cor do ponto, se disponível
            color = (
                colors_adjusted[i] if i < len(colors_adjusted) else "#000000"
            )
            # Converte cor hex para RGB
            rgb = tuple(
                int(color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4)
            )

            data.append(
                {
                    "x": utm_point[0],  # easting
                    "y": utm_point[1],  # northing
                    "z": elevation,  # elevation from separate array
                    "zone_number": (
                        utm_point[3] if len(utm_point) > 3 else 23
                    ),  # default to zone 23
                    "zone_letter": (
                        utm_point[4] if len(utm_point) > 4 else "K"
                    ),  # default to K
                    "r": rgb[0],
                    "g": rgb[1],
                    "b": rgb[2],
                    "hex_color": color,
                    "front": 0,
                    "road": 0,
                }
            )

        # Adiciona pontos da frente, se existirem
        front_points = point_colors.get("front_points", [])
        if front_points:
            for point in front_points:
                if (
                    not isinstance(point, dict)
                    or "lat" not in point
                    or "lng" not in point
                ):
                    continue

                lat, lng = point["lat"], point["lng"]
                if not isinstance(lat, (int, float)) or not isinstance(
                    lng, (int, float)
                ):
                    continue

                # Converte para UTM
                x, y, zone_number, zone_letter = utm.from_latlon(lat, lng)

                # Encontra a cor do ponto mais próximo
                hex_color = find_nearest_point_color(x, y, data)
                rgb = tuple(
                    int(hex_color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4)
                )

                data.append(
                    {
                        "x": x,
                        "y": y,
                        "z": (
                            data[0]["z"] if data else 0
                        ),  # Usa a elevação do primeiro ponto ou 0
                        "zone_number": zone_number,
                        "zone_letter": zone_letter,
                        "r": rgb[0],
                        "g": rgb[1],
                        "b": rgb[2],
                        "hex_color": hex_color,
                        "front": 1,
                        "road": 0,
                    }
                )

        if not data:
            raise ValueError("Nenhum ponto válido para gerar CSV")

        df = pd.DataFrame(data)

        # Gera nome do arquivo
        filename = f"{doc_id}.csv"

        # Salva temporariamente
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as temp_file:
            df.to_csv(temp_file.name, index=False)
            temp_path = temp_file.name

            # Upload para GCS
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(f"csv_files/{filename}")
            blob.upload_from_filename(temp_path)

            # Gera URL pública
            csv_url = f"https://storage.cloud.google.com/{bucket_name}/csv_files/{filename}"

            # Atualiza URL no MongoDB
            collection.update_one(
                {"_id": ObjectId(doc_id)},
                {"$set": {"csv_elevation_colors": csv_url}},
            )

            print(f"✓ CSV gerado e salvo em: {csv_url}")

        # Remove arquivo temporário
        os.unlink(temp_path)

    except Exception as e:
        print(f"Erro ao processar lote {doc_id}: {str(e)}")
        raise


def process_lots_csv(
    mongodb_uri: str,
    bucket_name: str,
    year: str,
    doc_id: Optional[str] = None,
    confidence: float = 0.62,
) -> List[Dict]:
    """
    Processa lotes gerando arquivos CSV.

    Args:
        mongodb_uri (str): URI de conexão com MongoDB
        bucket_name (str): Nome do bucket no GCS
        year (str): Ano de referência
        doc_id (Optional[str]): ID específico do documento
        confidence (float): Valor mínimo de confiança

    Returns:
        List[Dict]: Lista de documentos processados
    """
    print("\n=== Iniciando processamento de lotes ===")
    print(f"Ano: {year}")
    print(f"Doc ID específico: {doc_id if doc_id else 'Todos os lotes'}")
    print(f"Filtro de confiança: >= {confidence}")

    client = None
    try:
        # Estabelece conexão com MongoDB
        client = MongoClient(mongodb_uri)
        db = client["gethome-01-hml"]
        collection = db["lots_detections_details_hmg"]

        # Define query base
        query = {
            "$and": [
                {"lot_details.point_colors.points_lat_lon": {"$exists": True}},
                {"lot_details.points_utm": {"$exists": True}},
                {"lot_details.elevations": {"$exists": True}},
                {"csv_elevation_colors": {"$exists": False}},
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

                # Processa o lote usando a função existente
                process_lot_csv(client, current_doc_id, bucket_name)

                # Obtém o documento atualizado
                updated_doc = collection.find_one({"_id": doc["_id"]})
                if updated_doc and updated_doc.get("csv_elevation_colors"):
                    processed_docs.append(updated_doc)
                    print(
                        f"✅ Documento {current_doc_id} processado com sucesso"
                    )
                else:
                    print(
                        f"⚠️ Documento {current_doc_id} não foi atualizado corretamente"
                    )
                    errors += 1

            except Exception as e:
                errors += 1
                print(f"Erro ao processar documento {current_doc_id}: {str(e)}")
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
