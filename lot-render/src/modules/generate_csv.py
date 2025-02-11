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
        db = client.gethome
        collection = db.lots_coords
        doc = collection.find_one({"_id": ObjectId(doc_id)})

        if not doc:
            raise ValueError(f"Documento {doc_id} não encontrado")

        # Verifica se tem os dados necessários
        point_colors = doc.get("point_colors", {})
        if not all(
            key in point_colors for key in ["points_utm", "colors_adjusted"]
        ):
            raise ValueError("Dados de UTM ou cores não encontrados")

        # Prepara os dados para o CSV
        points_utm = point_colors["points_utm"]
        colors = point_colors["colors_adjusted"]

        if len(points_utm) != len(colors):
            raise ValueError("Número diferente de pontos e cores")

        # Cria DataFrame
        data = []
        for utm_point, color in zip(points_utm, colors):
            if not all(
                x is not None for x in utm_point[:3]
            ):  # Verifica x, y, z
                continue

            # Converte cor hex para RGB
            rgb = tuple(
                int(color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4)
            )

            data.append(
                {
                    "x": utm_point[0],  # easting
                    "y": utm_point[1],  # northing
                    "z": utm_point[2],  # elevation
                    "r": rgb[0],
                    "g": rgb[1],
                    "b": rgb[2],
                }
            )

        if not data:
            raise ValueError("Nenhum ponto válido para gerar CSV")

        df = pd.DataFrame(data)

        # Gera nome do arquivo
        filename = f"{doc_id}.csv"

        # Salva temporariamente
        temp_path = f"/tmp/{filename}"
        df.to_csv(temp_path, index=False)

        # Upload para GCS
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(f"lots_csv/{filename}")

        blob.upload_from_filename(temp_path)

        # Remove arquivo temporário
        os.remove(temp_path)

        # Atualiza URL no MongoDB
        csv_url = f"gs://{bucket_name}/lots_csv/{filename}"
        collection.update_one(
            {"_id": ObjectId(doc_id)},
            {"$set": {"csv_elevation_colors": csv_url}},
        )

        print(f"✓ CSV gerado e salvo em: {csv_url}")

    except Exception as e:
        print(f"Erro ao processar lote {doc_id}: {str(e)}")
        raise


def process_lots_csv(
    mongodb_uri: str,
    bucket_name: str,
    year: str,
    doc_id: Optional[str] = None,
    confidence: float = 0.62,
) -> None:
    """
    Processa lotes gerando arquivos CSV.

    Args:
        mongodb_uri (str): URI de conexão com MongoDB
        bucket_name (str): Nome do bucket no GCS
        year (str): Ano de referência
        doc_id (Optional[str]): ID específico do documento
        confidence (float): Valor mínimo de confiança
    """
    print("\n=== Iniciando processamento de lotes ===")
    print(f"Ano: {year}")
    print(f"Doc ID específico: {doc_id if doc_id else 'Todos os lotes'}")
    print(f"Filtro de confiança: >= {confidence}")

    client = None
    try:
        # Estabelece conexão com MongoDB
        client = MongoClient(mongodb_uri)
        db = client.gethome
        collection = db.lots_coords

        # Lista databases disponíveis
        print("\nBancos de dados disponíveis:")
        dbs = client.list_database_names()
        for db_name in dbs:
            print(f"- {db_name}")

        # Lista collections do banco
        print(f"\nCollections em gethome:")
        collections = db.list_collection_names()
        for col in collections:
            print(f"- {col}")

        # Conta documentos na collection
        total_docs = collection.count_documents({})
        print(f"\nTotal de documentos na collection: {total_docs}")

        # Define filtro
        filter_query = {
            "year": year,
            "confidence": {"$gte": confidence},
            "point_colors.points_utm": {"$exists": True},
            "point_colors.colors_adjusted": {"$exists": True},
            "csv_elevation_colors": {"$exists": False},
        }

        if doc_id:
            filter_query["_id"] = ObjectId(doc_id)

        # Busca documentos
        print("\nBuscando documentos no MongoDB...")
        print(f"Filtro: {filter_query}")

        # Tenta buscar apenas pelo ID primeiro
        if doc_id:
            doc_by_id = collection.find_one({"_id": ObjectId(doc_id)})
            if doc_by_id:
                print(f"\nDocumento encontrado pelo ID {doc_id}:")
                print(f"Ano: {doc_by_id.get('year')}")

        try:
            lots = collection.find(filter_query)
            lots_list = list(lots)
            total_lots = len(lots_list)

            if total_lots == 0:
                print(
                    "\n❌ Nenhum documento encontrado com os critérios especificados"
                )
                print("Verifique se:")
                print(f"1. O ano '{year}' está correto")
                if doc_id:
                    print(f"2. O Doc ID '{doc_id}' existe")
                print("\nDados disponíveis na collection:")

                # Mostra alguns exemplos de documentos para ajudar no debug
                sample_docs = collection.aggregate(
                    [
                        {"$sample": {"size": 1}},
                        {"$project": {"year": 1}},
                    ]
                )

                for doc in sample_docs:
                    print(f"Exemplo encontrado: Ano: {doc.get('year')}")

                # Verifica se o documento existe com o ID específico
                if doc_id:
                    doc = collection.find_one({"_id": ObjectId(doc_id)})
                    if doc:
                        print(
                            f"\nDocumento com ID {doc_id} existe, mas com dados diferentes:"
                        )
                        print(f"Ano no documento: {doc.get('year')}")
                    else:
                        print(
                            f"\nDocumento com ID {doc_id} não existe na collection"
                        )

                # Mostra anos disponíveis
                years = collection.distinct("year")
                if years:
                    print(f"\nAnos disponíveis na collection:")
                    for year_available in years:
                        print(f"- {year_available}")
                else:
                    print(f"\nNenhum documento encontrado com o Ano {year}")

                # Mostra alguns anos disponíveis
                years = collection.distinct("year")
                if years:
                    print("\nAlguns anos disponíveis na collection:")
                    for year_available in list(years)[
                        :5
                    ]:  # Mostra apenas os 5 primeiros
                        print(f"- {year_available}")

                return

            print(f"Encontrados {total_lots} lotes para processar")

            # Processa cada lote
            processed = 0
            errors = 0

            for idx, lot in enumerate(lots_list, 1):
                print(f"\nProcessando lote {idx}/{total_lots}")
                try:
                    process_lot_csv(client, str(lot["_id"]), bucket_name)
                    processed += 1
                except Exception as e:
                    print(f"❌ Erro ao processar lote {lot['_id']}: {str(e)}")
                    errors += 1
                    continue

            print("\n=== Processamento finalizado ===")
            print(f"Total de lotes: {total_lots}")
            print(f"Processados com sucesso: {processed}")
            print(f"Erros: {errors}")

            if errors > 0:
                print("\n⚠️ Alguns lotes não foram processados corretamente!")

        except Exception as e:
            print(f"\n❌ Erro ao acessar o MongoDB: {str(e)}")

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
