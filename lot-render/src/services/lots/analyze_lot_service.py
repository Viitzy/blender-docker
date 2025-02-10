from pathlib import Path
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import tempfile

from ...apis.google_maps import GoogleMapsAPI
from ...modules.detection import detect_lots_and_save
from ...modules.area import process_lot_areas
from ...modules.site_images import process_lot_images_for_site
from ...modules.colors import process_lot_colors
from ...modules.elevation import process_lots_elevation
from ...modules.utm import process_lots_utm_coordinates


async def analyze_lot_service(
    latitude: float,
    longitude: float,
    zoom: int,
    confidence: float = 0.62,
) -> Dict[str, Any]:
    """
    Complete lot analysis service that processes:
    1. Satellite image acquisition
    2. Lot detection
    3. Area calculation
    4. Site image processing
    5. Color processing
    6. Elevation processing
    7. UTM coordinate conversion
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

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            print(
                f"\nAnalysis - Created temporary directory: {temp_dir}"
            )  # Debug print

            # Set up directories
            output_path = temp_dir / f"satellite_{coord_id}.jpg"
            detection_dir = temp_dir / "lots_detection"
            json_dir = detection_dir / "json"
            masks_dir = detection_dir / "masks"
            results_dir = detection_dir / "detections"
            processed_dir = detection_dir / "processed"
            site_images_dir = detection_dir / "site_images"
            colors_dir = detection_dir / "colors"
            elevations_dir = detection_dir / "elevations"
            utm_dir = detection_dir / "utm"

            # Create all directories
            for directory in [
                json_dir,
                masks_dir,
                results_dir,
                processed_dir,
                site_images_dir,
                colors_dir,
                elevations_dir,
                utm_dir,
            ]:
                directory.mkdir(parents=True, exist_ok=True)
                print(
                    f"Analysis - Created directory: {directory}"
                )  # Debug print

            # Get satellite image
            print(
                f"Analysis - Getting satellite image for coordinates: {latitude}, {longitude}"
            )  # Debug print
            image_content = google_maps.get_satellite_image(
                lat=latitude,
                lng=longitude,
                zoom=zoom,
                size="640x640",
                scale=2,
            )

            # Save image
            print(
                f"Analysis - Saving satellite image to: {output_path}"
            )  # Debug print
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
            print(
                f"Analysis - Starting lot detection with model: {model_path}"
            )  # Debug print
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
                }

            # Move satellite image to correct location
            satellite_images_dir = detection_dir / "satellite_images"
            satellite_images_dir.mkdir(exist_ok=True)
            new_image_path = satellite_images_dir / output_path.name
            print(
                f"Analysis - Moving satellite image from {output_path} to {new_image_path}"
            )  # Debug print
            os.rename(output_path, new_image_path)

            # Process lot areas
            print("Analysis - Processing lot areas")  # Debug print
            area_stats = process_lot_areas(
                input_dir=str(json_dir),
                output_dir=str(processed_dir),
                confidence_threshold=confidence,
            )

            # Process site images
            watermark_path = (
                Path(__file__).parent.parent.parent.parent
                / "assets"
                / "watermark.png"
            )
            site_processed = process_lot_images_for_site(
                input_dir=str(processed_dir),
                output_dir=str(site_images_dir),
                hex_color="#e8f34e",
                watermark_path=str(watermark_path),
                confidence=confidence,
            )

            # Process colors
            colors_processed = process_lot_colors(
                input_dir=str(processed_dir),
                output_dir=str(colors_dir),
                max_points=130,
                dark_threshold=70,
                bright_threshold=215,
                confidence=confidence,
            )

            # Process elevations
            elevations_processed = process_lots_elevation(
                input_dir=str(colors_dir),
                output_dir=str(elevations_dir),
                api_key=google_maps.api_key,
                db_path=str(detection_dir / "elevation_cache.db"),
                confidence=confidence,
            )

            # Process UTM coordinates
            utm_processed = process_lots_utm_coordinates(
                input_dir=str(elevations_dir),
                output_dir=str(utm_dir),
                confidence=confidence,
            )

            # Combine all results
            result = processed_docs[0]
            result.update(
                {
                    "area_stats": area_stats,
                    "site_images": (
                        site_processed[0] if site_processed else None
                    ),
                    "colors": colors_processed[0] if colors_processed else None,
                    "elevations": (
                        elevations_processed[0]
                        if elevations_processed
                        else None
                    ),
                    "utm": utm_processed[0] if utm_processed else None,
                }
            )

            return {"id": lot_id, "status": "success", "results": result}

    except Exception as e:
        return {
            "id": f"error_{datetime.now().timestamp()}",
            "status": "error",
            "error": str(e),
        }
