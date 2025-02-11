from pathlib import Path
import os
import json
from datetime import datetime
from typing import Dict, Any, List
import numpy as np

from ...apis.google_maps import GoogleMapsAPI
from ...modules.area import process_lot_areas
from ...modules.site_images import process_lot_images_for_site
from ...modules.colors import process_lot_colors
from ...modules.elevation import process_lots_elevation
from ...modules.utm import process_lots_utm_coordinates
from ...modules.process_cardinal_points import process_cardinal_points
from ...modules.process_front_points import process_front_points
from ...modules.generate_csv import process_lots_csv
from ...modules.generate_glb import process_lots_glb
from ...modules.classify_lots_slope import process_lots_slope


async def process_lot_service(
    points: List[Dict[str, float]],
    latitude: float,
    longitude: float,
    zoom: int = 20,
    confidence: float = 0.62,
) -> Dict[str, Any]:
    """
    Service that processes a lot based on its polygon points.
    """
    try:
        # Initialize Google Maps API
        google_maps = GoogleMapsAPI()

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
        print(f"\nProcessing - Created analysis directory: {analysis_dir}")

        # Set up directories
        output_path = analysis_dir / f"satellite_{coord_id}.jpg"
        detection_dir = analysis_dir / "lots_detection"
        json_dir = detection_dir / "json"
        processed_dir = detection_dir / "processed"
        site_images_dir = detection_dir / "site_images"
        colors_dir = detection_dir / "colors"
        elevations_dir = detection_dir / "elevations"
        utm_dir = detection_dir / "utm"

        # Create all directories
        for directory in [
            json_dir,
            processed_dir,
            site_images_dir,
            colors_dir,
            elevations_dir,
            utm_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Processing - Created directory: {directory}")

        # Get satellite image for visualization
        print(
            f"Processing - Getting satellite image for coordinates: {latitude}, {longitude}"
        )
        image_content = google_maps.get_satellite_image(
            lat=latitude,
            lng=longitude,
            zoom=zoom,
            size="640x640",
            scale=2,
        )

        # Save image
        print(f"Processing - Saving satellite image to: {output_path}")
        with open(output_path, "wb") as f:
            f.write(image_content)

        # Create initial document with polygon points
        width = height = 1280  # 640x640 with scale=2
        polygon_points = []
        for point in points:
            lat, lon = point["lat"], point["lon"]
            # Convert lat/lon back to normalized coordinates
            x, y = lat_lon_to_pixel_normalized(
                lat=lat,
                lon=lon,
                center_lat=latitude,
                center_lon=longitude,
                zoom=zoom,
                scale=2,
                image_width=width,
                image_height=height,
            )
            polygon_points.append([x, y])

        # Create the document with the polygon
        doc = {
            "id": lot_id,
            "original_detection": {
                "polygon": polygon_points,
                "confidence": confidence,
                "annotation": points_to_yolov8_annotation(polygon_points),
            },
            "metadata": {
                "latitude": latitude,
                "longitude": longitude,
                "dimensions": f"{width}x{height}",
                "zoom": zoom,
                "street_name": "Test Street",
                "google_place_id": "test_place",
                "year": datetime.now().year,
                "original_image": str(output_path),
            },
        }

        # Save initial document
        json_path = json_dir / f"{lot_id}.json"
        with open(json_path, "w") as f:
            json.dump(doc, f, indent=2)

        # Process lot areas
        print("Processing - Processing lot areas")
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

        print("\nIniciando processamento de pontos cardeais...")
        cardinal_dir = os.path.join(detection_dir, "cardinal")

        cardinal_processed = process_cardinal_points(
            input_dir=utm_dir,
            output_dir=cardinal_dir,
            distance_meters=5,
            confidence=confidence,
        )

        # Process front points
        front_dir = os.path.join(detection_dir, "front")
        maps_dir = Path(detection_dir) / "maps"
        front_processed = process_front_points(
            input_dir=cardinal_dir,
            output_dir=front_dir,
            google_maps_api_key=google_maps.api_key,
            create_maps=False,
            confidence=confidence,
            maps_output_dir=maps_dir,
        )

        # Process CSV
        print("\nIniciando processamento de CSVs...")
        csv_dir = os.path.join(detection_dir, "csv")

        csv_processed = process_lots_csv(
            input_dir=front_dir,
            output_dir=csv_dir,
            confidence=confidence,
        )

        # Process GLB
        print("\nIniciando processamento de GLBs...")
        glb_dir = os.path.join(detection_dir, "glb")

        glb_processed = process_lots_glb(
            input_dir=csv_dir,
            output_dir=glb_dir,
            confidence=confidence,
        )

        # Process slope
        slope_dir = os.path.join(detection_dir, "slope")
        db_path = os.path.join(detection_dir, "slope_cache.db")

        slope_processed = process_lots_slope(
            input_dir=glb_dir,
            output_dir=slope_dir,
            db_path=db_path,
            confidence=confidence,
        )

        # Combine all results
        result = doc
        result.update(
            {
                "area_stats": area_stats,
                "site_images": (site_processed[0] if site_processed else None),
                "colors": colors_processed[0] if colors_processed else None,
                "elevations": (
                    elevations_processed[0] if elevations_processed else None
                ),
                "utm": utm_processed[0] if utm_processed else None,
            }
        )

        return {
            "id": lot_id,
            "status": "success",
            "results": result,
        }

    except Exception as e:
        return {
            "id": f"error_{datetime.now().timestamp()}",
            "status": "error",
            "error": str(e),
        }


def lat_lon_to_pixel_normalized(
    lat: float,
    lon: float,
    center_lat: float,
    center_lon: float,
    zoom: int,
    scale: int,
    image_width: int,
    image_height: int,
) -> tuple:
    """Convert lat/lon to normalized pixel coordinates (0-1)."""
    # First convert lat/lon to world coordinates
    sin_y = min(max(np.sin(lat * np.pi / 180), -0.9999), 0.9999)
    world_x = 256 * (lon + 180) / 360
    world_y = 256 * (0.5 - np.log((1 + sin_y) / (1 - sin_y)) / (4 * np.pi))

    # Convert center lat/lon to world coordinates
    sin_y_center = min(max(np.sin(center_lat * np.pi / 180), -0.9999), 0.9999)
    center_world_x = 256 * (center_lon + 180) / 360
    center_world_y = 256 * (
        0.5 - np.log((1 + sin_y_center) / (1 - sin_y_center)) / (4 * np.pi)
    )

    # Calculate pixel coordinates
    scale_factor = 2**zoom
    pixel_x = (world_x - center_world_x) * scale_factor + image_width / (
        2 * scale
    )
    pixel_y = (world_y - center_world_y) * scale_factor + image_height / (
        2 * scale
    )

    # Normalize coordinates
    x_normalized = pixel_x / image_width
    y_normalized = pixel_y / image_height

    return x_normalized, y_normalized


def points_to_yolov8_annotation(points: List[List[float]]) -> str:
    """Convert normalized points to YOLOv8 annotation string."""
    # Start with class 0 (assuming single class)
    annotation = ["0"]

    # Add coordinates
    for x, y in points:
        annotation.extend([f"{x:.8f}", f"{y:.8f}"])

    return " ".join(annotation)
