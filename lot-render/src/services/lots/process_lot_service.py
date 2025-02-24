from pathlib import Path
import os
import json
from datetime import datetime
from typing import Dict, Any, List
import numpy as np
from bson import ObjectId
import tempfile
from google.cloud import storage
from geopy.distance import geodesic

from ...apis.google_maps import GoogleMapsAPI
from ...modules.colors import process_lot_colors
from ...modules.elevation import process_lots_elevation
from ...modules.utm import process_lots_utm_coordinates
from ...modules.process_cardinal_points import process_cardinal_points
from ...modules.process_front_points import process_front_points
from ...modules.generate_csv import process_lots_csv
from ...modules.generate_glb import process_lots_glb
from ...modules.classify_lots_slope import process_lots_slope
from ...database.mongodb import MongoDB
from ...modules.site_images import process_lot_images_for_site
from ...modules.detection import (
    detect_lots_and_save,
    load_yolo_model,
    get_best_segmentation,
)
from ...modules.pixel_to_geo import pixel_to_latlon, lat_lon_to_pixel_normalized
from ...modules.process_address import process_lot_address


def convert_objectid_to_string(obj):
    """Convert ObjectId to string in a document recursively."""
    if isinstance(obj, dict):
        return {
            key: convert_objectid_to_string(value) for key, value in obj.items()
        }
    elif isinstance(obj, list):
        return [convert_objectid_to_string(item) for item in obj]
    elif isinstance(obj, ObjectId):
        return str(obj)
    return obj


