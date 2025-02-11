import os
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Tuple
import requests
import time
import numpy as np
import traceback
import googlemaps
from pymongo import MongoClient
from bson import ObjectId


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
    mongodb_uri: str,
    api_key: str,
    google_place_id: str = None,
    doc_id: str = None,
    db_path: str = "elevation_cache.db",
    confidence: float = 0.62,
) -> List[Dict]:
    """
    Processa elevações para lotes na collection.

    Args:
        mongodb_uri (str): URI de conexão com MongoDB
        api_key (str): Chave da API do Google
        google_place_id (str): ID do local Google para filtrar
        doc_id (str): ID específico do documento (opcional)
        db_path (str): Caminho para o banco de dados de cache
        confidence (float): Valor mínimo de confiança para processar o documento (default: 0.62)

    Returns:
        List[Dict]: Lista de documentos processados
    """
    # Inicializa cache
    init_elevation_cache(db_path)

    client = None
    try:
        # Estabelece conexão com MongoDB
        client = MongoClient(mongodb_uri)
        db = client.gethome
        collection = db.lots_coords

        # Monta a query base
        query = {
            "point_colors.points_lat_lon": {"$exists": True},
            "point_colors.lat_lon_elevation": {"$exists": False},
            "confidence": {"$gte": confidence},
        }

        # Se foi especificado um ID ou google_place_id, adiciona à query
        if doc_id:
            query["_id"] = ObjectId(doc_id)
            print(f"\n=== Processando elevação para documento específico ===")
            print(f"ID: {doc_id}")
        elif google_place_id:
            query["google_place_id"] = google_place_id
            print(f"\n=== Processando elevações para {google_place_id} ===")

        print(f"Filtro de confiança: >= {confidence}")

        total_docs = collection.count_documents(query)
        print(f"Total de documentos para processar: {total_docs}")

        if total_docs == 0:
            print("Nenhum documento encontrado para processar")
            return []

        processed_docs = []

        for i, doc in enumerate(collection.find(query), 1):
            try:
                print(f"\nProcessando documento {i}/{total_docs}")
                print(f"ID: {doc['_id']}")
                print(f"Rua: {doc.get('street_name', 'N/A')}")

                # Obtém pontos lat/lon
                points_lat_lon = doc["point_colors"]["points_lat_lon"]
                print(f"Total de pontos para elevação: {len(points_lat_lon)}")

                # Obtém elevações
                elevations = get_elevations_with_cache(
                    points_lat_lon, api_key, db_path
                )

                # Atualiza documento
                point_colors = doc["point_colors"]
                point_colors["lat_lon_elevation"] = elevations

                result = collection.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"point_colors": point_colors}},
                )

                if result.modified_count > 0:
                    doc["point_colors"] = point_colors
                    processed_docs.append(doc)
                    print(f"Documento {doc['_id']} atualizado com sucesso")
                    print(
                        f"Elevações: min={min(elevations):.1f}m, max={max(elevations):.1f}m"
                    )

            except Exception as e:
                print(f"Erro ao processar documento {doc.get('_id')}: {str(e)}")
                traceback.print_exc()
                continue

        print(f"\n=== Resumo do processamento ===")
        if google_place_id:
            print(f"Google Place ID: {google_place_id}")
        if doc_id:
            print(f"ID do documento: {doc_id}")
        print(f"Total de documentos: {total_docs}")
        print(f"Documentos processados: {len(processed_docs)}")
        print(f"Cache utilizado: {db_path}")
        print("=============================\n")

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
