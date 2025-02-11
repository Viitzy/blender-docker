from typing import List, Dict
import pandas as pd
import math
import os
import json
import traceback


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
    # Se quiser, pode considerar apenas “fundo” vs. “frente”,
    # ou então “todo o lote” vs. “frente”.
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


def classify_lot_slope(csv_file: str) -> dict:
    """
    Lê o CSV de um lote, calcula declividade, encontra valores de altitude (mínimo, máximo, amplitude)
    e retorna um dicionário com todos esses resultados.
    """
    # Passo 1: Ler o CSV
    df = read_lot_data(csv_file)

    # Passo 2: Calcular centróides (frente e fundo)
    front_centroid, back_centroid = get_front_and_back_centroids(df)

    # Passo 3: Calcular declividade (%)
    slope_percent = calculate_slope(front_centroid, back_centroid)

    # Passo 4: Classificar
    classification = classify_slope(slope_percent)

    # Passo 5: Obter estatísticas de altitude
    alt_stats = get_altitude_stats(df)

    # Montar resultado final
    return {
        "slope_percent": slope_percent,
        "classification": classification,
        "front_centroid": front_centroid,
        "back_centroid": back_centroid,
        "min_altitude": alt_stats["z_min"],
        "max_altitude": alt_stats["z_max"],
        "altitude_range": alt_stats["amplitude"],
    }


def process_lots_slope(
    input_dir: str,
    output_dir: str,
    db_path: str,
    confidence: float = 0.62,
) -> List[Dict]:
    """
    Processa e classifica a inclinação dos lotes usando arquivos locais.
    """
    print("\n=== Iniciando processamento de inclinação dos lotes ===")
    print(f"Filtro de confiança: >= {confidence}")
    print(f"DB Path: {db_path}")

    try:
        # Cria diretório de saída se não existir
        os.makedirs(output_dir, exist_ok=True)

        # Lista todos os arquivos GLB no diretório de entrada
        glb_files = [f for f in os.listdir(input_dir) if f.endswith(".glb")]
        print(f"\nTotal de arquivos para processar: {len(glb_files)}")

        processed_docs = []
        errors = 0

        for i, glb_file in enumerate(glb_files, 1):
            try:
                # Define nomes dos arquivos
                base_name = os.path.splitext(glb_file)[0]
                output_file = os.path.join(
                    output_dir, f"{base_name}_slope.json"
                )
                input_glb = os.path.join(input_dir, glb_file)

                # Procura o arquivo CSV correspondente
                csv_dir = os.path.dirname(input_dir)
                csv_dir = os.path.join(csv_dir, "csv")
                csv_file = os.path.join(csv_dir, f"{base_name}.csv")

                # Procura o JSON no diretório front
                front_dir = os.path.dirname(input_dir)
                front_dir = os.path.join(front_dir, "front")
                json_file = os.path.join(front_dir, f"{base_name}.json")

                # Verifica se já existe arquivo processado
                if os.path.exists(output_file):
                    print(
                        f"\nArquivo {output_file} já processado, carregando dados..."
                    )
                    with open(output_file, "r") as f:
                        doc = json.load(f)
                        processed_docs.append(doc)
                    continue

                # Verifica se existe o CSV
                if not os.path.exists(csv_file):
                    print(f"Arquivo CSV não encontrado: {csv_file}")
                    continue

                # Carrega o documento JSON original
                if not os.path.exists(json_file):
                    print(f"Arquivo JSON não encontrado: {json_file}")
                    continue

                with open(json_file, "r") as f:
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

                print(f"\nProcessando documento {i}/{len(glb_files)}")
                print(f"ID: {doc['id']}")

                # Calcula a inclinação usando o CSV
                slope_info = classify_lot_slope(csv_file)

                if slope_info:
                    # Adiciona informações de inclinação ao documento
                    doc["slope_info"] = slope_info

                    # Salva o resultado
                    with open(output_file, "w") as f:
                        json.dump(doc, f, indent=2)

                    processed_docs.append(doc)
                    print(
                        f"Inclinação calculada: {slope_info['slope_percent']:.2f}%"
                    )
                    print(f"Classificação: {slope_info['classification']}")

            except Exception as e:
                errors += 1
                print(f"Erro ao processar arquivo {glb_file}: {str(e)}")
                traceback.print_exc()
                continue

        print("\n=== Resumo do processamento ===")
        print(f"Total de arquivos: {len(glb_files)}")
        print(f"Processados com sucesso: {len(processed_docs)}")
        print(f"Erros: {errors}")
        print("============================\n")

        return processed_docs

    except Exception as e:
        print(f"Erro durante o processamento: {str(e)}")
        traceback.print_exc()
        return []
