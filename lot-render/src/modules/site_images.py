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
    outline_thickness: int = 4,
) -> np.ndarray:
    """
    Draw segment outline on image.

    Args:
        image: Input image
        contours: List of contours
        hex_color: Hex color for outline
        outline_thickness: Thickness of the outline in pixels

    Returns:
        Image with segment outline
    """
    # Create copy of image
    result = image.copy()

    # Convert hex color to BGR
    bgr_color = hex_to_bgr(hex_color)

    # Draw contours with specified thickness
    cv2.drawContours(result, contours, -1, bgr_color, outline_thickness)

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
    hex_color: str,
    doc_id: str = None,
    confidence: float = 0.62,
) -> list:
    """
    Processa imagens de lotes para exibição no site e salva no GCS.

    Args:
        mongodb_uri (str): URI de conexão com MongoDB
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
    storage_client = None
    try:
        # Initialize GCS with new bucket name
        storage_client = storage.Client()
        bucket = storage_client.bucket("images_from_have_allotment")

        # Connect to MongoDB
        client = MongoClient(mongodb_uri)
        db = client["gethome-01-hml"]
        collection = db["lots_detections_details_hmg"]

        # Consulta atualizada de acordo com a nova estrutura do documento
        query = {
            "image_info.url": {"$exists": True},
            "detection_result.confidence": {"$gte": confidence},
        }

        if doc_id:
            query["_id"] = ObjectId(doc_id)

        total_docs = collection.count_documents(query)
        print(f"Total de documentos para processar: {total_docs}")

        if total_docs == 0:
            print("Nenhum documento encontrado para processar")
            return []

        processed_docs = []

        for doc in collection.find(query):
            try:
                current_doc_id = str(doc["_id"])
                satellite_image_url = doc.get("image_info", {}).get("url")
                if not satellite_image_url:
                    print(
                        f"URL da imagem do satélite não encontrada para o documento {current_doc_id}"
                    )
                    continue

                # Extract blob path from gs:// URL, now using the new bucket name
                _, _, blob_path = satellite_image_url.partition(
                    "images_from_have_allotment/"
                )

                # Ensure the blob path starts with satellite_images/
                if not blob_path.startswith("satellite_images/"):
                    blob_path = f"satellite_images/{blob_path}"

                # Download to temporary file
                with tempfile.NamedTemporaryFile(
                    suffix=".jpg", delete=False
                ) as temp_file:
                    blob = bucket.blob(blob_path)
                    blob.download_to_filename(temp_file.name)

                    # Read image with OpenCV
                    image = cv2.imread(temp_file.name)
                    os.unlink(temp_file.name)

                    if image is None:
                        print("Falha ao decodificar a imagem")
                        continue

                    # Redimensiona para 1280x1280 se necessário
                    if image.shape[:2] != (1280, 1280):
                        image = cv2.resize(
                            image,
                            (1280, 1280),
                            interpolation=cv2.INTER_LANCZOS4,
                        )

                    # Prepara o contorno
                    if doc.get("detection_result"):
                        if "adjusted_mask" in doc["detection_result"]:
                            mask_annotation = doc["detection_result"][
                                "adjusted_mask"
                            ].get("yolov8_annotation")
                        else:
                            mask_annotation = doc["detection_result"].get(
                                "yolov8_annotation"
                            )

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
                    print(
                        f"Primeiro contorno: {contours[0][:3]}"
                    )  # Debug dos primeiros 3 pontos

                    # Aplica apenas o contorno
                    processed_image = draw_segment_with_watermark(
                        image=image,
                        contours=contours,
                        hex_color=hex_color,
                        outline_thickness=4,
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

                        # Upload para GCS na pasta site_images
                        site_blob_path = f"site_images/{current_doc_id}.jpg"
                        blob = bucket.blob(site_blob_path)
                        blob.upload_from_filename(temp_path)

                        # Gera URL pública com link direto
                        site_image_url = f"https://storage.cloud.google.com/images_from_have_allotment/{site_blob_path}"

                        # Atualiza MongoDB
                        collection.update_one(
                            {"_id": doc["_id"]},
                            {
                                "$set": {
                                    "image_info.image_thumb_site": site_image_url
                                }
                            },
                        )

                        processed_docs.append(
                            {
                                "id": current_doc_id,
                                "site_image_url": site_image_url,
                                "confidence": doc.get("confidence"),
                            }
                        )

                        print(f"Imagem processada e salva: {site_image_url}")

                    # Remove arquivo temporário
                    os.unlink(temp_path)

            except Exception as e:
                print(f"Erro ao processar documento {current_doc_id}: {str(e)}")
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
        if storage_client:
            try:
                storage_client.close()
                print("✅ Conexão com GCS fechada com sucesso")
            except Exception as e:
                print(f"⚠️ Erro ao fechar conexão com GCS: {e}")
