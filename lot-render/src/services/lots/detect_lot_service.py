from pathlib import Path
import os
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd

from ...apis.google_maps import GoogleMapsAPI
from ...modules.detection import detect_lots_and_save
from ...modules.pixel_to_geo import pixel_to_latlon


async def detect_lot_service(
    latitude: float,
    longitude: float,
    zoom: int = 20,
    confidence: float = 0.62,
) -> Dict[str, Any]:
    """
    Service that detects a lot and returns its polygon points.
    """
    try:
        # Initialize Google Maps API
        google_maps = GoogleMapsAPI()

        # Load environment variables
        model_path = os.getenv("YOLO_MODEL_PATH")
        if not model_path:
            raise ValueError("YOLO_MODEL_PATH not found")

        # Create unique ID for the lot
        lat_str = f"{latitude:.14f}"
        lng_str = f"{longitude:.14f}"
        coord_id = f"{lat_str}_{lng_str}"
        lot_id = f"test_{coord_id}"

        # Set up base directory for generated files
        base_dir = Path("/app/generated")
        base_dir.mkdir(exist_ok=True)

        # Create a unique directory for this analysis using timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        analysis_dir = base_dir / f"analysis_{timestamp}_{coord_id}"
        analysis_dir.mkdir(exist_ok=True)
        print(f"\nDetection - Created analysis directory: {analysis_dir}")

        # Set up directories
        output_path = analysis_dir / f"satellite_{coord_id}.jpg"
        detection_dir = analysis_dir / "lots_detection"
        json_dir = detection_dir / "json"
        masks_dir = detection_dir / "masks"
        results_dir = detection_dir / "detections"

        # Create all directories
        for directory in [json_dir, masks_dir, results_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Detection - Created directory: {directory}")

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

        # Save image
        print(f"Detection - Saving satellite image to: {output_path}")
        with open(output_path, "wb") as f:
            f.write(image_content)

        # Prepare items list for detection
        items_list = [
            {
                "image_path": str(output_path),
                "object_id": lot_id,
                "latitude": latitude,
                "longitude": longitude,
                "dimensions": "1280x1280",  # 640x640 with scale=2
                "zoom": zoom,
                "street_name": "Test Street",
                "google_place_id": "test_place",
                "year": datetime.now().year,
            }
        ]

        # Execute lot detection
        print(f"Detection - Starting lot detection with model: {model_path}")
        processed_docs = detect_lots_and_save(
            model_path=model_path,
            items_list=items_list,
            output_dir=str(detection_dir),
            adjust_mask=True,
        )

        if not processed_docs:
            return {
                "id": lot_id,
                "status": "error",
                "error": "No lots detected in the image",
                "points": [],
            }

        # Get the detected polygon points
        doc = processed_docs[0]
        detection = doc.get("adjusted_detection", {}) or doc.get(
            "original_detection", {}
        )
        if not detection:
            return {
                "id": lot_id,
                "status": "error",
                "error": "No detection data found",
                "points": [],
            }

        # Convert polygon points to lat/lon coordinates
        polygon = detection.get("polygon", [])
        width = height = 1280  # 640x640 with scale=2

        points = []
        for x, y in polygon:
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
            points.append({"lat": lat, "lon": lon})

        return {
            "id": lot_id,
            "status": "success",
            "points": points,
        }

    except Exception as e:
        return {
            "id": f"error_{datetime.now().timestamp()}",
            "status": "error",
            "error": str(e),
            "points": [],
        }
