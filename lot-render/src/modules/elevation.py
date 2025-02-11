import os
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Tuple
import requests
import time
import numpy as np
import traceback


def init_elevation_cache(db_path: str) -> None:
    """Initialize elevation cache database."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS elevations
                 (lat REAL, lon REAL, elevation REAL,
                  PRIMARY KEY (lat, lon))"""
    )
    conn.commit()
    conn.close()


def get_elevations_batch(
    locations: List[Tuple[float, float]], api_key: str
) -> List[float]:
    """
    Obtém elevações em lote da API do Google.

    Parameters:
        locations: List[Tuple[float, float]] - Lista de coordenadas (lat, lon)
        api_key: str - Chave da API do Google

    Returns:
        List[float] - Lista de elevações
    """
    max_locations_per_request = 100
    elevations = []

    for i in range(0, len(locations), max_locations_per_request):
        batch = locations[i : i + max_locations_per_request]
        coordenadas = "|".join([f"{lat},{lon}" for lat, lon in batch])

        base_url = "https://maps.googleapis.com/maps/api/elevation/json"
        url = f"{base_url}?locations={coordenadas}&key={api_key}"

        try:
            response = requests.get(url)
            print(
                f"Batch {i//max_locations_per_request + 1}: Status {response.status_code}"
            )

            if response.status_code == 200:
                dados = response.json()
                if dados.get("status") == "OK":
                    batch_elevations = [
                        result.get("elevation")
                        for result in dados.get("results", [])
                    ]
                    elevations.extend(batch_elevations)
                else:
                    print(f"Erro na API: {dados.get('status')}")
                    elevations.extend([None] * len(batch))
            else:
                print(f"Erro na requisição: {response.status_code}")
                elevations.extend([None] * len(batch))

            # Pausa para evitar limites de taxa da API
            time.sleep(0.1)

        except Exception as e:
            print(f"Erro ao obter elevações: {str(e)}")
            elevations.extend([None] * len(batch))

    return elevations


def get_elevations_with_cache(
    locations: List[Tuple[float, float]],
    api_key: str,
    db_path: str = "elevation_cache.db",
) -> List[float]:
    """
    Obtém elevações usando cache local primeiro.

    Parameters:
        locations: List[Tuple[float, float]] - Lista de coordenadas (lat, lon)
        api_key: str - Chave da API do Google
        db_path: str - Caminho para o banco de dados de cache

    Returns:
        List[float] - Lista de elevações
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    elevations = []
    locations_to_fetch = []
    cached_count = 0

    # Verifica cache para cada localização
    for lat, lon in locations:
        cursor.execute(
            "SELECT elevation FROM elevations WHERE lat = ? AND lon = ?",
            (round(lat, 6), round(lon, 6)),
        )
        row = cursor.fetchone()

        if row and row[0] is not None and not np.isnan(row[0]):
            elevations.append(row[0])
            cached_count += 1
        else:
            elevations.append(None)
            locations_to_fetch.append((lat, lon))

    print(f"Encontrados {cached_count} pontos no cache")
    print(f"Necessário buscar {len(locations_to_fetch)} novos pontos")

    # Busca elevações não encontradas no cache
    if locations_to_fetch:
        fetched_elevations = get_elevations_batch(locations_to_fetch, api_key)

        # Atualiza lista de elevações e cache
        index = 0
        for i, elevation in enumerate(elevations):
            if elevation is None:
                elevation = fetched_elevations[index]
                elevations[i] = elevation
                index += 1

        # Atualiza cache
        cursor.executemany(
            "INSERT OR REPLACE INTO elevations (lat, lon, elevation) VALUES (?, ?, ?)",
            [
                (round(lat, 6), round(lon, 6), elev)
                for (lat, lon), elev in zip(
                    locations_to_fetch, fetched_elevations
                )
            ],
        )
        conn.commit()

    conn.close()
    return elevations


def process_lots_elevation(
    input_dir: str,
    output_dir: str,
    api_key: str,
    db_path: str = "elevation_cache.db",
    confidence: float = 0.62,
) -> List[Dict]:
    """
    Processa elevações para lotes usando arquivos locais.

    Args:
        input_dir (str): Diretório contendo os arquivos JSON processados
        output_dir (str): Diretório para salvar os resultados
        api_key (str): Chave da API do Google
        db_path (str): Caminho para o banco de dados de cache
        confidence (float): Valor mínimo de confiança para processar

    Returns:
        List[Dict]: Lista de documentos processados
    """
    # Inicializa cache
    init_elevation_cache(db_path)

    try:
        # Cria diretório de saída se não existir
        os.makedirs(output_dir, exist_ok=True)

        # Lista todos os arquivos JSON no diretório de entrada
        json_files = [f for f in os.listdir(input_dir) if f.endswith(".json")]
        print(f"\nTotal de arquivos para processar: {len(json_files)}")

        processed_docs = []

        for i, json_file in enumerate(json_files, 1):
            try:
                # Verifica se já existe arquivo processado
                output_file = os.path.join(output_dir, f"elevation_{json_file}")
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

                # Verifica se tem pontos lat/lon
                points_lat_lon = doc.get("point_colors", {}).get(
                    "points_lat_lon"
                )
                if not points_lat_lon:
                    print("Pontos lat/lon não encontrados, pulando...")
                    continue

                print(f"Total de pontos para elevação: {len(points_lat_lon)}")

                # Obtém elevações
                elevations = get_elevations_with_cache(
                    points_lat_lon, api_key, db_path
                )

                # Atualiza documento
                if "point_colors" not in doc:
                    doc["point_colors"] = {}
                doc["point_colors"]["lat_lon_elevation"] = elevations

                # Salva o documento processado
                with open(output_file, "w") as f:
                    json.dump(doc, f, indent=2)

                processed_docs.append(doc)
                print(f"Documento processado e salvo com sucesso!")
                print(
                    f"Elevações: min={min(elevations):.1f}m, max={max(elevations):.1f}m"
                )

            except Exception as e:
                print(f"Erro ao processar arquivo {json_file}: {str(e)}")
                traceback.print_exc()
                continue

        print("\n=== Resumo do processamento ===")
        print(f"Total de documentos: {len(json_files)}")
        print(f"Processados com sucesso: {len(processed_docs)}")
        print(f"Cache utilizado: {db_path}")
        print("==============================\n")

        return processed_docs

    except Exception as e:
        print(f"Erro durante o processamento: {str(e)}")
        raise
