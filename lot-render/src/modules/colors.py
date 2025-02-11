import os
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
import cv2
import numpy as np
from PIL import Image
from pixel_to_geo import pixel_to_latlon
from lot_colors_adjustment import correct_colors
import pandas as pd
import traceback


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
    input_dir: str,
    output_dir: str,
    max_points: int = 130,
    dark_threshold: int = 70,
    bright_threshold: int = 215,
    confidence: float = 0.62,
) -> list:
    """
    Processa as cores dos lotes usando arquivos locais, adiciona coordenadas geográficas
    e corrige cores escuras e claras.

    Args:
        input_dir (str): Diretório contendo os arquivos JSON processados
        output_dir (str): Pasta para salvar visualizações
        max_points (int): Número máximo de pontos por lote
        dark_threshold (int): Limite para cores escuras
        bright_threshold (int): Limite para cores claras
        confidence (float): Valor mínimo de confiança para processar o documento

    Returns:
        list: Lista de documentos processados
    """
    print("\n=== Iniciando processamento de cores dos lotes ===")
    print(f"Parâmetros:")
    print(f"- Máximo de pontos: {max_points}")
    print(f"- Threshold escuro: {dark_threshold}")
    print(f"- Threshold claro: {bright_threshold}")
    print(f"- Filtro de confiança: >= {confidence}")

    try:
        # Cria diretório de saída se não existir
        os.makedirs(output_dir, exist_ok=True)

        # Lista todos os arquivos JSON no diretório de entrada
        json_files = [f for f in os.listdir(input_dir) if f.endswith(".json")]
        total_docs = len(json_files)
        print(f"\nTotal de documentos para processar: {total_docs}")

        processed_docs = []
        processed = 0
        errors = 0

        for json_file in json_files:
            try:
                # Carrega o documento JSON
                json_path = os.path.join(input_dir, json_file)
                with open(json_path, "r") as f:
                    doc = json.load(f)

                # Verifica a confiança
                confidence_value = doc.get("original_detection", {}).get(
                    "confidence", 0
                )
                if confidence_value < confidence:
                    print(
                        f"Confiança {confidence_value} abaixo do limiar, pulando..."
                    )
                    continue

                processed += 1
                print(
                    f"\n--- Processando documento {processed}/{total_docs} ---"
                )
                print(f"ID: {doc['id']}")
                print(
                    f"Street: {doc.get('metadata', {}).get('street_name', 'N/A')}"
                )

                # Carrega a imagem original
                image_path = doc.get("metadata", {}).get("original_image")
                if not image_path or not os.path.exists(image_path):
                    print(f"Imagem original não encontrada: {image_path}")
                    errors += 1
                    continue

                image = cv2.imread(image_path)
                if image is None:
                    print("Erro ao carregar imagem, pulando documento")
                    errors += 1
                    continue

                height, width = image.shape[:2]
                print(f"Dimensões da imagem: {width}x{height}")

                # Usa a área já calculada ou calcula se necessário
                area = doc.get("area_m2")
                if area is None:
                    print("Área não encontrada no documento")
                    errors += 1
                    continue

                print(f"Área do lote: {area:.2f} m²")

                # Cria máscara do polígono
                print("Gerando máscara do polígono...")
                mask = np.zeros((height, width), dtype=np.uint8)
                annotation = doc.get("adjusted_detection", {}).get(
                    "annotation"
                ) or doc.get("original_detection", {}).get("annotation")

                if not annotation:
                    print("Anotação não encontrada")
                    errors += 1
                    continue

                points = annotation.split()[1:]
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

                for x, y in points_inside:
                    # Processa cores
                    bgr_color = image[y, x]
                    rgb_color = (
                        int(bgr_color[2]),
                        int(bgr_color[1]),
                        int(bgr_color[0]),
                    )
                    hex_color = rgb_to_hex(rgb_color)
                    colors.append(hex_color)
                    colors_rgb.append(rgb_color)

                    # Normaliza pontos
                    normalized_points.append(
                        [
                            round(float(x) / width, 3),
                            round(float(y) / height, 3),
                        ]
                    )

                    # Calcula coordenadas geográficas
                    lat, lon = pixel_to_latlon(
                        pixel_x=x,
                        pixel_y=y,
                        center_lat=center_lat,
                        center_lon=center_lon,
                        zoom=zoom,
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

                # Salva visualizações
                print("Salvando visualizações...")
                save_visualizations(
                    image,
                    polygon_points,
                    points_inside,
                    colors_rgb,
                    df_corrected,
                    doc["id"],
                    output_dir,
                )

                # Prepara dados de cores para salvar
                point_colors = {
                    "points": normalized_points,
                    "colors": colors,
                    "colors_adjusted": colors_adjusted,
                    "points_lat_lon": geo_points,
                }

                # Atualiza o documento com as cores processadas
                doc["point_colors"] = point_colors

                # Salva o documento atualizado
                output_json_path = os.path.join(
                    output_dir, f"colors_{doc['id']}.json"
                )
                with open(output_json_path, "w") as f:
                    json.dump(doc, f, indent=2)

                processed_docs.append(doc)
                print("Documento processado e salvo com sucesso!")

            except Exception as e:
                errors += 1
                print(f"\nERRO ao processar arquivo {json_file}: {str(e)}")
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
