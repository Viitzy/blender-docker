from typing import Dict, Any, List
import os
import traceback
from pathlib import Path
import json
from .pixel_to_geo import pixel_to_latlon
from pymongo import MongoClient
from bson import ObjectId

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
    mongodb_uri: str,
    google_maps_api_key: str,
    create_maps: bool = False,
    doc_id: str = None,
    confidence: float = 0.62,
    output_dir: Path = Path("/app/generated/maps"),
    force_visualization: bool = True,
) -> List[Dict]:
    """
    Processa lotes para identificar seus pontos frontais usando detecção baseada em ruas próximas.

    Args:
        mongodb_uri (str): URI de conexão com MongoDB
        google_maps_api_key (str): Chave da API do Google Maps
        create_maps (bool): Se deve criar mapas de visualização
        doc_id (str): ID específico de documento para processar (opcional)
        confidence (float): Valor mínimo de confiança para processar o documento (default: 0.62)
        output_dir (Path): Diretório onde os mapas serão salvos (default: outputs/maps)
        force_visualization (bool): Se True, gera visualização mesmo sem modificações no MongoDB

    Returns:
        List[Dict]: Lista de documentos processados
    """
    processed_docs = []
    client = None

    try:
        print("\n=== Iniciando processamento de pontos frontais ===")
        print(f"Filtro de confiança: >= {confidence}")

        # Estabelece conexão com MongoDB
        client = MongoClient(mongodb_uri)
        db = client["gethome-01-hml"]
        collection = db["lots_detections_details_hmg"]

        # Prepara query
        query = {
            "$and": [
                {"lot_details.point_colors.points_lat_lon": {"$exists": True}},
                {"lot_details.cardinal_points": {"$exists": True}},
                {
                    "$or": [
                        {
                            "lot_details.point_colors.front_points": {
                                "$exists": False
                            }
                        },
                        {"lot_details.point_colors.front_points": {"$size": 0}},
                    ]
                },
                {"detection_result.confidence": {"$gte": confidence}},
            ]
        }

        if doc_id:
            query["_id"] = ObjectId(doc_id)
            print(f"Processando documento específico: {doc_id}")

        total_lots = collection.count_documents(query)
        print(f"Total de lotes para processar: {total_lots}")

        # Criar diretório de saída se não existir
        if create_maps:
            output_dir.mkdir(parents=True, exist_ok=True)
            print(f"\nDiretório de saída: {output_dir.absolute()}")

        for i, lot in enumerate(collection.find(query), 1):
            lot_id = str(lot.get("_id"))
            print(f"\n--- Processando lote {i}/{total_lots} ---")
            print(f"ID: {lot_id}")

            try:
                # Obtém pontos lat/lon do novo formato
                coordinates = (
                    lot.get("lot_details", {})
                    .get("point_colors", {})
                    .get("points_lat_lon", [])
                )
                if not coordinates:
                    print("ERRO: Pontos lat/lon não encontrados")
                    continue

                # Converte para o formato esperado pela função process_lot_circle
                coordinates = [{"lat": p[0], "lng": p[1]} for p in coordinates]

                print(f"\nCoordenadas processadas: {len(coordinates)} pontos")

                # 2. Processar círculo e obter pontos da rua
                circle_result = process_lot_circle(coordinates)
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

                # Encontrar os dois pontos do lote mais próximos dos pontos da rua
                front_points = find_closest_points(
                    coordinates,
                    circle_result["snapped_points"],
                )

                print("\nPontos frontais encontrados:")
                print(f"- Total: {len(front_points)}")
                for idx, point in enumerate(front_points):
                    print(
                        f"- Ponto {idx}: lat={point['lat']}, lng={point['lng']}"
                    )

                if not front_points:
                    print("ERRO: Não foi possível determinar pontos frontais")
                    continue

                # 4. Atualizar documento no MongoDB com a nova estrutura
                if "lot_details" not in lot:
                    lot["lot_details"] = {}
                if "point_colors" not in lot["lot_details"]:
                    lot["lot_details"]["point_colors"] = {}

                # Preparar dados para atualização
                update_data = {
                    "lot_details.point_colors.front_points": front_points,
                    "lot_details.point_colors.street_points": circle_result[
                        "snapped_points"
                    ],
                    "lot_details.point_colors.street_info": (
                        circle_result["streets_info"][0]
                        if circle_result["streets_info"]
                        else {}
                    ),
                }

                # Verificar se houve mudança nos dados
                current_front_points = (
                    lot.get("lot_details", {})
                    .get("point_colors", {})
                    .get("front_points", [])
                )

                print("\nComparando dados atuais com novos:")
                print(f"- Front points atuais: {len(current_front_points)}")
                print(f"- Novos front points: {len(front_points)}")

                # Atualizar apenas se os dados forem diferentes
                if current_front_points != front_points:
                    print("\nTentando atualizar MongoDB com:")
                    print(f"- Front points: {len(front_points)} pontos")
                    print(
                        f"- Street points: {len(circle_result['snapped_points'])} pontos"
                    )
                    print(
                        f"- Street info: {'Sim' if circle_result['streets_info'] else 'Não'}"
                    )

                    result = collection.update_one(
                        {"_id": lot["_id"]},
                        {"$set": update_data},
                    )

                    if result.modified_count > 0:
                        print("\n✓ Documento atualizado com sucesso")
                        # Atualizar o documento em memória
                        lot["lot_details"]["point_colors"].update(
                            {
                                "front_points": front_points,
                                "street_points": circle_result[
                                    "snapped_points"
                                ],
                                "street_info": (
                                    circle_result["streets_info"][0]
                                    if circle_result["streets_info"]
                                    else {}
                                ),
                            }
                        )
                        processed_docs.append(lot)
                    else:
                        print("\n⚠ AVISO: Documento não foi modificado")
                        print("- Verifique se houve erro na atualização")
                else:
                    print("\n⚠ AVISO: Dados idênticos aos existentes")
                    print("- Nenhuma atualização necessária")

                # Criar mapa de visualização se solicitado
                # if create_maps or force_visualization:
                #     try:
                #         save_path = (
                #             output_dir / f"front_detection_{lot_id}.html"
                #         )
                #         visualization_data = {
                #             "lot_coordinates": coordinates,
                #             "snapped_points": circle_result["snapped_points"],
                #             "streets_info": circle_result["streets_info"],
                #             "front_vertices": front_points,
                #             "front_vertex_indices": list(
                #                 range(len(front_points))
                #             ),
                #         }

                #         print("\nCriando visualização:")
                #         print(f"- Caminho absoluto: {save_path.absolute()}")
                #         print(
                #             f"- Dados: {len(visualization_data['lot_coordinates'])} pontos do lote"
                #         )
                #         print(
                #             f"- Pontos na rua: {len(visualization_data['snapped_points'])}"
                #         )
                #         print(
                #             f"- Pontos frontais: {len(visualization_data['front_vertices'])}"
                #         )

                #         visualize_lot_front(
                #             result=visualization_data,
                #             output_path=str(save_path),
                #         )
                #         print("✓ Mapa salvo com sucesso")
                #     except Exception as e:
                #         print(f"\n❌ ERRO ao gerar visualização: {str(e)}")
                #         print(traceback.format_exc())

            except Exception as e:
                print(f"\n❌ ERRO ao processar lote: {str(e)}")
                print(traceback.format_exc())

        print("\n=== Resumo do processamento ===")
        print(f"Total processado: {total_lots}")
        print(f"Sucessos: {len(processed_docs)}")
        print("============================\n")

        return processed_docs

    except Exception as e:
        print(f"Erro durante o processamento: {str(e)}")
        raise

    finally:
        if client:
            try:
                client.close()
                print("✅ Conexão com MongoDB fechada com sucesso")
            except Exception as e:
                print(f"⚠️ Erro ao fechar conexão com MongoDB: {e}")


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
