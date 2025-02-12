import os
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
import cv2
import numpy as np
from PIL import Image
from .pixel_to_geo import pixel_to_latlon
from .lot_colors_adjustment import correct_colors
import pandas as pd
import traceback
import random
from pymongo import MongoClient
from bson.objectid import ObjectId


def save_visualizations(
    image,
    polygon_points,
    points_inside,
    colors_rgb,
    df_corrected,
    doc_id,
    output_folder,
):
    """Helper function para salvar visualizações"""
    # Visualização original
    vis_image = image.copy()
    cv2.polylines(vis_image, [np.array(polygon_points)], True, (0, 255, 0), 2)
    for i, (x, y) in enumerate(points_inside):
        r, g, b = colors_rgb[i]
        cv2.circle(vis_image, (x, y), 3, (b, g, r), -1)

    # Visualização com cores corrigidas
    vis_image_corrected = image.copy()
    cv2.polylines(
        vis_image_corrected, [np.array(polygon_points)], True, (0, 255, 0), 2
    )
    for i, (x, y) in enumerate(points_inside):
        r = int(df_corrected.iloc[i]["r"])
        g = int(df_corrected.iloc[i]["g"])
        b = int(df_corrected.iloc[i]["b"])
        cv2.circle(vis_image_corrected, (x, y), 3, (b, g, r), -1)

    os.makedirs(output_folder, exist_ok=True)
    cv2.imwrite(
        os.path.join(output_folder, f"{doc_id}_points_original.jpg"), vis_image
    )
    cv2.imwrite(
        os.path.join(output_folder, f"{doc_id}_points_corrected.jpg"),
        vis_image_corrected,
    )


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


def process_lot_colors(
    mongodb_uri: str,
    max_points: int = 130,
    dark_threshold: int = 70,
    bright_threshold: int = 215,
    confidence: float = 0.62,
    doc_id: str = None,
) -> list:
    print(f"\n=== Iniciando processamento de cores dos lotes ===")
    print(f"Parâmetros:")
    print(f"- Máximo de pontos: {max_points}")
    print(f"- Threshold escuro: {dark_threshold}")
    print(f"- Threshold claro: {bright_threshold}")
    print(f"- Filtro de confiança: >= {confidence}")

    if doc_id:
        print(f"Processando documento específico: {doc_id}")

    client = None
    try:
        # Conecta ao MongoDB
        client = MongoClient(mongodb_uri)
        db = client.gethome
        collection = db.lots_coords

        # Monta a query base
        query = {
            "satellite_image_url": {"$exists": True},
            "confidence": {"$gte": confidence},
            "point_colors": {
                "$exists": False
            },  # Só processa se ainda não tiver cores
        }

        # Se foi especificado um ID, adiciona à query
        if doc_id:
            query["_id"] = ObjectId(doc_id)
            # Para o caso específico de reprocessamento, removemos a checagem de point_colors
            del query["point_colors"]

        total_docs = collection.count_documents(query)
        print(f"\nTotal de documentos para processar: {total_docs}")

        processed_docs = []
        processed = 0
        errors = 0

        for doc in collection.find(query):
            try:
                processed += 1
                print(
                    f"\n--- Processando documento {processed}/{total_docs} ---"
                )
                print(f"ID: {doc['_id']}")
                print(f"Street: {doc.get('street_name', 'N/A')}")

                # Verifica se tem área
                area = doc.get("area_m2")
                if area is None:
                    print("Área não encontrada no documento")
                    errors += 1
                    continue

                print(f"Área do lote: {area:.2f} m²")

                # Obtém os pontos lat/lon
                points_lat_lon = doc.get("points_lat_lon")
                if not points_lat_lon:
                    print("Pontos lat/lon não encontrados")
                    errors += 1
                    continue

                # Calcula o número de pontos baseado na área
                n_points = min(compute_number_of_points(area), max_points)
                print(f"Número de pontos a processar: {n_points}")

                # Seleciona pontos aleatoriamente se necessário
                if len(points_lat_lon) > n_points:
                    indices = np.random.choice(
                        len(points_lat_lon), size=n_points, replace=False
                    )
                    selected_points = [points_lat_lon[i] for i in indices]
                else:
                    selected_points = points_lat_lon

                # Processa cores e coordenadas
                print("Processando cores e coordenadas...")
                colors = []
                colors_rgb = []
                normalized_points = []
                geo_points = []

                metadata = doc.get("metadata", {})
                center_lat = metadata.get("latitude")
                center_lon = metadata.get("longitude")
                zoom = metadata.get("zoom", 20)

                for lat, lon in selected_points:
                    # Converte para coordenadas normalizadas
                    x, y = pixel_to_latlon(
                        lat=lat,
                        lon=lon,
                        center_lat=center_lat,
                        center_lon=center_lon,
                        zoom=zoom,
                        scale=2,
                        image_width=1280,
                        image_height=1280,
                    )

                    # Gera uma cor da terra
                    r, g, b = random_earthy_color()
                    hex_color = rgb_to_hex((r, g, b))

                    colors.append(hex_color)
                    colors_rgb.append((r, g, b))
                    normalized_points.append([round(x, 3), round(y, 3)])
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

                # Salva visualização se necessário
                if output_folder:
                    print("Salvando visualizações...")
                    save_visualizations(
                        image=None,  # Não temos mais a imagem
                        polygon_points=None,  # Não temos mais os pontos do polígono
                        points_inside=None,  # Não temos mais os pontos internos
                        colors_rgb=colors_rgb,
                        df_corrected=df_corrected,
                        doc_id=str(doc["_id"]),
                        output_folder=output_folder,
                    )

                # Prepara dados de cores para atualizar
                point_colors = {
                    "points": normalized_points,
                    "colors": colors,
                    "colors_adjusted": colors_adjusted,
                    "points_lat_lon": geo_points,
                }

                # Atualiza MongoDB
                print("Atualizando documento no MongoDB...")
                result = collection.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"point_colors": point_colors}},
                )

                if result.modified_count > 0:
                    doc["point_colors"] = point_colors
                    processed_docs.append(doc)
                    print("Documento atualizado com sucesso!")
                else:
                    print("Nenhuma atualização necessária")

            except Exception as e:
                errors += 1
                print(
                    f"\nERRO ao processar documento {doc.get('_id')}: {str(e)}"
                )
                traceback.print_exc()
                continue

        print("\n=== Resumo do processamento ===")
        print(f"Total de documentos: {total_docs}")
        print(f"Processados com sucesso: {len(processed_docs)}")
        print(f"Erros: {errors}")
        print("==============================\n")

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
