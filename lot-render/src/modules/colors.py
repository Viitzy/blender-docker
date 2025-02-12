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


# Função para encontrar a cor média de pontos próximos não escuros
def get_replacement_color(point, data, radius=2.0):
    x, y, z = point["x"], point["y"], point["z"]
    # Filtrar pontos próximos
    nearby_points = data[
        (~data["is_dark"])  # Apenas pontos não escuros
        & (np.abs(data["x"] - x) <= radius)
        & (np.abs(data["y"] - y) <= radius)
        & (np.abs(data["z"] - z) <= radius)
    ]
    if nearby_points.empty:
        return None  # Nenhum ponto próximo encontrado
    # Calcular a média de R, G, B dos pontos próximos
    avg_r = nearby_points["r"].mean()
    avg_g = nearby_points["g"].mean()
    avg_b = nearby_points["b"].mean()
    return int(avg_r), int(avg_g), int(avg_b)


# Função para corrigir cores escuras
def correct_dark_colors(data, dark_threshold=50, radius=2.0):
    data["is_dark"] = data[["r", "g", "b"]].mean(axis=1) < dark_threshold
    for index, row in data[data["is_dark"]].iterrows():
        replacement_color = get_replacement_color(row, data, radius)
        if replacement_color:
            data.loc[index, ["r", "g", "b"]] = replacement_color
    # Atualizar a coluna 'hex_color'
    data["hex_color"] = data.apply(
        lambda row: f"#{int(row['r']):02x}{int(row['g']):02x}{int(row['b']):02x}",
        axis=1,
    )
    return data


def get_replacement_color_for_bright(point, data, radius=2.0):
    """
    Encontra a cor média de pontos próximos não brancos.

    Parameters:
        point: Series - Ponto atual com coordenadas e cores
        data: DataFrame - DataFrame com todos os pontos
        radius: float - Raio de busca para pontos próximos
    """
    x, y, z = point["x"], point["y"], point["z"]
    # Filtrar pontos próximos
    nearby_points = data[
        (~data["is_bright"])  # Apenas pontos não brancos
        & (np.abs(data["x"] - x) <= radius)
        & (np.abs(data["y"] - y) <= radius)
        & (np.abs(data["z"] - z) <= radius)
    ]
    if nearby_points.empty:
        return None
    # Calcular a média de R, G, B dos pontos próximos
    avg_r = nearby_points["r"].mean()
    avg_g = nearby_points["g"].mean()
    avg_b = nearby_points["b"].mean()
    return int(avg_r), int(avg_g), int(avg_b)


def correct_bright_colors(data, bright_threshold=240, radius=2.0):
    """
    Corrige cores muito claras (brancas) substituindo pela média das cores próximas.

    Parameters:
        data: DataFrame - DataFrame com colunas r, g, b, x, y, z
        bright_threshold: int - Valor mínimo para considerar uma cor como branca
        radius: float - Raio de busca para pontos próximos
    """
    # Identifica cores muito claras (média dos canais acima do threshold)
    data["is_bright"] = data[["r", "g", "b"]].mean(axis=1) > bright_threshold

    # Corrige cores muito claras
    for index, row in data[data["is_bright"]].iterrows():
        replacement_color = get_replacement_color_for_bright(row, data, radius)
        if replacement_color:
            data.loc[index, ["r", "g", "b"]] = replacement_color

    return data


def correct_colors(data, dark_threshold=50, bright_threshold=240, radius=2.0):
    """
    Aplica correção tanto para cores escuras quanto para cores claras.

    Parameters:
        data: DataFrame - DataFrame com colunas r, g, b, x, y, z
        dark_threshold: int - Valor máximo para considerar uma cor como escura
        bright_threshold: int - Valor mínimo para considerar uma cor como branca
        radius: float - Raio de busca para pontos próximos
    """
    # Primeiro corrige as cores escuras
    data = correct_dark_colors(data, dark_threshold, radius)
    # Depois corrige as cores claras
    data = correct_bright_colors(data, bright_threshold, radius)
    return data


