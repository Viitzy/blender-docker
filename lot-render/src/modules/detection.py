import os
from pathlib import Path
import json
from typing import List, Dict, Any, Optional
import cv2
import numpy as np
from ultralytics import YOLO
from .poligonization import (
    calculate_polygon_area,
    select_best_polygon_adjustment,
)


def load_yolo_model(model_path: str):
    """
    Carrega o modelo YOLO (ultralytics).
    """
    model = YOLO(model_path)  # ex.: YOLO("caminho/para/best.pt")
    return model


def get_best_segmentation(
    model,
    img_512,
    mask_save_dir=None,
    mask_filename=None,
):
    """
    Realiza a detecção e retorna a melhor segmentação.
    """
    try:
        # Realiza a detecção
        results = model(img_512, verbose=True)

        if len(results) == 0 or len(results[0].masks) == 0:
            return None

        # Pega a primeira detecção (assumindo que é a melhor)
        result = results[0]

        # Extrai dados da máscara
        mask_data = result.masks[0]
        points = mask_data.xy[0]  # Pega apenas os pontos do primeiro polígono
        confidence = float(result.boxes[0].conf)
        class_id = int(result.boxes[0].cls)

        # Normaliza os pontos para o intervalo [0,1]
        normalized_points = points / 512  # Assumindo imagem 512x512

        # Se diretório de máscaras foi especificado, salva a máscara
        if mask_save_dir and mask_filename:
            mask_path = os.path.join(mask_save_dir, mask_filename)
            mask = (
                mask_data.data[0].cpu().numpy()
            )  # Pega apenas a primeira máscara
            mask = (mask * 255).astype(np.uint8)
            cv2.imwrite(mask_path, mask)

        return {
            "polygon": normalized_points,
            "confidence": confidence,
            "class_id": class_id,
        }

    except Exception as e:
        print(f"Erro na segmentação: {str(e)}")
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
    # Convertendo para string com alguma precisão.
    # Fique à vontade para ajustar a precisão (ex.: {:.6f})
    for x, y in polygon:
        mask_str_list.append(f"{x:.8f}")
        mask_str_list.append(f"{y:.8f}")

    # Retorna uma string única
    return " ".join(mask_str_list)


def detect_lots_and_save(
    model_path: str,
    items_list: list,
    output_dir: str,
    adjust_mask: bool = False,
) -> list:
    """
    Detecta lotes nas imagens e salva resultados em disco.

    Args:
        model_path: Caminho para o modelo YOLO
        items_list: Lista de itens com imagens para processar
        output_dir: Diretório base para salvar resultados
        adjust_mask: Se True, aplica ajuste de máscara

    Returns:
        list: Lista de resultados processados
    """
    processed_results = []

    try:
        # Carrega o modelo YOLO apenas se necessário
        model = None

        # Cria diretórios de saída
        results_dir = os.path.join(output_dir, "detections")
        masks_dir = os.path.join(output_dir, "masks")
        json_dir = os.path.join(output_dir, "json")

        for directory in [results_dir, masks_dir, json_dir]:
            os.makedirs(directory, exist_ok=True)

        for item in items_list:
            try:
                item_id = item["object_id"]

                # Verifica se os arquivos já existem
                mask_path = os.path.join(masks_dir, f"mask_{item_id}.png")
                json_path = os.path.join(json_dir, f"{item_id}.json")
                result_path = os.path.join(results_dir, f"{item_id}.png")

                # Se todos os arquivos existem, carrega os resultados existentes
                if all(
                    [
                        os.path.exists(p)
                        for p in [mask_path, json_path, result_path]
                    ]
                ):
                    print(f"\nArquivos existentes encontrados para {item_id}")
                    print(f"Carregando resultados de: {json_path}")

                    with open(json_path, "r") as f:
                        result = json.load(f)
                    processed_results.append(result)
                    continue

                # Se chegou aqui, precisa processar
                # Carrega o modelo YOLO se ainda não carregou
                if model is None:
                    print("Carregando modelo YOLO...")
                    model = load_yolo_model(model_path)

                # Carrega a imagem local
                image_path = item["image_path"]
                if not os.path.exists(image_path):
                    print(f"Imagem não encontrada: {image_path}")
                    continue

                # Lê e redimensiona a imagem
                img = cv2.imread(image_path)
                if img is None:
                    print(f"Erro ao ler imagem: {image_path}")
                    continue

                img_512 = cv2.resize(
                    img, (512, 512), interpolation=cv2.INTER_AREA
                )

                # Realiza a detecção
                seg_data = get_best_segmentation(
                    model,
                    img_512,
                    mask_save_dir=masks_dir,
                    mask_filename=f"mask_{item_id}.png",
                )

                if seg_data is None:
                    print(f"Nenhuma detecção encontrada para item {item_id}")
                    continue

                # Prepara resultado base
                result = {
                    "id": item_id,
                    "original_detection": {
                        "polygon": seg_data["polygon"].tolist(),
                        "confidence": seg_data["confidence"],
                        "annotation": polygon_to_yolov8_mask_str(
                            seg_data["class_id"], seg_data["polygon"]
                        ),
                    },
                    "metadata": {
                        "latitude": item["latitude"],
                        "longitude": item["longitude"],
                        "dimensions": item["dimensions"],
                        "zoom": item["zoom"],
                        "street_name": item.get("street_name", ""),
                        "google_place_id": item.get("google_place_id", ""),
                        "year": item.get("year", ""),
                        "original_image": image_path,
                    },
                }

                # Se adjust_mask=True, processa ajuste
                if adjust_mask:
                    adjusted_polygon, adjustment_method = (
                        select_best_polygon_adjustment(
                            seg_data,
                            calculate_polygon_area(seg_data["polygon"]),
                            size=(512, 512),
                        )
                    )

                    if adjusted_polygon is not None:
                        result["adjusted_detection"] = {
                            "polygon": adjusted_polygon.tolist(),
                            "adjustment_method": adjustment_method,
                            "annotation": polygon_to_yolov8_mask_str(
                                seg_data["class_id"], adjusted_polygon
                            ),
                        }

                # Salva resultado em JSON
                with open(json_path, "w") as f:
                    json.dump(result, f, indent=2)

                # Salva imagem original com máscaras
                result_img = img_512.copy()

                # Desenha máscara original (verde)
                points = (seg_data["polygon"] * 512).astype(np.int32)
                cv2.fillPoly(result_img, [points], (0, 255, 0))

                # Desenha máscara ajustada se existir (azul)
                if adjust_mask and "adjusted_detection" in result:
                    adj_points = (adjusted_polygon * 512).astype(np.int32)
                    cv2.fillPoly(result_img, [adj_points], (255, 0, 0))

                # Salva imagem com máscaras
                cv2.imwrite(result_path, result_img)

                print(f"Processado item {item_id}")
                print(f"Resultados salvos em:")
                print(f"- JSON: {json_path}")
                print(f"- Máscara: {mask_path}")
                print(f"- Imagem: {result_path}")

                processed_results.append(result)

            except Exception as e:
                print(f"Erro processando item: {str(e)}")
                continue

        return processed_results

    except Exception as e:
        print(f"Erro durante o processamento: {str(e)}")
        return []
