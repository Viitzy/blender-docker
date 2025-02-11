from typing import Dict, Any, List
import os
import traceback
from pathlib import Path
import json
from .pixel_to_geo import pixel_to_latlon


from .google_roads_circle import process_lot_circle
from .front_view import visualize_lot_front


def process_single_document(
    document: Dict[str, Any], scale: int = 2
) -> Dict[str, Any]:
    """
    Processa um único documento, convertendo suas coordenadas YOLO para lat/lon.

    Args:
        document (Dict[str, Any]): Documento contendo os dados do lote
        scale (int): Fator de escala da imagem (default: 2)

    Returns:
        Dict[str, Any]: Dicionário com ID do documento e coordenadas processadas
    """
    try:
        print(f"\nProcessando documento: {document['id']}")

        # Obtém a anotação (preferindo a ajustada se disponível)
        annotation = document.get("adjusted_detection", {}).get(
            "annotation"
        ) or document.get("original_detection", {}).get("annotation")

        if not annotation:
            print("Anotação não encontrada no documento")
            return None

        # Obtém metadados necessários
        metadata = document.get("metadata", {})
        center_lat = metadata.get("latitude")
        center_lon = metadata.get("longitude")
        zoom = metadata.get("zoom", 20)

        if not all([center_lat, center_lon]):
            print("Coordenadas do centro não encontradas")
            return None

        # Converte coordenadas YOLO para pixels
        points = annotation.split()[1:]  # Remove o primeiro elemento (classe)
        image_size = 1280  # 640 * scale
        coordinates = []

        for i in range(0, len(points), 2):
            x_norm = float(points[i])
            y_norm = float(points[i + 1])

            # Converte para pixels
            pixel_x = int(x_norm * image_size)
            pixel_y = int(y_norm * image_size)

            # Converte para lat/lon
            lat, lon = pixel_to_latlon(
                pixel_x=pixel_x,
                pixel_y=pixel_y,
                center_lat=center_lat,
                center_lon=center_lon,
                zoom=zoom,
                scale=scale,
                image_width=image_size,
                image_height=image_size,
            )

            coordinates.append({"lat": lat, "lng": lon})

        return {"document_id": document["id"], "coordinates": coordinates}

    except Exception as e:
        print(f"Erro ao processar documento: {e}")
        traceback.print_exc()
        return None


