from typing import Dict, Any, List
import pandas as pd
import os
import utm
import json
import traceback


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


def process_lots_csv(
    input_dir: str,
    output_dir: str,
    confidence: float = 0.62,
) -> List[Dict]:
    """
    Processa lotes e gera CSVs usando arquivos locais.

    Args:
        input_dir (str): Diretório contendo os arquivos JSON processados
        output_dir (str): Diretório para salvar os CSVs
        confidence (float): Valor mínimo de confiança para processar

    Returns:
        List[Dict]: Lista de documentos processados
    """
    print("\n=== Iniciando processamento de CSVs ===")
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
                # Define nomes dos arquivos
                base_name = os.path.splitext(json_file)[0]
                output_file = os.path.join(output_dir, f"{base_name}.csv")
                input_json = os.path.join(input_dir, json_file)

                # Verifica se já existe arquivo processado
                if os.path.exists(output_file):
                    print(
                        f"\nArquivo {output_file} já processado, carregando dados..."
                    )
                    with open(input_json, "r") as f:
                        doc = json.load(f)
                        processed_docs.append(doc)
                    continue

                # Carrega o documento JSON
                with open(input_json, "r") as f:
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

                # Gera o DataFrame
                df = generate_lot_csv(doc)
                print(f"DataFrame gerado com {len(df)} pontos")

                # Salva o CSV
                df.to_csv(output_file, index=False)
                print(f"CSV salvo em: {output_file}")

                processed_docs.append(doc)

            except Exception as e:
                errors += 1
                print(f"Erro ao processar arquivo {json_file}: {str(e)}")
                traceback.print_exc()
                continue

        print("\n=== Resumo do processamento ===")
        print(f"Total de arquivos: {len(json_files)}")
        print(f"Processados com sucesso: {len(processed_docs)}")
        print(f"Erros: {errors}")
        print("============================\n")

        return processed_docs

    except Exception as e:
        print(f"Erro durante o processamento: {str(e)}")
        traceback.print_exc()
        return []
