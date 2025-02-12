from pathlib import Path
import os
from datetime import datetime
from typing import Dict, Any, List
from bson import ObjectId
import tempfile

from ...apis.google_maps import GoogleMapsAPI
from ...modules.detection import detect_lots_and_save
from ...modules.pixel_to_geo import pixel_to_latlon
from ...database.mongodb import MongoDB
from google.cloud import storage


async def detect_lot_service(
    latitude: float,
    longitude: float,
    zoom: int = 20,
    confidence: float = 0.62,
    year: str = None,
) -> Dict[str, Any]:
    """
    Service that detects a lot and returns its polygon points.
    """
    try:
        # Initialize services
        google_maps = GoogleMapsAPI()
        mongo_db = MongoDB()
        storage_client = storage.Client()
        bucket = storage_client.bucket("images_from_have_allotment")

        # Load environment variables
        model_path = os.getenv("YOLO_MODEL_PATH")
        if not model_path:
            raise ValueError("YOLO_MODEL_PATH not found")

        # Prepare initial document structure
        current_year = str(datetime.now().year)
        current_month = datetime.now().strftime("%m")
        current_datetime = datetime.utcnow()

        initial_data = {
            "coordinates": {"lat": latitude, "lon": longitude},
            "image_info": {
                "zoom": zoom,
                "scale": 2,
                "year": year or current_year,
                "month": current_month,
                "captured_at": current_datetime,
            },
            "created_at": current_datetime,
            "updated_at": current_datetime,
            "detection_index": 0,
            "detection_id": None,
        }

        # Insert initial document
        doc_id = await mongo_db.insert_detection(initial_data)

        # Get satellite image and save to GCS
        image_content = google_maps.get_satellite_image(
            lat=latitude,
            lng=longitude,
            zoom=zoom,
            size="640x640",
            scale=2,
        )

        # Save image to GCS and update image_info
        blob_path = f"satellite_images/{doc_id}.jpg"
        blob = bucket.blob(blob_path)

        with tempfile.NamedTemporaryFile(
            suffix=".jpg", delete=False
        ) as temp_file:
            temp_file.write(image_content)
            temp_file.flush()
            blob.upload_from_filename(temp_file.name)
            os.unlink(temp_file.name)

        # Update image URL in MongoDB
        satellite_image_url = f"https://storage.cloud.google.com/images_from_have_allotment/{blob_path}"

        image_info_update = {
            "image_info.url": satellite_image_url,
            "image_info.path": blob_path,
            "updated_at": datetime.utcnow(),
        }

        await mongo_db.update_detection(doc_id, image_info_update)

        # Process detection
        items_list = [
            {
                "image_content": image_content,
                "latitude": latitude,
                "longitude": longitude,
                "dimensions": "1280x1280",
                "zoom": zoom,
                "year": initial_data["image_info"]["year"],
            }
        ]

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

        # Update detection results
        detection = processed_docs[0]
        detection_result = {
            "detection_result": {
                "center": {
                    "pixel": {
                        "x": detection["original_detection"]["polygon"][0][0],
                        "y": detection["original_detection"]["polygon"][0][1],
                    },
                    "geo": {"lat": latitude, "lon": longitude},
                },
                "confidence": detection["confidence"],
                "mask_points": detection["original_detection"]["polygon"],
                "processed_at": datetime.utcnow(),
            }
        }

        if "adjusted_detection" in detection:
            detection_result["detection_result"]["adjusted_mask"] = {
                "points": detection["adjusted_detection"]["polygon"],
                "geo_points": [],  # Will be filled with converted coordinates
                "center": {"geo": {"lat": latitude, "lon": longitude}},
                "adjustment_type": detection["adjusted_detection"][
                    "adjustment_method"
                ],
                "adjusted_at": datetime.utcnow(),
            }

        await mongo_db.update_detection(doc_id, detection_result)

        return {
            "id": doc_id,
            "status": "success",
            "points": (
                detection_result["detection_result"]["adjusted_mask"]["points"]
                if "adjusted_mask" in detection_result["detection_result"]
                else detection_result["detection_result"]["mask_points"]
            ),
        }

    except Exception as e:
        return {
            "id": str(ObjectId()),
            "status": "error",
            "error": str(e),
            "points": [],
        }
