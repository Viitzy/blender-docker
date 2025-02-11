import os
import json
from pathlib import Path
from typing import Dict, List, Any
import cv2
import numpy as np
from shapely.geometry import Polygon


def calculate_lot_area(mask_path: str, metadata: Dict) -> float:
    """
    Calculate lot area in square meters from mask and metadata.

    Args:
        mask_path: Path to mask image
        metadata: Metadata with lat/lon and zoom

    Returns:
        Area in square meters
    """
    # Load mask
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    if mask is None:
        return 0.0

    # Get contours
    contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    if not contours:
        return 0.0

    # Get largest contour
    largest_contour = max(contours, key=cv2.contourArea)

    # Convert to polygon points
    points = largest_contour.reshape(-1, 2)

    # Convert pixel coordinates to lat/lon
    lat = metadata["latitude"]
    lon = metadata["longitude"]
    zoom = metadata["zoom"]

    # Calculate meters per pixel at this zoom level
    # Reference: https://wiki.openstreetmap.org/wiki/Zoom_levels
    meters_per_pixel = 156543.03392 * np.cos(lat * np.pi / 180) / (2**zoom)

    # Create polygon and calculate area
    polygon = Polygon(points)
    area_pixels = polygon.area

    # Convert to square meters
    area_m2 = area_pixels * (meters_per_pixel**2)

    return area_m2


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
