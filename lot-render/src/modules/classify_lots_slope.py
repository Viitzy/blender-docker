from typing import List, Dict, Any, Optional
import pandas as pd
import math
import os
import json
import traceback
import numpy as np
import tempfile
from pymongo import MongoClient
from bson import ObjectId
from google.cloud import storage


def read_lot_data(csv_file: str) -> pd.DataFrame:
    """
    Lê o arquivo CSV com colunas:
    x, y, z, zone_number, zone_letter, r, g, b, hex_color, front, road

    Retorna um DataFrame pandas.
    """
    df = pd.read_csv(csv_file)
    return df


def get_front_and_back_centroids(df: pd.DataFrame):
    """
    Calcula o centróide (média de x, y, z) da frente e do fundo (restante).
    Retorna (centro_frente, centro_fundo).
    Cada centróide é um dicionário: {'x': ..., 'y': ..., 'z': ...}
    """
    df_front = df[df["front"] == 1]
    df_back = df[df["front"] == 0]

    # Caso raro: se não houver ponto front=1, você pode decidir lançar exceção ou tratar de outra forma
    if df_front.empty:
        raise ValueError("Não há pontos de frente (front=1) no arquivo.")

    # Cálculo da média
    front_centroid = {
        "x": df_front["x"].mean(),
        "y": df_front["y"].mean(),
        "z": df_front["z"].mean(),
    }
    # Se quiser, pode considerar apenas "fundo" vs. "frente",
    # ou então "todo o lote" vs. "frente".
    back_centroid = {
        "x": df_back["x"].mean(),
        "y": df_back["y"].mean(),
        "z": df_back["z"].mean(),
    }

    return front_centroid, back_centroid


def calculate_slope(front_centroid: dict, back_centroid: dict) -> float:
    """
    Calcula declividade (em %) entre a frente e o fundo do lote.
    Se resultado for +, é aclive. Se for -, é declive.
    """
    # Diferença de cota
    delta_z = back_centroid["z"] - front_centroid["z"]

    # Distância horizontal no plano XY
    dx = back_centroid["x"] - front_centroid["x"]
    dy = back_centroid["y"] - front_centroid["y"]
    horizontal_distance = math.sqrt(dx * dx + dy * dy)

    # Evitar divisão por zero (caso raro de X e Y serem iguais)
    if horizontal_distance == 0:
        # Se isso acontecer, podemos dizer que a declividade é 0% ou
        # levantar uma exceção ou alguma decisão de projeto.
        return 0.0

    slope_percent = (delta_z / horizontal_distance) * 100.0
    return slope_percent


def classify_slope(slope_percent: float) -> str:
    """
    Classifica de acordo com faixas de declividade (em %).
    slope_percent > 0 => uphill
    slope_percent < 0 => downhill
    """
    abs_slope = abs(slope_percent)

    if abs_slope < 5.0:
        return "Flat"
    elif 5.0 <= abs_slope < 12.0:
        return "Moderate Uphill" if slope_percent > 0 else "Moderate Downhill"
    elif 12.0 <= abs_slope < 20.0:
        return "Steep Uphill" if slope_percent > 0 else "Steep Downhill"
    else:
        # >= 20%
        return (
            "Very Steep Uphill" if slope_percent > 0 else "Very Steep Downhill"
        )


def get_altitude_stats(df: pd.DataFrame) -> dict:
    """
    Retorna o min, max e amplitude de altitude (z) do lote inteiro
    """
    z_min = df["z"].min()
    z_max = df["z"].max()
    amplitude = z_max - z_min

    return {"z_min": z_min, "z_max": z_max, "amplitude": amplitude}


def classify_lot_slope(csv_path: str) -> Dict[str, Any]:
    """
    Classifica a declividade de um lote baseado nos dados do CSV.

    Args:
        csv_path (str): Caminho para o arquivo CSV com os pontos do lote

    Returns:
        Dict[str, Any]: Dicionário com informações de declividade
    """
    try:
        # Lê o CSV
        df = pd.read_csv(csv_path)

        front_centroid, back_centroid = get_front_and_back_centroids(df)
        slope_percent = calculate_slope(front_centroid, back_centroid)
        classification = classify_slope(slope_percent)
        alt_stats = get_altitude_stats(df)

        return {
            "slope_percent": slope_percent,
            "classification": classification,
            "front_centroid": front_centroid,
            "back_centroid": back_centroid,
            "min_altitude": alt_stats["z_min"],
            "max_altitude": alt_stats["z_max"],
            "altitude_range": alt_stats["amplitude"],
        }

    except Exception as e:
        print(f"Erro ao classificar declividade: {str(e)}")
        raise


