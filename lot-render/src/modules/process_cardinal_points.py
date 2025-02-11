from typing import Dict, List, Optional, Tuple
from pymongo import MongoClient
from bson import ObjectId
import numpy as np
from geopy.distance import geodesic
import os
import json
import traceback


def calculate_cardinal_points(
    center_lat: float, center_lon: float, distance_meters: float
) -> Dict[str, List[float]]:
    """
    Calcula pontos cardeais a uma distância específica do centro.

    Args:
        center_lat: Latitude do centro
        center_lon: Longitude do centro
        distance_meters: Distância em metros

    Returns:
        Dicionário com pontos cardeais
    """
    # Converte distância para graus (aproximadamente)
    distance_deg = distance_meters / 111320  # 1 grau ≈ 111.32 km no equador

    cardinal_points = {
        "center": [center_lat, center_lon],
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

    # Verifica distâncias
    for direction, point in cardinal_points.items():
        if direction != "center":
            actual_distance = geodesic(
                (center_lat, center_lon), (point[0], point[1])
            ).meters
            print(f"Distância {direction}: {actual_distance:.2f}m")

    return cardinal_points


def process_cardinal_points(
    input_dir: str,
    output_dir: str,
    distance_meters: float,
    confidence: float = 0.62,
) -> List[Dict]:
    """
    Processa e adiciona pontos cardeais para lotes usando arquivos locais.

    Args:
        input_dir (str): Diretório contendo os arquivos JSON processados
        output_dir (str): Diretório para salvar os resultados
        distance_meters (float): Distância em metros para os pontos cardeais
        confidence (float): Valor mínimo de confiança para processar

    Returns:
        List[Dict]: Lista de documentos processados
    """
    print("\n=== Iniciando processamento de pontos cardeais ===")
    print(f"Distância: {distance_meters}m")
    print(f"Filtro de confiança: >= {confidence}")

    try:
        # Cria diretório de saída se não existir
        os.makedirs(output_dir, exist_ok=True)

        # Lista todos os arquivos JSON no diretório de entrada
        json_files = [f for f in os.listdir(input_dir) if f.endswith(".json")]
        print(f"\nTotal de arquivos para processar: {len(json_files)}")

        processed_docs = []
        errors = 0

        for i, json_file in enumerate(json_files, 1):
            try:
                # Verifica se já existe arquivo processado
                output_file = os.path.join(output_dir, f"cardinal_{json_file}")
                if os.path.exists(output_file):
                    print(
                        f"\nArquivo {output_file} já processado, carregando dados..."
                    )
                    with open(output_file, "r") as f:
                        doc = json.load(f)
                        processed_docs.append(doc)
                    continue

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

                print(f"\nProcessando documento {i}/{len(json_files)}")
                print(f"ID: {doc['id']}")
                print(
                    f"Rua: {doc.get('metadata', {}).get('street_name', 'N/A')}"
                )

                # Verifica se já tem point_colors
                point_colors = doc.get("point_colors", {})

                # Calcula centro do polígono se houver pontos
                if "points_lat_lon" in point_colors:
                    points = np.array(point_colors["points_lat_lon"])
                    center_lat = np.mean(points[:, 0])
                    center_lon = np.mean(points[:, 1])
                    print(
                        f"Centro calculado: ({center_lat:.6f}, {center_lon:.6f})"
                    )
                else:
                    print("AVISO: Usando coordenadas do documento como centro")
                    center_lat = doc.get("metadata", {}).get("latitude")
                    center_lon = doc.get("metadata", {}).get("longitude")

                if not (center_lat and center_lon):
                    print("ERRO: Não foi possível determinar o centro")
                    errors += 1
                    continue

                # Calcula pontos cardeais
                cardinal_points = calculate_cardinal_points(
                    center_lat, center_lon, distance_meters
                )

                # Adiciona pontos cardeais ao point_colors
                point_colors["cardinal_points"] = cardinal_points
                doc["point_colors"] = point_colors

                # Salva o documento processado
                with open(output_file, "w") as f:
                    json.dump(doc, f, indent=2)

                processed_docs.append(doc)
                print("Documento processado e salvo com sucesso!")
                print("Pontos cardeais adicionados:")
                for direction, point in cardinal_points.items():
                    print(f"  {direction}: ({point[0]:.6f}, {point[1]:.6f})")

            except Exception as e:
                errors += 1
                print(f"Erro ao processar arquivo {json_file}: {str(e)}")
                traceback.print_exc()
                continue

        print("\n=== Resumo do processamento ===")
        print(f"Total de documentos: {len(json_files)}")
        print(f"Processados com sucesso: {len(processed_docs)}")
        print(f"Erros: {errors}")
        print("============================\n")

        return processed_docs

    except Exception as e:
        print(f"Erro durante o processamento: {str(e)}")
        raise
