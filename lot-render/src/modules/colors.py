import os
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
import cv2
import numpy as np
from PIL import Image
from .pixel_to_geo import pixel_to_latlon, extract_zoom
from .lot_colors_adjustment import correct_colors
import pandas as pd
import traceback
import random
from pymongo import MongoClient
from bson.objectid import ObjectId
from google.cloud import storage
import math


def compute_number_of_points(area_m2: float) -> int:
    """
    Compute number of points based on lot area.

    Args:
        area_m2: Lot area in square meters

    Returns:
        Number of points to sample
    """
    # Base number of points
    base_points = 50

    # Additional points based on area
    additional_points = int(area_m2 / 100)  # 1 point per 100m²

    # Total points capped at max_points
    total_points = min(base_points + additional_points, 130)

    return total_points


def get_points_inside_mask(
    mask: np.ndarray, area_m2: float, max_points: int = 130
) -> List[Tuple[int, int]]:
    """
    Get random points inside mask.

    Args:
        mask: Binary mask
        area_m2: Lot area in square meters
        max_points: Maximum number of points

    Returns:
        List of (x, y) points
    """
    # Get mask contours
    contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    if not contours:
        return []

    # Get largest contour
    contour = max(contours, key=cv2.contourArea)

    # Create point mask
    point_mask = np.zeros_like(mask)
    cv2.drawContours(point_mask, [contour], -1, 255, -1)

    # Get points inside mask
    y_coords, x_coords = np.where(point_mask > 0)
    if len(x_coords) == 0:
        return []

    # Compute number of points
    n_points = min(compute_number_of_points(area_m2), max_points)

    # Randomly sample points
    indices = np.random.choice(len(x_coords), size=n_points, replace=False)
    points = [(int(x_coords[i]), int(y_coords[i])) for i in indices]

    return points


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """Convert RGB to hex color."""
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def calculate_geo_area(points: list) -> float:
    """
    Calcula a área de um polígono em metros quadrados usando coordenadas geográficas.
    Usa a fórmula de Haversine para considerar a curvatura da Terra.
    """
    R = 6371000

    if points[0] != points[-1]:
        points = points + [points[0]]

    area = 0.0
    for i in range(len(points) - 1):
        lat1, lon1 = points[i]
        lat2, lon2 = points[i + 1]

        lat1, lon1 = math.radians(lat1), math.radians(lon1)
        lat2, lon2 = math.radians(lat2), math.radians(lon2)

        area += (lon2 - lon1) * (2 + math.sin(lat1) + math.sin(lat2))

    area = abs(area * R * R / 2.0)
    return area


def calculate_lot_area(doc: dict) -> float:
    """
    Calcula a área do lote em metros quadrados usando as funções do pixel_to_geo.py
    """
    center_lat = doc["latitude"]
    center_lon = doc["longitude"]
    zoom = doc.get("zoom", 20)  # Default para 20 se não especificado
    width = height = 1280  # Dimensões fixas da imagem

    # Tenta usar a detecção ajustada primeiro, se não existir usa a original
    if "adjusted_detection" in doc:
        annotation = doc["adjusted_detection"]["annotation"]
    else:
        annotation = doc["yolov8_annotation"]

    points_str = annotation.split()[1:]
    geo_points = []

    for i in range(0, len(points_str), 2):
        pixel_x = float(points_str[i]) * width
        pixel_y = float(points_str[i + 1]) * height
        lat, lon = pixel_to_latlon(
            pixel_x=pixel_x,
            pixel_y=pixel_y,
            center_lat=center_lat,
            center_lon=center_lon,
            zoom=zoom,
            scale=2,
            image_width=width,
            image_height=height,
        )
        geo_points.append((lat, lon))

    return calculate_geo_area(geo_points)


def download_image_from_gcs(image_url: str) -> np.ndarray:
    """
    Baixa imagem do Google Cloud Storage.
    """
    try:
        # Remove o prefixo 'https://storage.cloud.google.com/' se presente
        if image_url.startswith("https://storage.cloud.google.com/"):
            bucket_path = image_url.replace(
                "https://storage.cloud.google.com/", ""
            )
        else:
            bucket_path = image_url

        # Separa o nome do bucket e o caminho do blob
        parts = bucket_path.split("/", 1)
        bucket_name = parts[0]
        blob_path = parts[1]

        # Inicializa cliente GCS
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_path)

        # Baixa os bytes da imagem
        image_bytes = blob.download_as_bytes()

        # Converte para numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        return image
    except Exception as e:
        print(f"Erro ao baixar imagem: {str(e)}")
        return None


