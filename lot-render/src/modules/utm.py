import os
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
import pyproj
import traceback
import utm


def convert_to_utm(lat: float, lon: float) -> Tuple[float, float, int]:
    """
    Convert lat/lon to UTM coordinates.

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        Tuple of (easting, northing, zone)
    """
    # Get UTM zone
    zone = int((lon + 180) / 6) + 1

    # Create projections
    wgs84 = pyproj.CRS("EPSG:4326")  # WGS84
    utm = pyproj.CRS(f"+proj=utm +zone={zone} +datum=WGS84")

    # Create transformer
    transformer = pyproj.Transformer.from_crs(wgs84, utm, always_xy=True)

    # Convert coordinates
    easting, northing = transformer.transform(lon, lat)

    return easting, northing, zone


def process_lots_utm_coordinates(
    input_dir: str,
    output_dir: str,
    confidence: float = 0.62,
) -> List[Dict]:
    """
    Processa coordenadas UTM para pontos de lotes usando arquivos locais.

    Args:
        input_dir (str): Diretório contendo os arquivos JSON com elevações
        output_dir (str): Diretório para salvar os resultados
        confidence (float): Valor mínimo de confiança para processar

    Returns:
        List[Dict]: Lista de documentos processados
    """
    print("\n=== Iniciando processamento de coordenadas UTM ===")
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
                output_file = os.path.join(output_dir, f"utm_{json_file}")
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

                # Obtém pontos lat/lon e elevações
                point_colors = doc.get("point_colors", {})
                points_lat_lon = point_colors.get("points_lat_lon")
                elevations = point_colors.get("lat_lon_elevation")

                if not points_lat_lon or not elevations:
                    print(
                        "Pontos lat/lon ou elevações não encontrados, pulando..."
                    )
                    continue

                if len(points_lat_lon) != len(elevations):
                    print(
                        f"ERRO: Número diferente de pontos ({len(points_lat_lon)}) e elevações ({len(elevations)})"
                    )
                    errors += 1
                    continue

                print(f"Processando {len(points_lat_lon)} pontos...")

                # Lista para armazenar coordenadas UTM
                points_utm = []

                # Processa cada ponto
                for (lat, lon), elevation in zip(points_lat_lon, elevations):
                    try:
                        # Converte para UTM
                        easting, northing, zone_number, zone_letter = (
                            utm.from_latlon(lat, lon)
                        )

                        # Armazena como [x, y, z, zone_number, zone_letter]
                        points_utm.append(
                            [
                                round(easting, 3),  # x
                                round(northing, 3),  # y
                                round(float(elevation), 3),  # z
                                zone_number,  # zone_number
                                zone_letter,  # zone_letter
                            ]
                        )

                    except Exception as e:
                        print(
                            f"ERRO ao converter ponto ({lat}, {lon}): {str(e)}"
                        )
                        points_utm.append([None, None, None, None, None])

                # Verifica se todos os pontos têm a mesma zona UTM
                unique_zones = set(
                    (p[3], p[4]) for p in points_utm if p[3] is not None
                )
                if len(unique_zones) > 1:
                    print(
                        f"AVISO: Pontos em diferentes zonas UTM: {unique_zones}"
                    )

                # Atualiza documento
                doc["point_colors"]["points_utm"] = points_utm

                # Salva o documento processado
                with open(output_file, "w") as f:
                    json.dump(doc, f, indent=2)

                processed_docs.append(doc)
                print(f"Documento processado e salvo com sucesso!")

                # Calcula estatísticas das coordenadas
                valid_points = [p for p in points_utm if p[0] is not None]
                if valid_points:
                    x_coords = [p[0] for p in valid_points]
                    y_coords = [p[1] for p in valid_points]
                    z_coords = [p[2] for p in valid_points]
                    print(f"Estatísticas UTM:")
                    print(
                        f"X: min={min(x_coords):.1f}, max={max(x_coords):.1f}"
                    )
                    print(
                        f"Y: min={min(y_coords):.1f}, max={max(y_coords):.1f}"
                    )
                    print(
                        f"Z: min={min(z_coords):.1f}, max={max(z_coords):.1f}"
                    )

            except Exception as e:
                errors += 1
                print(f"Erro ao processar arquivo {json_file}: {str(e)}")
                traceback.print_exc()
                continue

        print("\n=== Resumo do processamento UTM ===")
        print(f"Total de documentos: {len(json_files)}")
        print(f"Processados com sucesso: {len(processed_docs)}")
        print(f"Erros: {errors}")
        print("================================\n")

        return processed_docs

    except Exception as e:
        print(f"Erro durante o processamento: {str(e)}")
        raise
