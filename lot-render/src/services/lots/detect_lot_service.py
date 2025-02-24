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
from ...modules.area import calculate_geo_area
from google.cloud import storage


def points_to_yolov8_annotation(points: List[List[float]]) -> str:
    """Convert normalized points to YOLOv8 annotation string."""
    # Start with class 0 (assuming single class)
    annotation = ["0"]

    # Add coordinates
    for x, y in points:
        annotation.extend([f"{x:.8f}", f"{y:.8f}"])

    return " ".join(annotation)


async def detect_lot_service(
    latitude: float,
    longitude: float,
    zoom: int = 20,
    object_id: str = None,
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
                "object_id": doc_id,
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
                "status": "error",
                "points": [],
                "error": "No lots detected in the image",
                "doc_id": None,
            }

        # Update detection results
        detection = processed_docs[0]

        # Convert normalized pixel coordinates to lat/lon points for original mask
        original_points = []
        print(
            f"Original detection: {detection['original_detection']['polygon']}"
        )
        for x, y in detection["original_detection"]["polygon"]:
            lat, lon = pixel_to_latlon(
                pixel_x=x * 1280,
                pixel_y=y * 1280,
                center_lat=latitude,
                center_lon=longitude,
                zoom=zoom,
                scale=2,
                image_width=1280,
                image_height=1280,
            )
            original_points.append([lat, lon])

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
                "geo_points": original_points,
                "yolov8_annotation": points_to_yolov8_annotation(
                    detection["original_detection"]["polygon"]
                ),
                "processed_at": datetime.utcnow(),
            }
        }

        if "adjusted_detection" in detection:
            # Convert normalized pixel coordinates to lat/lon points for adjusted mask
            adjusted_geo_points = []
            for x, y in detection["adjusted_detection"]["polygon"]:
                lat, lon = pixel_to_latlon(
                    pixel_x=x * 1280,
                    pixel_y=y * 1280,
                    center_lat=latitude,
                    center_lon=longitude,
                    zoom=zoom,
                    scale=2,
                    image_width=1280,
                    image_height=1280,
                )
                adjusted_geo_points.append([lat, lon])

            detection_result["detection_result"]["adjusted_mask"] = {
                "points": detection["adjusted_detection"]["polygon"],
                "geo_points": adjusted_geo_points,
                "center": {"geo": {"lat": latitude, "lon": longitude}},
                "adjustment_type": detection["adjusted_detection"][
                    "adjustment_method"
                ],
                "yolov8_annotation": points_to_yolov8_annotation(
                    detection["adjusted_detection"]["polygon"]
                ),
                "adjusted_at": datetime.utcnow(),
            }

        await mongo_db.update_detection(doc_id, detection_result)

        # Get points from detection result
        points_array = (
            detection_result["detection_result"]["adjusted_mask"]["points"]
            if "adjusted_mask" in detection_result["detection_result"]
            else detection_result["detection_result"]["mask_points"]
        )

        # Convert normalized pixel coordinates to lat/lon points
        points = []
        for x, y in points_array:
            lat, lon = pixel_to_latlon(
                pixel_x=x
                * 1280,  # Convert normalized coordinates back to pixels
                pixel_y=y * 1280,
                center_lat=latitude,
                center_lon=longitude,
                zoom=zoom,
                scale=2,
                image_width=1280,
                image_height=1280,
            )
            points.append({"lat": lat, "lon": lon})

        # Calculate area
        points_lat_lon = [[p["lat"], p["lon"]] for p in points]
        area_m2 = calculate_geo_area(points_lat_lon)

        # Initialize lot_details structure
        lot_details = {
            "area_m2": area_m2,
            "point_colors": {
                "points": [],
                "colors": [],
                "colors_adjusted": [],
                "points_lat_lon": points_lat_lon,
                "points_utm": [],
                "cardinal_points": {},
                "front_points": [],
                "front_points_lat_lon": [],
                "street_points": [],
                "street_info": {},
            },
            "elevations": [],
            "mask_elevation": [],
            "mask_utm": [],
        }

        # Update MongoDB with lot_details
        await mongo_db.update_detection(doc_id, {"lot_details": lot_details})

        return {"status": "success", "points": points, "doc_id": str(doc_id)}

    except Exception as e:
        return {
            "status": "error",
            "points": [],
            "error": str(e),
            "doc_id": None,
        }