def process_lot_colors(
    mongodb_uri: str,
    doc_id: str,
    max_points: int = 130,
    dark_threshold: int = 70,
    bright_threshold: int = 215,
    confidence: float = 0.62,
) -> list:
    """Process lot colors."""
    print("\n=== Iniciando processamento de cores do lote ===")
    print(f"ID do documento: {doc_id}")
    print("Parâmetros:")
    print(f"- Máximo de pontos: {max_points}")
    print(f"- Threshold escuro: {dark_threshold}")
    print(f"- Threshold claro: {bright_threshold}")
    print(f"- Filtro de confiança: >= {confidence}")

    client = None
    try:
        # Connect to MongoDB
        client = MongoClient(mongodb_uri)
        db = client["gethome-01-hml"]
        collection = db["lots_detections_details_hmg"]

        # Query para a nova estrutura
        query = {
            "_id": ObjectId(doc_id),
            "detection_result": {"$exists": True},
            "image_info.url": {"$exists": True},
        }

        doc = collection.find_one(query)
        if not doc:
            print(
                f"Documento {doc_id} não encontrado ou não atende aos critérios"
            )
            return []

        # Get image URL from new structure
        image_url = doc["image_info"]["url"]

        # Get area from detection result
        area = calculate_lot_area(doc)

        # Download and process image
        image = download_image_from_gcs(image_url)
        if image is None:
            print("Erro ao baixar imagem")
            return []

        height, width = image.shape[:2]
        print(f"Dimensões da imagem: {width}x{height}")

        # Create polygon mask using adjusted detection if available
        print("Gerando máscara do polígono...")
        mask = np.zeros((height, width), dtype=np.uint8)

        if "adjusted_mask" in doc["detection_result"]:
            print("Usando detecção ajustada...")
            points_array = doc["detection_result"]["adjusted_mask"]["points"]
        else:
            print("Usando detecção original...")
            points_array = doc["detection_result"]["mask_points"]

        # Convert normalized points to pixel coordinates
        polygon_points = []
        for x, y in points_array:
            x_pixel = int(x * width)
            y_pixel = int(y * height)
            polygon_points.append([x_pixel, y_pixel])

        cv2.fillPoly(mask, [np.array(polygon_points)], 1)

        # Generate internal points
        points_inside = get_points_inside_mask(mask, area, max_points)

        # Process colors for points
        colors = []
        colors_adjusted = []
        points_lat_lon = []

        for point in points_inside:
            # Get color from image
            color = image[point[1], point[0]]
            colors.append(color.tolist())

            # Adjust color if needed
            adjusted_color = correct_color(
                color, dark_threshold, bright_threshold
            )
            colors_adjusted.append(adjusted_color)

            # Convert point to lat/lon
            lat, lon = pixel_to_latlon(
                pixel_x=point[0],
                pixel_y=point[1],
                center_lat=doc["coordinates"]["lat"],
                center_lon=doc["coordinates"]["lon"],
                zoom=doc["image_info"]["zoom"],
                scale=doc["image_info"]["scale"],
                image_width=width,
                image_height=height,
            )
            points_lat_lon.append([lat, lon])

        # Update MongoDB
        update_data = {
            "lot_details": {
                "area_m2": area,
                "point_colors": {
                    "points": points_inside,
                    "colors": colors,
                    "colors_adjusted": colors_adjusted,
                    "points_lat_lon": points_lat_lon,
                },
            }
        }

        result = collection.update_one(
            {"_id": ObjectId(doc_id)}, {"$set": update_data}
        )

        if result.modified_count > 0:
            print(f"Documento {doc_id} atualizado com sucesso")
            return [
                {
                    "id": str(doc["_id"]),
                    "point_colors": update_data["lot_details"]["point_colors"],
                }
            ]

        return []

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
