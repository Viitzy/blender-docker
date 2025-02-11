from pathlib import Path
import os
from datetime import datetime
from typing import Dict, Any
import pandas as pd

from ...apis.google_maps import GoogleMapsAPI
from ...modules.detection import detect_lots_and_save
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


async def analyze_lot_service(
    latitude: float,
    longitude: float,
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

        # Set up base directory for generated files
        base_dir = Path("/app/generated")
        base_dir.mkdir(exist_ok=True)

        # Create a unique directory for this analysis using timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        analysis_dir = base_dir / f"analysis_{timestamp}_{coord_id}"
        analysis_dir.mkdir(exist_ok=True)
        print(f"\nAnalysis - Created analysis directory: {analysis_dir}")

        # Set up directories
        output_path = analysis_dir / f"satellite_{coord_id}.jpg"
        detection_dir = analysis_dir / "lots_detection"
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
            print(f"Analysis - Created directory: {directory}")

        # Get satellite image
        print(
            f"Analysis - Getting satellite image for coordinates: {latitude}, {longitude}"
        )
        image_content = google_maps.get_satellite_image(
            lat=latitude,
            lng=longitude,
            zoom=20,
            size="640x640",
            scale=2,
        )

        # Save image
        print(f"Analysis - Saving satellite image to: {output_path}")
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
                "zoom": 20,
                "street_name": "Test Street",
                "google_place_id": "test_place",
                "year": datetime.now().year,
            }
        ]

        # Execute lot detection
        print(f"Analysis - Starting lot detection with model: {model_path}")
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

        # Move satellite image to correct location TALVEZ MUDAR
        satellite_images_dir = detection_dir / "satellite_images"
        satellite_images_dir.mkdir(exist_ok=True)
        new_image_path = satellite_images_dir / output_path.name
        print(
            f"Analysis - Moving satellite image from {output_path} to {new_image_path}"
        )
        os.rename(output_path, new_image_path)

        # Process lot areas
        print("Analysis - Processing lot areas")
        area_stats = process_lot_areas(
            input_dir=str(json_dir),
            output_dir=str(processed_dir),
            confidence_threshold=0.62,
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
            confidence=0.62,
        )

        # Process colors
        colors_processed = process_lot_colors(
            input_dir=str(processed_dir),
            output_dir=str(colors_dir),
            max_points=130,
            dark_threshold=70,
            bright_threshold=215,
            confidence=0.62,
        )

        # Process elevations
        elevations_processed = process_lots_elevation(
            input_dir=str(colors_dir),
            output_dir=str(elevations_dir),
            api_key=google_maps.api_key,
            db_path=str(detection_dir / "elevation_cache.db"),
            confidence=0.62,
        )

        # Process UTM coordinates
        utm_processed = process_lots_utm_coordinates(
            input_dir=str(elevations_dir),
            output_dir=str(utm_dir),
            confidence=0.62,
        )

        print("\nIniciando processamento de pontos cardeais...")
        cardinal_dir = os.path.join(detection_dir, "cardinal")

        cardinal_processed = process_cardinal_points(
            input_dir=utm_dir,
            output_dir=cardinal_dir,
            distance_meters=5,
            confidence=0.62,
        )

        # TALVEZ OPCIONAL
        if cardinal_processed:
            print("\nResultados do processamento de pontos cardeais:")
            for result in cardinal_processed:
                print(f"\nID: {result['id']}")
                cardinal_points = result["point_colors"].get(
                    "cardinal_points", {}
                )
                if cardinal_points:
                    print("Pontos cardeais:")
                    for direction, point in cardinal_points.items():
                        print(
                            f"  {direction}: ({point[0]:.6f}, {point[1]:.6f})"
                        )

        front_dir = os.path.join(detection_dir, "front")
        maps_dir = Path(detection_dir) / "maps"
        front_processed = process_front_points(
            input_dir=cardinal_dir,
            output_dir=front_dir,
            google_maps_api_key=google_maps.api_key,
            create_maps=False,
            confidence=0.62,
            maps_output_dir=maps_dir,
        )

        # TALVEZ OPCIONAL
        if front_processed:
            print("\nResultados do processamento de pontos frontais:")
            for result in front_processed:
                print(f"\nID: {result['id']}")
                front_points = result["point_colors"].get("front_points", [])
                if front_points:
                    print(f"Pontos frontais encontrados: {len(front_points)}")
                    street_info = result["point_colors"].get("street_info")
                    if street_info:
                        print(
                            f"Rua mais próxima: {street_info.get('name', 'N/A')}"
                        )

        print("\nIniciando processamento de CSVs...")
        csv_dir = os.path.join(detection_dir, "csv")

        csv_processed = process_lots_csv(
            input_dir=front_dir,
            output_dir=csv_dir,
            confidence=0.62,
        )

        # TALVEZ OPCIONAL
        if csv_processed:
            print("\nResultados do processamento de CSVs:")
            for result in csv_processed:
                print(f"\nID: {result['id']}")
                csv_path = os.path.join(csv_dir, f"{result['id']}.csv")
                if os.path.exists(csv_path):
                    df = pd.read_csv(csv_path)
                    print(f"Total de pontos no CSV: {len(df)}")
                    print(f"Colunas: {', '.join(df.columns)}")

        print("\nIniciando processamento de GLBs...")
        glb_dir = os.path.join(detection_dir, "glb")

        glb_processed = process_lots_glb(
            input_dir=csv_dir,  # Usa o diretório de CSVs como entrada
            output_dir=glb_dir,
            confidence=0.62,
        )

        # TALVEZ OPCIONAL
        if glb_processed:
            print("\nResultados do processamento de GLBs:")
            for result in glb_processed:
                print(f"\nID: {result['id']}")
                glb_path = result.get("glb_file")
                if glb_path and os.path.exists(glb_path):
                    print(f"GLB gerado: {glb_path}")
                    print(f"Tamanho: {os.path.getsize(glb_path)} bytes")

        slope_dir = os.path.join(detection_dir, "slope")
        db_path = os.path.join(detection_dir, "slope_cache.db")

        slope_processed = process_lots_slope(
            input_dir=glb_dir,  # Usa o diretório de GLBs como entrada
            output_dir=slope_dir,
            db_path=db_path,
            confidence=0.62,
        )

        # TALVEZ OPCIONAL
        if slope_processed:
            print("\nResultados do processamento de inclinação:")
            for result in slope_processed:
                print(f"\nID: {result['id']}")
                slope_info = result.get("slope_info", {})
                if slope_info:
                    print(f"Inclinação: {slope_info['slope_percent']:.2f}%")
                    print(f"Classificação: {slope_info['classification']}")
                    print(f"Altitude mínima: {slope_info['min_altitude']:.2f}m")
                    print(f"Altitude máxima: {slope_info['max_altitude']:.2f}m")
                    print(f"Amplitude: {slope_info['altitude_range']:.2f}m")

        # Combine all results
        result = processed_docs[0]
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

        return {"id": lot_id, "status": "success", "results": result}

    except Exception as e:
        return {
            "id": f"error_{datetime.now().timestamp()}",
            "status": "error",
            "error": str(e),
        }