def process_lots_slope(
    mongodb_uri: str,
    year: str,
    doc_id: str = None,
    confidence: float = 0.62,
) -> None:
    """
    Processa a classificação de declividade para lotes específicos.

    Args:
        mongodb_uri (str): URI de conexão com MongoDB
        year (str): Ano de referência
        doc_id (str): ID específico do documento (opcional)
        confidence (float): Valor mínimo de confiança para processar o documento (default: 0.62)
    """
    client = None
    try:
        # Inicializa cliente do Google Cloud Storage
        storage_client = storage.Client()

        # Estabelece conexão com MongoDB
        client = MongoClient(mongodb_uri)
        db = client["gethome-01-hml"]
        collection = db["lots_detections_details_hmg"]

        # Prepara a query base
        base_query = {
            "$and": [
                {"csv_elevation_colors": {"$exists": True}},
                {"lot_details.slope_classify": {"$exists": False}},
                {"detection_result.confidence": {"$gte": confidence}},
            ]
        }

        # Adiciona doc_id à query se fornecido
        if doc_id:
            try:
                base_query["_id"] = ObjectId(doc_id)
            except Exception as e:
                print(f"Erro ao converter doc_id para ObjectId: {str(e)}")
                raise

        # Recupera documentos do MongoDB
        documents = collection.find(base_query)
        total_docs = collection.count_documents(base_query)

        print("\n=== Iniciando processamento de declividade ===")
        print(f"Total de documentos a processar: {total_docs}")
        print(f"Filtro de confiança: >= {confidence}")

        # Processa cada documento
        success_count = 0
        error_count = 0

        for doc in documents:
            try:
                # Extrai o caminho do CSV do URL
                csv_url = doc["csv_elevation_colors"]

                # Extrai o caminho relativo do arquivo no bucket
                csv_blob_path = csv_url.replace(
                    "https://storage.cloud.google.com/csv_from_have_allotment/",
                    "",
                )

                # Download do CSV do GCS
                bucket = storage_client.bucket("csv_from_have_allotment")
                blob = bucket.blob(csv_blob_path)

                # Cria diretório temporário
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Define caminho do arquivo temporário
                    temp_csv = os.path.join(temp_dir, f"{doc['_id']}.csv")

                    # Baixa o arquivo CSV do bucket
                    blob.download_to_filename(temp_csv)

                    print(f"Processando lote: {doc['_id']}")
                    print(f"CSV baixado para: {temp_csv}")

                    # Aplica a classificação
                    result = classify_lot_slope(temp_csv)

                    # Atualiza o documento no MongoDB
                    collection.update_one(
                        {"_id": doc["_id"]},
                        {"$set": {"lot_details.slope_classify": result}},
                    )

                    success_count += 1
                    print(f"✅ Lote {doc['_id']} processado com sucesso")
                    print(f"Declividade: {result['slope_percent']:.2f}%")
                    print(f"Classificação: {result['classification']}")

            except Exception as e:
                error_count += 1
                print(f"❌ Erro ao processar lote {doc['_id']}: {str(e)}")
                traceback.print_exc()
                continue

        # Imprime resumo
        print("\n=== Resumo do processamento ===")
        print(f"Total processado: {total_docs}")
        print(f"Sucessos: {success_count}")
        print(f"Erros: {error_count}")

    except Exception as e:
        print(f"Erro geral no processamento: {str(e)}")
        raise

    finally:
        # Fecha a conexão com segurança
        if client:
            try:
                client.close()
                print("✅ Conexão com MongoDB fechada com sucesso")
            except Exception as e:
                print(f"⚠️ Erro ao fechar conexão com MongoDB: {e}")
