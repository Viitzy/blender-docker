import os
import json
from pathlib import Path
from typing import Dict, List, Any
import cv2
import numpy as np
from shapely.geometry import Polygon
from .pixel_to_geo import pixel_to_latlon
import math


def calculate_geo_area(points: list) -> float:
    """
    Calcula a área de um polígono definido por coordenadas geográficas
    usando a fórmula de Haversine.

    Parameters:
        points: list - Lista de tuplas (lat, lon) definindo o polígono

    Returns:
        float - Área em metros quadrados
    """
    if len(points) < 3:
        return 0.0

    # Raio da Terra em metros
    R = 6371000

    # Fecha o polígono se necessário
    if points[0] != points[-1]:
        points = points + [points[0]]

    area = 0.0
    for i in range(len(points) - 1):
        lat1, lon1 = points[i]
        lat2, lon2 = points[i + 1]

        # Converte para radianos
        lat1, lon1 = math.radians(lat1), math.radians(lon1)
        lat2, lon2 = math.radians(lat2), math.radians(lon2)

        # Fórmula da área de Haversine
        area += (lon2 - lon1) * (2 + math.sin(lat1) + math.sin(lat2))

    area = abs(area * R * R / 2.0)
    return area


def calculate_lot_area(doc: dict) -> float:
    """
    Calcula a área do lote em metros quadrados usando as funções do pixel_to_geo.py
    """
    # Get new structure coordinates
    center_lat = doc["coordinates"]["lat"]
    center_lon = doc["coordinates"]["lon"]
    zoom = doc["image_info"]["zoom"]
    width = height = 1280  # Fixed dimensions

    # Get annotation from detection result
    if "detection_result" in doc and "adjusted_mask" in doc["detection_result"]:
        points_array = doc["detection_result"]["adjusted_mask"]["points"]
    else:
        points_array = doc["detection_result"]["mask_points"]

    geo_points = []
    for x, y in points_array:
        pixel_x = x * width
        pixel_y = y * height
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


def process_lot_areas(
    input_dir: str, output_dir: str, confidence_threshold: float = 0.62
) -> Dict:
    """
    Processa e calcula as áreas dos lotes a partir dos arquivos JSON salvos.

    Args:
        input_dir: Diretório contendo os arquivos JSON das detecções
        output_dir: Diretório para salvar os resultados processados
        confidence_threshold: Valor mínimo de confiança para processar

    Returns:
        Dict: Estatísticas do processamento
    """
    print(f"\n=== Processando áreas dos lotes ===")
    print(f"Diretório de entrada: {input_dir}")
    print(f"Filtro de confiança: >= {confidence_threshold}")

    try:
        # Cria diretório de saída se não existir
        os.makedirs(output_dir, exist_ok=True)

        # Lista todos os arquivos JSON no diretório de entrada
        json_files = [f for f in os.listdir(input_dir) if f.endswith(".json")]
        total_files = len(json_files)

        print(f"Total de arquivos para processar: {total_files}")

        processed = 0
        success = 0
        errors = 0
        areas = []

        for json_file in json_files:
            try:
                json_path = os.path.join(input_dir, json_file)

                # Carrega o arquivo JSON
                with open(json_path, "r") as f:
                    doc = json.load(f)

                # Verifica a confiança
                confidence = doc.get("original_detection", {}).get(
                    "confidence", 0
                )
                if confidence < confidence_threshold:
                    print(
                        f"\nArquivo {json_file} abaixo do limiar de confiança, pulando..."
                    )
                    continue

                processed += 1
                print(f"\nProcessando arquivo {processed}/{total_files}")
                print(f"ID: {doc.get('id', 'N/A')}")

                try:
                    # Calcula a área
                    area = calculate_lot_area(doc)
                    print(f"Área calculada: {area:.2f} m²")

                    # Adiciona a área ao documento
                    doc["area_m2"] = area
                    areas.append(area)

                    # Salva o documento atualizado
                    output_path = os.path.join(output_dir, json_file)
                    with open(output_path, "w") as f:
                        json.dump(doc, f, indent=2)

                    success += 1
                    print(f"✓ Arquivo processado e salvo em: {output_path}")

                except ValueError as ve:
                    print(f"✗ Erro nos dados do documento: {str(ve)}")
                    errors += 1
                    continue

            except Exception as e:
                errors += 1
                print(f"✗ Erro ao processar arquivo {json_file}: {str(e)}")
                continue

            # Mostra progresso a cada 10 documentos
            if processed % 10 == 0:
                print(f"\n--- Progresso: {processed}/{total_files} ---")
                print(f"Sucessos: {success}")
                print(f"Erros: {errors}")

        # Calcula estatísticas
        stats = {
            "total_processed": processed,
            "success": success,
            "errors": errors,
            "areas_stats": {},
        }

        if areas:
            stats["areas_stats"] = {
                "min_area": min(areas),
                "max_area": max(areas),
                "avg_area": sum(areas) / len(areas),
            }

        print("\n=== Resumo do processamento ===")
        print(f"Total processado: {processed}")
        print(f"Sucessos: {success}")
        print(f"Erros: {errors}")

        if areas:
            print("\nEstatísticas das áreas:")
            print(f"Mínima: {stats['areas_stats']['min_area']:.2f} m²")
            print(f"Máxima: {stats['areas_stats']['max_area']:.2f} m²")
            print(f"Média: {stats['areas_stats']['avg_area']:.2f} m²")

        return stats

    except Exception as e:
        print(f"Erro durante o processamento: {str(e)}")
        return {"error": str(e)}
