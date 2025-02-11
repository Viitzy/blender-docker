from pathlib import Path
import os
from datetime import datetime
from typing import Dict, Any, List
from bson import ObjectId

from ...apis.google_maps import GoogleMapsAPI
from ...modules.detection import detect_lots_and_save
from ...modules.pixel_to_geo import pixel_to_latlon
from ...database.mongodb import MongoDB


async def detect_lot_service(
    latitude: float,
    longitude: float,
    zoom: int = 20,
    confidence: float = 0.62,
    object_id: str = None,
    year: str = None,
) -> Dict[str, Any]:
    """
    Service that detects a lot and returns its polygon points.
    """
    try:
        # Initialize services
        google_maps = GoogleMapsAPI()
        mongo_db = MongoDB()

        # Load environment variables
        model_path = os.getenv("YOLO_MODEL_PATH")
        if not model_path:
            raise ValueError("YOLO_MODEL_PATH not found")

        # Create initial document
        initial_data = {
            "latitude": latitude,
            "longitude": longitude,
            "dimensions": "1280x1280",
            "zoom": zoom,
            "object_id": object_id or str(ObjectId()),
            "year": year or str(datetime.now().year),
        }

        # Insert initial document
        doc_id = await mongo_db.insert_detection(initial_data)

        # Get satellite image
        print(
            f"Detection - Getting satellite image for coordinates: {latitude}, {longitude}"
        )
        image_content = google_maps.get_satellite_image(
            lat=latitude,
            lng=longitude,
            zoom=zoom,
            size="640x640",
            scale=2,
        )

        # Prepare items list for detection
        items_list = [
            {
                "image_content": image_content,
                "object_id": initial_data["object_id"],
                "latitude": latitude,
                "longitude": longitude,
                "dimensions": "1280x1280",
                "zoom": zoom,
                "year": initial_data["year"],
            }
        ]

        # Execute lot detection
        print(f"Detection - Starting lot detection with model: {model_path}")
        processed_docs = detect_lots_and_save(
            model_path=model_path,
            items_list=items_list,
            adjust_mask=True,
        )

        if not processed_docs:
            return {
                "id": doc_id,
                "status": "error",
                "error": "No lots detected in the image",
                "points": [],
            }

        # Get detection data
        detection = processed_docs[0]
        width = height = 1280  # 640x640 with scale=2

        # Função auxiliar para converter pontos para lat/lon
        def convert_points_to_latlon(points):
            converted_points = []
            for x, y in points:
                pixel_x = x * width
                pixel_y = y * height
                lat, lon = pixel_to_latlon(
                    pixel_x=pixel_x,
                    pixel_y=pixel_y,
                    center_lat=latitude,
                    center_lon=longitude,
                    zoom=zoom,
                    scale=2,
                    image_width=width,
                    image_height=height,
                )
                converted_points.append({"lat": lat, "lon": lon})
            return converted_points

        # Converte pontos originais e ajustados para lat/lon
        original_points = convert_points_to_latlon(
            detection["original_detection"]["polygon"]
        )

        # Prepara dados para atualização do MongoDB
        update_data = {
            "yolov8_annotation": detection["yolov8_annotation"],
            "confidence": detection["confidence"],
            "original_detection": {
                **detection["original_detection"],
                "polygon_latlon": original_points,
            },
            "original_area_pixels": detection["original_area_pixels"],
            "metadata": {
                "latitude": latitude,
                "longitude": longitude,
                "dimensions": "1280x1280",
                "zoom": zoom,
                "year": initial_data["year"],
            },
        }

        # Se houver detecção ajustada, converte seus pontos também
        points_to_return = original_points
        if "adjusted_detection" in detection:
            adjusted_points = convert_points_to_latlon(
                detection["adjusted_detection"]["polygon"]
            )
            update_data["adjusted_detection"] = {
                **detection["adjusted_detection"],
                "polygon_latlon": adjusted_points,
            }
            points_to_return = adjusted_points

        # Atualiza MongoDB com todos os dados
        await mongo_db.update_detection(doc_id, update_data)

        # Retorna os pontos ajustados se disponíveis, senão os originais
        return {"id": doc_id, "status": "success", "points": points_to_return}

    except Exception as e:
        return {
            "id": str(ObjectId()),
            "status": "error",
            "error": str(e),
            "points": [],
        }
