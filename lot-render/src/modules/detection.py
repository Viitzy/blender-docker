import os
from pathlib import Path
import json
from typing import List, Dict, Any, Optional
import cv2
import numpy as np
from ultralytics import YOLO
from datetime import datetime
from .poligonization import (
    calculate_polygon_area,
    select_best_polygon_adjustment,
)


def load_yolo_model(model_path: str):
    """
    Carrega o modelo YOLO (ultralytics).
    """
    model = YOLO(model_path)
    return model


def get_best_segmentation(
    model,
    img_512,
) -> Optional[Dict[str, Any]]:
    """
    Realiza a detecção e retorna a melhor segmentação.
    """
    try:
        print("\nIniciando segmentação com YOLOv8...")
        # Realiza a detecção
        results = model(img_512, verbose=True)
        print(f"Resultados obtidos: {len(results)}")

        if len(results) == 0:
            print("❌ Nenhum resultado retornado pelo modelo")
            return None

        if len(results[0].masks) == 0:
            print("❌ Nenhuma máscara encontrada no resultado")
            return None

        # Pega a primeira detecção (assumindo que é a melhor)
        result = results[0]
        print(f"✓ Máscara encontrada")
        print(f"  Total de máscaras: {len(result.masks)}")
        print(f"  Total de boxes: {len(result.boxes)}")

        # Extrai dados da máscara
        mask_data = result.masks[0]
        points = mask_data.xy[0]  # Pega apenas os pontos do primeiro polígono
        confidence = float(result.boxes[0].conf)
        class_id = int(result.boxes[0].cls)

        print(f"✓ Dados extraídos da máscara:")
        print(f"  Pontos: {len(points)}")
        print(f"  Confiança: {confidence:.3f}")
        print(f"  Classe: {class_id}")

        # Normaliza os pontos para o intervalo [0,1]
        normalized_points = points / 512  # Assumindo imagem 512x512
        print(f"✓ Pontos normalizados para intervalo [0,1]")

        return {
            "polygon": normalized_points,
            "confidence": confidence,
            "class_id": class_id,
        }

    except Exception as e:
        print(f"❌ Erro na segmentação: {str(e)}")
        import traceback

        traceback.print_exc()
        return None


def polygon_to_yolov8_mask_str(class_id: int, polygon: np.ndarray) -> str:
    """
    Converte um array (N, 2) [x, y], normalizado (0..1), para a
    string de anotação YOLOv8 no estilo:

    'classe x0 y0 x1 y1 x2 y2 ... xN yN'

    Exemplo (classe = 0):
    0 0.84765625 0.42578125 0.8125 0.228515625 ...

    polygon: np.ndarray com shape (N, 2)
    """
    # Inicia com a classe
    mask_str_list = [str(class_id)]

    # Adiciona as coordenadas x0,y0, x1,y1, ... xN,yN
    for x, y in polygon:
        mask_str_list.append(f"{x:.8f}")
        mask_str_list.append(f"{y:.8f}")

    # Retorna uma string única
    return " ".join(mask_str_list)