def ai_validation(
    model_result: dict,
    param_center: tuple,
    zoom: int = 20,
) -> tuple[bool, str]:
    """
    Validates AI model results and center point distances.

    Args:
        model_result: Dictionary with model detection results
        param_center: Tuple of (lat, lon) for the center of polygon received as parameter
        zoom: Zoom level used for the satellite image

    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    print("\nValidando resultados da IA...")

    # Check confidence threshold
    confidence = model_result.get("confidence", 0)
    print(f"Verificando confiança: {confidence:.3f}")
    if confidence < 0.7:
        return (
            False,
            f"Confiança muito baixa: {confidence:.3f} < 0.7",
        )
    print("✓ Confiança passou no limite mínimo")

    # Calculate center of AI detected polygon
    ai_points = model_result["original_detection"]["polygon"]
    if not ai_points:
        return (False, "Polígono da IA está vazio")

    # Get parameters from param_center
    param_center_lat, param_center_lon = param_center

    # Primeiro converte cada ponto do polígono para lat/lon
    ai_points_latlon = []
    for x_norm, y_norm in ai_points:
        lat, lon = pixel_to_latlon(
            pixel_x=x_norm * 1280,  # Convert from normalized (0-1) to pixels
            pixel_y=y_norm * 1280,
            center_lat=param_center_lat,
            center_lon=param_center_lon,
            zoom=zoom,
            scale=2,
            image_width=1280,
            image_height=1280,
        )
        ai_points_latlon.append((lat, lon))

    # Calcula o centro como média das coordenadas lat/lon
    ai_center_lat = sum(p[0] for p in ai_points_latlon) / len(ai_points_latlon)
    ai_center_lon = sum(p[1] for p in ai_points_latlon) / len(ai_points_latlon)

    print(f"Centro do polígono por parâmetro: {param_center}")
    print(
        f"Centro do polígono detectado: ({ai_center_lat:.6f}, {ai_center_lon:.6f})"
    )

    # Check distance between parameter center and AI detected center
    param_ai_distance = geodesic(
        param_center, (ai_center_lat, ai_center_lon)
    ).meters
    print(f"Distância entre centros: {param_ai_distance:.2f}m")

    if param_ai_distance > 45:
        return (
            False,
            f"Distância entre o centro do parâmetro e da detecção muito grande: {param_ai_distance:.2f}m > 45m",
        )
    print("✓ Distância entre centros dentro do limite")

    return True, ""


async def process_lot_service(
    doc_id: str,
    points: List[Dict[str, float]],
    zoom: int = 20,
    confidence: float = 0,
) -> Dict[str, Any]:
    """
    Service that processes a lot based on its polygon points.
    Uses fixed values:
    - zoom: 20
    - confidence: 0.62
    """
    try:
        google_maps = GoogleMapsAPI()
        # Get MongoDB connection string from environment
        mongo_connection_string = os.getenv("MONGO_CONNECTION_STRING")
        if not mongo_connection_string:
            return {
                "status": "error",
                "error": "MongoDB connection string not found in environment variables",
            }

        mongo_db = MongoDB()
        doc = await mongo_db.get_detection(doc_id)

        if not doc:
            return {
                "status": "error",
                "error": "Document not found",
            }

        # Fixed values
        zoom = 20

        # Check if points are different from the original ones
        original_points = None
        original_center = None
        if "detection_result" in doc:
            if "adjusted_mask" in doc["detection_result"]:
                original_points = doc["detection_result"]["adjusted_mask"][
                    "geo_points"
                ]
            else:
                original_points = doc["detection_result"]["geo_points"]

            if (
                "center" in doc["detection_result"]
                and "geo" in doc["detection_result"]["center"]
            ):
                center = doc["detection_result"]["center"]["geo"]
                original_center = (center["lat"], center["lon"])
            if "confidence" in doc["detection_result"]:
                confidence = doc["detection_result"]["confidence"]

        # Convert Point objects to [lat, lon] format
        new_points_lat_lon = [[point.lat, point.lon] for point in points]

        # If points are different, update satellite image and run detection
        if original_points and original_points != new_points_lat_lon:
            confidence = 1
            # Calculate center point for new points
            new_center_lat = sum(p.lat for p in points) / len(points)
            new_center_lon = sum(p.lon for p in points) / len(points)
            new_center = (new_center_lat, new_center_lon)

            # Get new satellite image
            image_content = google_maps.get_satellite_image(
                lat=new_center_lat,
                lng=new_center_lon,
                zoom=zoom,
                size="640x640",
                scale=2,
            )

            # Load YOLO model and run detection
            model_path = os.getenv("YOLO_MODEL_PATH")
            if not model_path:
                return {"status": "error", "error": "YOLO_MODEL_PATH not found"}

            model = load_yolo_model(model_path)

            # Create items list for detection
            items_list = [
                {
                    "image_content": image_content,
                    "object_id": doc_id,
                    "latitude": new_center_lat,
                    "longitude": new_center_lon,
                    "dimensions": "1280x1280",
                    "zoom": zoom,
                    "year": str(datetime.now().year),
                }
            ]
            # Run detection without mask adjustment
            print(f"\nExecutando detecção para o lote {doc_id}")
            print(f"Centro: lat={new_center_lat}, lon={new_center_lon}")

            processed_docs = detect_lots_and_save(
                model_path=model_path,
                items_list=items_list,
                adjust_mask=False,
            )

            # Get detection result and validate
            detection = None
            if processed_docs:
                detection = processed_docs[0]
                print("\nDetecção realizada com sucesso")
                print(f"Confiança: {detection.get('confidence', 'N/A')}")

                if (
                    "original_detection" in detection
                    and "polygon" in detection["original_detection"]
                ):
                    print("Polígono detectado pela IA")
                    # Validate AI results
                    is_valid, error_message = ai_validation(
                        model_result=detection,
                        param_center=new_center,
                        zoom=zoom,
                    )
                    is_valid = True
                    error_message = ""

                    if not is_valid:
                        return {"status": "error", "error": error_message}

                    print("✓ Validação da IA passou com sucesso")
                    print(f"  Confiança: {detection['confidence']:.3f}")
                else:
                    print("Detecção não contém polígono válido")
                    print("Continuando com os pontos fornecidos por parâmetro")
                    detection = None
            else:
                print("\nNenhuma detecção encontrada pelo modelo")
                print("Continuando com os pontos fornecidos por parâmetro")
                detection = None

            # Create detection result with provided parameters if no valid detection
            if not detection:
                return {
                    "status": "error",
                    "error": "Nenhuma detecção encontrada",
                }
            # Convert points to normalized pixel coordinates for mask_points
            normalized_points = []
            for point in points:
                x_norm, y_norm = lat_lon_to_pixel_normalized(
                    lat=point.lat,
                    lon=point.lon,
                    center_lat=new_center_lat,
                    center_lon=new_center_lon,
                    zoom=zoom,
                    scale=2,
                    image_width=1280,
                    image_height=1280,
                )
                normalized_points.append([x_norm, y_norm])

            # Move current detection_result to old_detection_result
            if "detection_result" in doc:
                update_data = {
                    "old_detection_result": doc["detection_result"],
                }
                await mongo_db.update_detection(doc_id, update_data)
                print("Detecção original movida para old_detection_result")

            # Create new detection result with provided points
            new_detection_result = {
                "center": {
                    "pixel": {
                        "x": normalized_points[0][0],
                        "y": normalized_points[0][1],
                    },
                    "geo": {
                        "lat": new_center_lat,
                        "lon": new_center_lon,
                    },
                },
                "confidence": confidence,
                "mask_points": normalized_points,
                "geo_points": new_points_lat_lon,
                "yolov8_annotation": points_to_yolov8_annotation(
                    normalized_points
                ),
                "processed_at": datetime.utcnow(),
                "adjusted_mask": {
                    "points": normalized_points,
                    "geo_points": new_points_lat_lon,
                    "center": {
                        "geo": {
                            "lat": new_center_lat,
                            "lon": new_center_lon,
                        }
                    },
                    "adjustment_type": "manual",
                    "adjusted_at": datetime.utcnow(),
                    "yolov8_annotation": points_to_yolov8_annotation(
                        normalized_points
                    ),
                },
            }

            # Update MongoDB with new detection result
            await mongo_db.update_detection(
                doc_id, {"detection_result": new_detection_result}
            )
            print("\nCriando novo detection_result com parâmetros fornecidos:")
            print(f"Confiança: {confidence}")
            print("Detecção anterior salva em old_detection_result")
            print("Nova detecção salva em detection_result com adjusted_mask")

            # Save image to GCS
            storage_client = storage.Client()
            bucket = storage_client.bucket("images_from_have_allotment")

            # Save current image path as old if it exists
            if "image_info" in doc and "path" in doc["image_info"]:
                old_blob_path = doc["image_info"]["path"]
                if old_blob_path:
                    # Move current image to old_ path
                    old_path = f"old_{old_blob_path}"
                    bucket.copy_blob(
                        bucket.blob(old_blob_path), bucket, old_path
                    )

            # Save new image
            blob_path = f"satellite_images/{doc_id}.jpg"
            blob = bucket.blob(blob_path)

            with tempfile.NamedTemporaryFile(
                suffix=".jpg", delete=False
            ) as temp_file:
                temp_file.write(image_content)
                temp_file.flush()
                blob.upload_from_filename(temp_file.name)
                os.unlink(temp_file.name)

            # Generate new image URL
            satellite_image_url = f"https://storage.cloud.google.com/images_from_have_allotment/{blob_path}"

            # Update image_info with new image data and timestamp
            image_info_update = {
                "image_info.url": satellite_image_url,
                "image_info.path": blob_path,
                "image_info.captured_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            await mongo_db.update_detection(doc_id, image_info_update)

        # Initialize lot_details structure if it doesn't exist
        if "lot_details" not in doc:
            lot_details = {
                "point_colors": {
                    "points": [],
                    "colors": [],
                    "colors_adjusted": [],
                    "points_lat_lon": new_points_lat_lon,
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
            # Update MongoDB with initial lot_details
            await mongo_db.update_detection(
                doc_id, {"lot_details": lot_details}
            )
        else:
            # Update points_lat_lon in existing lot_details
            await mongo_db.update_detection(
                doc_id,
                {"lot_details.point_colors.points_lat_lon": new_points_lat_lon},
            )

        # Process colors
        colors_processed = process_lot_colors(
            mongodb_uri=mongo_connection_string,
            max_points=130,
            dark_threshold=70,
            bright_threshold=215,
            confidence=confidence,
            doc_id=doc_id,
        )

        if colors_processed:
            point_colors = colors_processed[0].get("point_colors", {})
            await mongo_db.update_detection(
                doc_id,
                {"lot_details.point_colors": point_colors},
            )

        # Process site images
        site_images_processed = process_lot_images_for_site(
            mongodb_uri=mongo_connection_string,
            hex_color="#e8f34e",
            doc_id=doc_id,
            confidence=confidence,
        )

        if site_images_processed:
            site_image = site_images_processed[0]
            if site_image.get("site_image_url"):
                await mongo_db.update_detection(
                    doc_id,
                    {
                        "image_info.image_thumb_site": site_image[
                            "site_image_url"
                        ]
                    },
                )

        # Process elevations
        google_maps = GoogleMapsAPI()
        # Process address
        address_processed = process_lot_address(
            mongodb_uri=mongo_connection_string,
            google_maps_api_key=google_maps.api_key,
            doc_id=doc_id,
            confidence=confidence,
        )

        if address_processed:
            doc = address_processed[0]  # Get updated document
            print("address_processed")

        # Check if document already has elevations
        doc = await mongo_db.get_detection(doc_id)
        elevations_processed = process_lots_elevation(
            mongodb_uri=mongo_connection_string,
            api_key=google_maps.api_key,
            doc_id=doc_id,
            confidence=confidence,
        )

        if elevations_processed:
            doc = elevations_processed[0]  # Get updated document

        # Process UTM coordinates
        utm_processed = process_lots_utm_coordinates(
            mongodb_uri=mongo_connection_string,
            doc_id=doc_id,
            confidence=confidence,
        )

        if utm_processed:
            doc = utm_processed[0]  # Get updated document
            print("utm_processed")

        # Process cardinal points
        cardinal_processed = process_cardinal_points(
            mongodb_uri=mongo_connection_string,
            distance_meters=5,
            doc_id=doc_id,
            confidence=confidence,
        )

        if cardinal_processed:
            doc = cardinal_processed[0]  # Get updated document
            print("cardinal_points_processed")

            # Process front points
            front_processed = process_front_points(
                mongodb_uri=mongo_connection_string,
                google_maps_api_key=google_maps.api_key,
                create_maps=False,
                doc_id=doc_id,
                confidence=confidence,
            )

            if front_processed and len(front_processed) > 0:
                # Get the processed document
                processed_doc = front_processed[0]

                # Extract front points and street information
                front_points = (
                    processed_doc.get("lot_details", {})
                    .get("point_colors", {})
                    .get("front_points", [])
                )

                # Convert front points to front_points_lat_lon format
                front_points_lat_lon = [
                    {"lat": point["lat"], "lng": point["lng"]}
                    for point in front_points
                ]

                # Get street points and info
                street_points = (
                    processed_doc.get("lot_details", {})
                    .get("point_colors", {})
                    .get("street_points", [])
                )
                street_info = (
                    processed_doc.get("lot_details", {})
                    .get("point_colors", {})
                    .get("street_info", {})
                )

                # Update MongoDB with all front and street information
                update_data = {
                    "lot_details.point_colors.front_points": front_points,
                    "lot_details.point_colors.front_points_lat_lon": front_points_lat_lon,
                    "lot_details.point_colors.street_points": street_points,
                    "lot_details.point_colors.street_info": street_info,
                }

                await mongo_db.update_detection(doc_id, update_data)
                print(
                    "\n✓ Front points and street information updated successfully"
                )

                # Process CSV
                csv_processed = process_lots_csv(
                    mongodb_uri=mongo_connection_string,
                    bucket_name="csv_from_have_allotment",
                    year=str(datetime.now().year),
                    doc_id=doc_id,
                    confidence=confidence,
                )

                if csv_processed and len(csv_processed) > 0:
                    # CSV URL is already updated in MongoDB by process_lots_csv
                    print("CSV processado e salvo com sucesso")
                    doc = csv_processed[0]  # Get updated document

                # Process GLB (only if CSV was processed)
                if doc.get("csv_elevation_colors"):
                    glb_processed = process_lots_glb(
                        mongodb_uri=mongo_connection_string,
                        bucket_name="images_from_have_allotment",
                        bucket_name_csv="csv_from_have_allotment",
                        doc_id=doc_id,
                        confidence=confidence,
                    )

                    if glb_processed and len(glb_processed) > 0:
                        print("GLB processado e salvo com sucesso")
                        doc = glb_processed[0]  # Get updated document

                # Process slope
                slope_processed = process_lots_slope(
                    mongodb_uri=mongo_connection_string,
                    year=str(datetime.now().year),
                    doc_id=doc_id,
                    confidence=confidence,
                )

                if slope_processed:
                    doc = slope_processed[0]  # Get updated document
                    print("Slope processado e salvo com sucesso")

        # Get final document
        final_doc = await mongo_db.get_detection(doc_id)

        # Return success response with document ID
        return {"status": "success", "doc_id": str(doc_id)}

    except Exception as e:
        return {"status": "error", "error": str(e)}


# def lat_lon_to_pixel_normalized(
#     lat: float,
#     lon: float,
#     center_lat: float,
#     center_lon: float,
#     zoom: int,
#     scale: int,
#     image_width: int,
#     image_height: int,
# ) -> tuple:
#     """Convert lat/lon to normalized pixel coordinates (0-1)."""
#     # First convert lat/lon to world coordinates
#     sin_y = min(max(np.sin(lat * np.pi / 180), -0.9999), 0.9999)
#     world_x = 256 * (lon + 180) / 360
#     world_y = 256 * (0.5 - np.log((1 + sin_y) / (1 - sin_y)) / (4 * np.pi))

#     # Convert center lat/lon to world coordinates
#     sin_y_center = min(max(np.sin(center_lat * np.pi / 180), -0.9999), 0.9999)
#     center_world_x = 256 * (center_lon + 180) / 360
#     center_world_y = 256 * (
#         0.5 - np.log((1 + sin_y_center) / (1 - sin_y_center)) / (4 * np.pi)
#     )

#     # Calculate pixel coordinates
#     scale_factor = 2**zoom
#     pixel_x = (world_x - center_world_x) * scale_factor + image_width / (
#         2 * scale
#     )
#     pixel_y = (world_y - center_world_y) * scale_factor + image_height / (
#         2 * scale
#     )

#     # Normalize coordinates
#     x_normalized = pixel_x / image_width
#     y_normalized = pixel_y / image_height

#     return x_normalized, y_normalized


def points_to_yolov8_annotation(points: List[List[float]]) -> str:
    """Convert normalized points to YOLOv8 annotation string."""
    # Start with class 0 (assuming single class)
    annotation = ["0"]

    # Add coordinates
    for x, y in points:
        annotation.extend([f"{x:.8f}", f"{y:.8f}"])

    return " ".join(annotation)