def process_front_points(
    input_dir: str,
    output_dir: str,
    google_maps_api_key: str,
    create_maps: bool = False,
    confidence: float = 0.62,
    maps_output_dir: Path = Path("outputs/maps"),
) -> List[Dict]:
    """
    Processa lotes para identificar seus pontos frontais usando arquivos locais.

    Args:
        input_dir (str): Diretório contendo os arquivos JSON processados
        output_dir (str): Diretório para salvar os resultados
        google_maps_api_key (str): Chave da API do Google Maps
        create_maps (bool): Se deve criar mapas de visualização
        confidence (float): Valor mínimo de confiança para processar
        maps_output_dir (Path): Diretório onde os mapas serão salvos

    Returns:
        List[Dict]: Lista de documentos processados
    """
    results = []
    try:
        print("\n=== Iniciando processamento de pontos frontais ===")
        print(f"Filtro de confiança: >= {confidence}")

        # Cria diretórios de saída se não existirem
        os.makedirs(output_dir, exist_ok=True)
        if create_maps:
            maps_output_dir.mkdir(parents=True, exist_ok=True)
            print(f"\nDiretório de mapas: {maps_output_dir.absolute()}")

        # Lista todos os arquivos JSON no diretório de entrada
        json_files = [f for f in os.listdir(input_dir) if f.endswith(".json")]
        total_lots = len(json_files)
        print(f"\nTotal de lotes para processar: {total_lots}")

        for i, json_file in enumerate(json_files, 1):
            try:
                # Verifica se já existe arquivo processado
                output_file = os.path.join(output_dir, f"front_{json_file}")
                if os.path.exists(output_file):
                    print(
                        f"\nArquivo {output_file} já processado, carregando dados..."
                    )
                    with open(output_file, "r") as f:
                        doc = json.load(f)
                        results.append(doc)
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

                print(f"\n--- Processando lote {i}/{total_lots} ---")
                print(f"ID: {doc['id']}")

                # 1. Processar coordenadas do lote
                processed_lot = process_single_document(doc)
                if not processed_lot:
                    print("ERRO: Falha ao processar coordenadas do lote")
                    continue

                print(
                    f"\nCoordenadas processadas: {len(processed_lot['coordinates'])} pontos"
                )

                # 2. Processar círculo e obter pontos da rua
                circle_result = process_lot_circle(
                    processed_lot["coordinates"],
                )

                if not circle_result["success"]:
                    print(
                        f"ERRO: {circle_result.get('error', 'Falha ao processar círculo')}"
                    )
                    continue

                print("\nResultados do círculo:")
                print(f"- Centro: {circle_result['center']}")
                print(f"- Raio: {circle_result['radius']}")
                print(
                    f"- Pontos na rua: {len(circle_result['snapped_points'])}"
                )
                print(
                    f"- Ruas encontradas: {len(circle_result['streets_info'])}"
                )

                # 3. Encontrar pontos frontais
                if not circle_result["snapped_points"]:
                    print("ERRO: Nenhum ponto de rua encontrado")
                    continue

                front_points = find_closest_points(
                    processed_lot["coordinates"],
                    circle_result["snapped_points"],
                )

                if not front_points:
                    print("ERRO: Não foi possível determinar pontos frontais")
                    continue

                # 4. Atualizar documento
                point_colors = doc.get("point_colors", {})
                point_colors.update(
                    {
                        "front_points": front_points,
                        "front_points_lat_lon": front_points,
                        "street_points": circle_result["snapped_points"],
                        "street_info": (
                            circle_result["streets_info"][0]
                            if circle_result["streets_info"]
                            else None
                        ),
                    }
                )

                doc["point_colors"] = point_colors

                # Salvar documento processado
                with open(output_file, "w") as f:
                    json.dump(doc, f, indent=2)

                results.append(doc)

                # Criar visualização se solicitado
                if create_maps:
                    try:
                        save_path = (
                            maps_output_dir
                            / f"front_detection_{doc['id']}.html"
                        )
                        visualization_data = {
                            "lot_coordinates": processed_lot["coordinates"],
                            "snapped_points": circle_result["snapped_points"],
                            "streets_info": circle_result["streets_info"],
                            "front_vertices": front_points,
                            "front_vertex_indices": list(
                                range(len(front_points))
                            ),
                        }

                        visualize_lot_front(
                            result=visualization_data,
                            output_path=str(save_path),
                        )
                        print(f"✓ Mapa salvo em: {save_path}")
                    except Exception as e:
                        print(f"ERRO ao gerar visualização: {str(e)}")

            except Exception as e:
                print(f"ERRO ao processar arquivo {json_file}: {str(e)}")
                traceback.print_exc()

        print("\n=== Resumo do processamento ===")
        print(f"Total de lotes: {total_lots}")
        print(f"Processados com sucesso: {len(results)}")
        print("============================\n")

        return results

    except Exception as e:
        print(f"Erro durante o processamento: {str(e)}")
        traceback.print_exc()
        return results


def find_closest_points(
    lot_points: list, street_points: list, num_points: int = 2
) -> list:
    """
    Encontra os pontos do lote mais próximos dos pontos da rua.

    Args:
        lot_points (list): Lista de pontos do lote
        street_points (list): Lista de pontos da rua
        num_points (int): Número de pontos frontais a retornar

    Returns:
        list: Lista com os pontos frontais encontrados
    """
    from scipy.spatial.distance import cdist
    import numpy as np

    # Converter pontos para arrays numpy
    lot_coords = np.array([[p["lat"], p["lng"]] for p in lot_points])
    street_coords = np.array([[p["lat"], p["lng"]] for p in street_points])

    # Calcular matriz de distâncias
    distances = cdist(lot_coords, street_coords)

    # Encontrar os pontos mais próximos
    min_distances = np.min(distances, axis=1)
    closest_indices = np.argsort(min_distances)[:num_points]

    # Retornar os pontos mais próximos no formato original
    return [lot_points[i] for i in closest_indices]