def detect_lots_and_save(
    model_path: str,
    items_list: list,
    adjust_mask: bool = False,
) -> list:
    """
    Detecta lotes nas imagens e salva resultados no MongoDB.

    Args:
        model_path: Caminho para o modelo YOLO
        items_list: Lista de itens com imagens para processar
        adjust_mask: Se True, aplica ajuste de máscara

    Returns:
        list: Lista de resultados processados
    """
    processed_docs = []

    try:
        # Carrega o modelo YOLO
        print("\n=== Iniciando detecção de lotes ===")
        print(f"Modelo: {model_path}")
        print(f"Total de itens: {len(items_list)}")
        print(f"Ajuste de máscara: {adjust_mask}")

        model = load_yolo_model(model_path)

        for item in items_list:
            try:
                item_id = item["object_id"]
                print(f"\nProcessando item: {item_id}")

                image_content = item.get("image_content")
                if not image_content:
                    print(
                        f"❌ Conteúdo da imagem não encontrado para {item_id}"
                    )
                    continue

                # Converte bytes para numpy array
                nparr = np.frombuffer(image_content, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is None:
                    print(f"❌ Erro ao decodificar imagem para {item_id}")
                    continue

                print(f"✓ Imagem decodificada com sucesso: {img.shape}")

                # Redimensiona para 512x512
                img_512 = cv2.resize(
                    img, (512, 512), interpolation=cv2.INTER_AREA
                )
                print("✓ Imagem redimensionada para 512x512")

                # Realiza a detecção
                print("\nExecutando detecção com YOLOv8...")
                seg_data = get_best_segmentation(model, img_512)

                if seg_data is None:
                    print(f"❌ Nenhuma detecção encontrada para item {item_id}")
                    continue

                print(f"✓ Detecção realizada com sucesso")
                print(f"  Confiança: {seg_data['confidence']:.3f}")
                print(f"  Classe: {seg_data['class_id']}")
                print(f"  Pontos do polígono: {len(seg_data['polygon'])}")

                # Calcula área original em pixels (normalizada)
                original_area_pixels = calculate_polygon_area(
                    seg_data["polygon"]
                )

                # Prepara documento base
                doc_to_save = {
                    "yolov8_annotation": polygon_to_yolov8_mask_str(
                        seg_data["class_id"], seg_data["polygon"]
                    ),
                    "confidence": seg_data["confidence"],
                    "object_id": item_id,
                    "latitude": item["latitude"],
                    "longitude": item["longitude"],
                    "dimensions": item["dimensions"],
                    "zoom": item["zoom"],
                    "street_name": item.get("street_name", ""),
                    "google_place_id": item.get("google_place_id", ""),
                    "year": item.get("year", ""),
                    "created_at": datetime.utcnow(),
                    "original_area_pixels": float(original_area_pixels),
                    "original_detection": {
                        "polygon": seg_data["polygon"].tolist(),
                        "confidence": seg_data["confidence"],
                        "class_id": seg_data["class_id"],
                    },
                }

                # Se adjust_mask=True, processa ajuste
                if adjust_mask:
                    print("\nAplicando ajuste de máscara...")
                    adjusted_polygon, adjustment_method = (
                        select_best_polygon_adjustment(
                            seg_data,
                            original_area_pixels,
                            size=(512, 512),
                        )
                    )

                    if adjusted_polygon is not None:
                        print(f"✓ Ajuste realizado: {adjustment_method}")
                        # Calcula área do polígono ajustado
                        adjusted_area_pixels = calculate_polygon_area(
                            adjusted_polygon
                        )
                        area_difference = (
                            adjusted_area_pixels - original_area_pixels
                        )
                        area_difference_percent = (
                            area_difference / original_area_pixels
                        ) * 100

                        doc_to_save["adjusted_detection"] = {
                            "polygon": adjusted_polygon.tolist(),
                            "adjustment_method": adjustment_method,
                            "annotation": polygon_to_yolov8_mask_str(
                                seg_data["class_id"], adjusted_polygon
                            ),
                            "adjusted_area_pixels": float(adjusted_area_pixels),
                            "area_difference_pixels": float(area_difference),
                            "area_difference_percent": float(
                                area_difference_percent
                            ),
                        }

                processed_docs.append(doc_to_save)
                print(f"✓ Item {item_id} processado com sucesso")

            except Exception as e:
                print(
                    f"❌ Erro processando item {item.get('object_id', 'N/A')}: {str(e)}"
                )
                continue

        print(f"\n=== Processamento finalizado ===")
        print(f"Total de documentos processados: {len(processed_docs)}")
        return processed_docs

    except Exception as e:
        print(f"❌ Erro durante o processamento: {str(e)}")
        return []
