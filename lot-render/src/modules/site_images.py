import os
import json
from pathlib import Path
from typing import Dict, List, Any
import cv2
import numpy as np
from PIL import Image


def hex_to_bgr(hex_color: str) -> tuple:
    """Convert hex color to BGR."""
    hex_color = hex_color.lstrip("#")
    rgb = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    return (rgb[2], rgb[1], rgb[0])


def draw_segment_with_watermark(
    image: np.ndarray,
    contours: List,
    hex_color: str = "#e8f34e",
    alpha: float = 0.5,
    outline_alpha: float = 0.8,
    watermark_path: str = None,
    watermark_scale: float = 0.2,
) -> np.ndarray:
    """
    Draw segment with watermark on image.

    Args:
        image: Input image
        contours: List of contours
        hex_color: Hex color for segment
        alpha: Segment transparency
        outline_alpha: Outline transparency
        watermark_path: Path to watermark image
        watermark_scale: Scale factor for watermark

    Returns:
        Image with segment and watermark
    """
    # Create copy of image
    result = image.copy()

    # Create mask for segment
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    cv2.drawContours(mask, contours, -1, 255, -1)

    # Create colored overlay
    overlay = np.zeros_like(image)
    bgr_color = hex_to_bgr(hex_color)
    overlay[mask > 0] = bgr_color

    # Blend overlay with image
    cv2.addWeighted(overlay, alpha, result, 1, 0, result)

    # Draw contours
    outline = np.zeros_like(image)
    cv2.drawContours(outline, contours, -1, bgr_color, 2)
    cv2.addWeighted(outline, outline_alpha, result, 1, 0, result)

    # Add watermark if provided
    if watermark_path and os.path.exists(watermark_path):
        try:
            # Load and resize watermark
            watermark = cv2.imread(watermark_path, cv2.IMREAD_UNCHANGED)
            if (
                watermark is not None and watermark.shape[2] == 4
            ):  # With alpha channel
                h, w = image.shape[:2]
                new_h = int(h * watermark_scale)
                new_w = int(new_h * watermark.shape[1] / watermark.shape[0])
                watermark = cv2.resize(watermark, (new_w, new_h))

                # Position watermark at bottom right
                y = h - new_h - 10
                x = w - new_w - 10

                # Extract alpha channel
                alpha_channel = watermark[:, :, 3] / 255.0

                # Blend watermark
                for c in range(3):
                    result[y : y + new_h, x : x + new_w, c] = (
                        result[y : y + new_h, x : x + new_w, c]
                        * (1 - alpha_channel)
                        + watermark[:, :, c] * alpha_channel
                    )
        except Exception as e:
            print(f"Error adding watermark: {str(e)}")

    return result


def yolov8_annotation_to_contours(annotation: str, image_shape: tuple) -> list:
    """
    Converte uma string de anotação YOLOv8 em contornos OpenCV.

    Parameters:
        annotation: str - String de anotação YOLOv8
        image_shape: tuple - (height, width) da imagem

    Returns:
        list - Lista de contornos no formato OpenCV
    """
    # Divide a string em valores
    values = annotation.strip().split()

    # Remove o class_id (primeiro valor)
    coordinates = values[1:]

    # Converte para float e reshape para pares (x,y)
    points = np.array([float(x) for x in coordinates]).reshape(-1, 2)

    # Desnormaliza as coordenadas
    height, width = image_shape
    points[:, 0] *= width
    points[:, 1] *= height

    # Converte para inteiros
    points = points.astype(np.int32)

    return [points]


def process_lot_images_for_site(
    input_dir: str,
    output_dir: str,
    hex_color: str,
    watermark_path: str,
    confidence: float = 0.62,
) -> list:
    """
    Processa imagens de lotes para exibição no site usando arquivos locais.

    Args:
        input_dir (str): Diretório contendo os arquivos JSON de detecção
        output_dir (str): Diretório para salvar as imagens processadas
        hex_color (str): Cor em hexadecimal para a máscara
        watermark_path (str): Caminho para a imagem de marca d'água
        confidence (float): Valor mínimo de confiança para processar o documento (default: 0.62)

    Returns:
        list: Lista de documentos processados
    """
    print(f"\nIniciando processamento de imagens para o site")
    print(f"Diretório de entrada: {input_dir}")
    print(f"Filtro de confiança: >= {confidence}")

    try:
        # Cria diretório de saída se não existir
        os.makedirs(output_dir, exist_ok=True)

        # Lista todos os arquivos JSON no diretório de entrada
        json_files = [f for f in os.listdir(input_dir) if f.endswith(".json")]
        print(f"Encontrados {len(json_files)} arquivos JSON para processar")

        if not json_files:
            print(f"Nenhum arquivo encontrado para processar")
            return []

        processed_docs = []

        for json_file in json_files:
            try:
                json_path = os.path.join(input_dir, json_file)
                print(f"\nProcessando arquivo: {json_file}")

                # Carrega o documento JSON
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

                # Obtém o caminho da imagem original
                image_path = doc.get("metadata", {}).get("original_image")
                if not image_path or not os.path.exists(image_path):
                    print(f"Imagem original não encontrada: {image_path}")
                    continue

                # Carrega e verifica a imagem original
                image = cv2.imread(image_path)
                if image is None:
                    print(f"Falha ao carregar a imagem")
                    continue

                print(f"Dimensões da imagem original: {image.shape}")

                # Redimensiona para 1280x1280 se necessário
                if image.shape[:2] != (1280, 1280):
                    print(f"Redimensionando imagem para 1280x1280")
                    image = cv2.resize(
                        image, (1280, 1280), interpolation=cv2.INTER_LANCZOS4
                    )

                # Prepara o contorno usando a anotação ajustada se disponível
                mask_annotation = doc.get("adjusted_detection", {}).get(
                    "annotation"
                ) or doc.get("original_detection", {}).get("annotation")

                if not mask_annotation:
                    print(f"Nenhuma anotação de máscara encontrada")
                    continue

                # Converte anotação em contornos
                contours = yolov8_annotation_to_contours(
                    mask_annotation, image.shape[:2]
                )
                print(
                    f"Contornos gerados com shape da imagem: {image.shape[:2]}"
                )

                # Aplica máscara e marca d'água
                processed_image = draw_segment_with_watermark(
                    image=image,
                    contours=contours,
                    hex_color=hex_color,
                    watermark_path=watermark_path,
                )

                # Gera nome do arquivo de saída
                output_filename = f"site_{os.path.splitext(json_file)[0]}.jpg"
                output_path = os.path.join(output_dir, output_filename)

                # Salva a imagem processada com alta qualidade
                encode_params = [
                    cv2.IMWRITE_JPEG_QUALITY,
                    95,
                    cv2.IMWRITE_JPEG_OPTIMIZE,
                    1,
                ]
                cv2.imwrite(output_path, processed_image, encode_params)

                processed_docs.append(
                    {
                        "object_id": doc.get("id"),
                        "site_image_path": output_path,
                        "original_image": image_path,
                        "confidence": confidence_value,
                    }
                )

                print(f"Imagem processada salva em: {output_path}")

            except Exception as e:
                print(f"Erro ao processar arquivo {json_file}: {str(e)}")
                continue

        print(
            f"\nProcessamento finalizado. {len(processed_docs)} documentos processados"
        )
        return processed_docs

    except Exception as e:
        print(f"Erro durante o processamento: {str(e)}")
        raise