def process_lot_colors(
    mongodb_uri: str,
    doc_id: str,
    max_points: int = 130,
    dark_threshold: int = 70,
    bright_threshold: int = 215,
    confidence: float = 0.62,
) -> list:
    """
    Processa as cores do lote específico, adiciona coordenadas geográficas e corrige cores escuras e claras.

    Args:
        mongodb_uri (str): URI de conexão com MongoDB
        doc_id (str): ID do documento para processar
        max_points (int): Número máximo de pontos a serem gerados
        dark_threshold (int): Limite para cores escuras
        bright_threshold (int): Limite para cores claras
        confidence (float): Valor mínimo de confiança
    """
    print("\n=== Iniciando processamento de cores do lote ===")
    print(f"ID do documento: {doc_id}")
    print(f"Parâmetros:")
    print(f"- Máximo de pontos: {max_points}")
    print(f"- Threshold escuro: {dark_threshold}")
    print(f"- Threshold claro: {bright_threshold}")
    print(f"- Filtro de confiança: >= {confidence}")

    client = None
    try:
        # Estabelece conexão com MongoDB
        client = MongoClient(mongodb_uri)
        db = client["gethome-01-hml"]
        collection = db["lots_detections_details_hmg"]

        # Busca o documento específico
        doc = collection.find_one(
            {
                "_id": ObjectId(doc_id),
                "confidence": {"$gte": confidence},
                "satellite_image_url": {"$exists": True},
            }
        )

        if not doc:
            print(
                f"Documento {doc_id} não encontrado ou não atende aos critérios"
            )
            return []

        processed_docs = []
        try:
            print("\n--- Processando documento ---")

            # Calcula ou obtém a área do lote
            if "area_m2" not in doc:
                area = calculate_lot_area(doc)
                print(f"Área calculada: {area:.2f} m²")
                collection.update_one(
                    {"_id": doc["_id"]}, {"$set": {"area_m2": area}}
                )
                doc["area_m2"] = area
            else:
                area = doc["area_m2"]
                print(f"Área existente: {area:.2f} m²")

            # Baixa a imagem do bucket images_from_have_allotment
            print("Baixando imagem...")
            image = download_image_from_gcs(doc["satellite_image_url"])
            if image is None:
                print("Erro ao baixar imagem")
                return []

            height, width = image.shape[:2]
            print(f"Dimensões da imagem: {width}x{height}")

            # Cria máscara do polígono
            print("Gerando máscara do polígono...")
            mask = np.zeros((height, width), dtype=np.uint8)
            points = doc["adjusted_yolov8_annotation"].split()[1:]
            polygon_points = []

            for i in range(0, len(points), 2):
                x = float(points[i]) * width
                y = float(points[i + 1]) * height
                polygon_points.append([int(x), int(y)])

            cv2.fillPoly(mask, [np.array(polygon_points)], 1)

            # Gera pontos internos
            print("Gerando pontos internos...")
            points_inside = get_points_inside_mask(mask, area)
            print(f"Pontos gerados: {len(points_inside)}")

            # Limita o número de pontos se necessário
            if len(points_inside) > max_points:
                print(
                    f"Reduzindo número de pontos de {len(points_inside)} para {max_points}"
                )
                indices = np.linspace(
                    0, len(points_inside) - 1, max_points, dtype=int
                )
                points_inside = [points_inside[i] for i in indices]

            # Processa cores e coordenadas
            print("Processando cores e coordenadas...")
            colors = []
            colors_rgb = []
            normalized_points = []
            geo_points = []

            for x, y in points_inside:
                bgr_color = image[y, x]
                rgb_color = (
                    int(bgr_color[2]),
                    int(bgr_color[1]),
                    int(bgr_color[0]),
                )
                hex_color = rgb_to_hex(rgb_color)
                colors.append(hex_color)
                colors_rgb.append(rgb_color)

                normalized_points.append(
                    [round(float(x) / width, 3), round(float(y) / height, 3)]
                )

                lat, lon = pixel_to_latlon(
                    pixel_x=x,
                    pixel_y=y,
                    center_lat=doc["latitude"],
                    center_lon=doc["longitude"],
                    zoom=doc.get("zoom") or extract_zoom(doc["image_url"]),
                    scale=2,
                    image_width=width,
                    image_height=height,
                )
                geo_points.append([round(lat, 6), round(lon, 6)])

            # Correção de cores
            print("Aplicando correção de cores...")
            df_colors = pd.DataFrame(colors_rgb, columns=["r", "g", "b"])
            df_colors["x"] = [p[0] for p in normalized_points]
            df_colors["y"] = [p[1] for p in normalized_points]
            df_colors["z"] = 0

            df_corrected = correct_colors(
                df_colors,
                dark_threshold=dark_threshold,
                bright_threshold=bright_threshold,
            )

            colors_adjusted = []
            for _, row in df_corrected.iterrows():
                rgb = (int(row["r"]), int(row["g"]), int(row["b"]))
                hex_color = rgb_to_hex(rgb)
                colors_adjusted.append(hex_color)

            # Atualiza MongoDB
            print("Atualizando documento no MongoDB...")
            point_colors = {
                "points": normalized_points,
                "colors": colors,
                "colors_adjusted": colors_adjusted,
                "points_lat_lon": geo_points,
            }

            result = collection.update_one(
                {"_id": doc["_id"]},
                {"$set": {"point_colors": point_colors}},
            )

            if result.modified_count > 0:
                doc["point_colors"] = point_colors
                processed_docs.append(doc)
                print("Documento atualizado com sucesso!")

        except Exception as e:
            print(f"\nERRO ao processar documento {doc_id}: {str(e)}")
            traceback.print_exc()

        print("\n=== Resumo do processamento ===")
        print(f"Documento processado: {doc_id}")
        print(f"Status: {'Sucesso' if processed_docs else 'Falha'}")
        print("==============================\n")

        return processed_docs

    except Exception as e:
        print(f"Erro durante o processamento: {str(e)}")
        raise

    finally:
        if client:
            try:
                client.close()
                print("✅ Conexão com MongoDB fechada com sucesso")
            except Exception as e:
                print(f"⚠️ Erro ao fechar conexão com MongoDB: {e}")
