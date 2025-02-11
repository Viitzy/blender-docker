import os
import json
from pathlib import Path
from typing import Dict, List, Any
import cv2
import numpy as np
from PIL import Image
import tempfile
import traceback
from pymongo import MongoClient
from google.cloud import storage
from bson.objectid import ObjectId


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
    mongodb_uri: str,
    bucket_name: str,
    hex_color: str,
    watermark_path: str,
    doc_id: str = None,
    confidence: float = 0.62,
) -> list:
    """
    Processa imagens de lotes para exibição no site e salva no GCS.

    Args:
        mongodb_uri (str): URI de conexão com MongoDB
        bucket_name (str): Nome do bucket no GCS
        hex_color (str): Cor em hexadecimal para a máscara
        watermark_path (str): Caminho para a imagem de marca d'água
        doc_id (str): ID específico do documento (opcional)
        confidence (float): Valor mínimo de confiança

    Returns:
        list: Lista de documentos processados
    """
    print(f"\nIniciando processamento de imagens para o site")
    print(f"Filtro de confiança: >= {confidence}")

    client = None
    try:
        # Inicializa cliente do GCS
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)

        # Estabelece conexão com MongoDB
        client = MongoClient(mongodb_uri)
        db = client.gethome
        collection = db.lots_coords

        # Monta a query base
        query = {
            "site_image_url": {"$exists": False},
            "confidence": {"$gte": confidence},
        }

        # Se foi especificado um ID, adiciona à query
        if doc_id:
            query["_id"] = ObjectId(doc_id)
            print(f"Processando documento específico: {doc_id}")

        total_docs = collection.count_documents(query)
        print(f"Total de documentos para processar: {total_docs}")

        if total_docs == 0:
            print("Nenhum documento encontrado para processar")
            return []

        processed_docs = []

        for doc in collection.find(query):
            try:
                doc_id = str(doc["_id"])
                print(f"\nProcessando documento: {doc_id}")

                # Obtém a imagem original do satélite
                image_content = doc.get("satellite_image")
                if not image_content:
                    print("Imagem do satélite não encontrada")
                    continue

                # Converte bytes para numpy array
                nparr = np.frombuffer(image_content, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if image is None:
                    print("Falha ao decodificar a imagem")
                    continue

                # Redimensiona para 1280x1280 se necessário
                if image.shape[:2] != (1280, 1280):
                    image = cv2.resize(
                        image, (1280, 1280), interpolation=cv2.INTER_LANCZOS4
                    )

                # Prepara o contorno usando a anotação ajustada se disponível
                mask_annotation = doc.get("adjusted_detection", {}).get(
                    "annotation"
                ) or doc.get("original_detection", {}).get("annotation")
                if not mask_annotation:
                    print("Nenhuma anotação de máscara encontrada")
                    continue

                # Converte anotação em contornos
                contours = yolov8_annotation_to_contours(
                    mask_annotation, image.shape[:2]
                )

                # Aplica máscara e marca d'água
                processed_image = draw_segment_with_watermark(
                    image=image,
                    contours=contours,
                    hex_color=hex_color,
                    watermark_path=watermark_path,
                )

                # Salva temporariamente
                with tempfile.NamedTemporaryFile(
                    suffix=".jpg", delete=False
                ) as temp_file:
                    temp_path = temp_file.name
                    encode_params = [
                        cv2.IMWRITE_JPEG_QUALITY,
                        95,
                        cv2.IMWRITE_JPEG_OPTIMIZE,
                        1,
                    ]
                    cv2.imwrite(temp_path, processed_image, encode_params)

                    # Upload para GCS
                    blob_path = f"site_images/{doc_id}.jpg"
                    blob = bucket.blob(blob_path)
                    blob.upload_from_filename(temp_path)

                    # Gera URL pública
                    site_image_url = f"gs://{bucket_name}/{blob_path}"

                    # Atualiza MongoDB
                    collection.update_one(
                        {"_id": doc["_id"]},
                        {"$set": {"site_image_url": site_image_url}},
                    )

                    processed_docs.append(
                        {
                            "id": doc_id,
                            "site_image_url": site_image_url,
                            "confidence": doc.get("confidence"),
                        }
                    )

                    print(f"Imagem processada e salva: {site_image_url}")

                # Remove arquivo temporário
                os.unlink(temp_path)

            except Exception as e:
                print(f"Erro ao processar documento {doc_id}: {str(e)}")
                traceback.print_exc()
                continue

        print(
            f"\nProcessamento finalizado. {len(processed_docs)} documentos processados"
        )
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
