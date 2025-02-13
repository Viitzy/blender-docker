from pathlib import Path
import os
import json
from datetime import datetime
from typing import Dict, Any, List
import numpy as np
from bson import ObjectId

from ...apis.google_maps import GoogleMapsAPI
from ...modules.area import calculate_geo_area
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


async def process_lot_service(
    doc_id: str,
    points: List[Dict[str, float]],
    zoom: int = 20,
    confidence: float = 0.62,
) -> Dict[str, Any]:
    """
    Service that processes a lot based on its polygon points.
    """
    try:
        google_maps = GoogleMapsAPI()
        # Get MongoDB connection string from environment
        mongo_connection_string = os.getenv("MONGO_CONNECTION_STRING")
        if not mongo_connection_string:
            return {
                "id": doc_id,
                "status": "error",
                "error": "MongoDB connection string not found in environment variables",
            }

        mongo_db = MongoDB()
        doc = await mongo_db.get_detection(doc_id)

        if not doc:
            return {
                "id": doc_id,
                "status": "error",
                "error": "Document not found",
            }

        # # Calculate area
        # points_lat_lon = [[p.lat, p.lon] for p in points]
        # area_m2 = calculate_geo_area(points_lat_lon)

        # # Initialize lot_details structure
        # lot_details = {
        #     "area_m2": area_m2,
        #     "point_colors": {
        #         "points": [],
        #         "colors": [],
        #         "colors_adjusted": [],
        #         "points_lat_lon": points_lat_lon,
        #         "points_utm": [],
        #         "cardinal_points": {},
        #         "front_points": [],
        #         "front_points_lat_lon": [],
        #         "street_points": [],
        #         "street_info": {},
        #     },
        #     "elevations": [],
        #     "mask_elevation": [],
        #     "mask_utm": [],
        # }

        # # Update MongoDB with initial lot_details
        # await mongo_db.update_detection(doc_id, {"lot_details": lot_details})

        # # Process colors
        # # colors_processed = process_lot_colors(
        # #     mongodb_uri=mongo_connection_string,
        # #     max_points=130,
        # #     dark_threshold=70,
        # #     bright_threshold=215,
        # #     confidence=confidence,
        # #     doc_id=doc_id,
        # # )

        # # if colors_processed:
        # #     point_colors = colors_processed[0].get("point_colors", {})
        # #     lot_details["point_colors"].update(point_colors)

        # #     # Update MongoDB with processed colors
        # #     await mongo_db.update_detection(
        # #         doc_id,
        # #         {"lot_details.point_colors": lot_details["point_colors"]},
        # #     )

        # # # Process site images
        # # watermark_path = (
        # #     Path(__file__).parent.parent.parent.parent
        # #     / "assets"
        # #     / "watermark.png"
        # # )
        # # site_images_processed = process_lot_images_for_site(
        # #     mongodb_uri=mongo_connection_string,
        # #     hex_color="#e8f34e",
        # #     watermark_path=str(watermark_path),
        # #     doc_id=doc_id,
        # #     confidence=confidence,
        # # )

        # # if site_images_processed:
        # #     site_image = site_images_processed[0]
        # #     if site_image.get("site_image_url"):
        # #         await mongo_db.update_detection(
        # #             doc_id,
        # #             {
        # #                 "image_info.image_thumb_site": site_image[
        # #                     "site_image_url"
        # #                 ]
        # #             },
        # #         )

        # Process elevations
        # google_maps = GoogleMapsAPI()
        # elevations_processed = process_lots_elevation(
        #     mongodb_uri=mongo_connection_string,
        #     api_key=google_maps.api_key,
        #     doc_id=doc_id,
        #     confidence=confidence,
        # )

        # if elevations_processed:
        #     doc = elevations_processed[0]  # Get updated document
        if True:

            # # Process UTM coordinates
            # utm_processed = process_lots_utm_coordinates(
            #     mongodb_uri=mongo_connection_string,
            #     doc_id=doc_id,
            #     confidence=confidence,
            # )

            # if utm_processed:
            #     doc = utm_processed[0]  # Get updated document
            #     print("utm_processed")

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
                # front_processed = process_front_points(
                #     mongodb_uri=mongo_connection_string,
                #     google_maps_api_key=google_maps.api_key,
                #     create_maps=False,
                #     doc_id=doc_id,
                #     confidence=confidence,
                # )

                # if front_processed:
                #     point_colors = front_processed[0].get("point_colors", {})
                #     await mongo_db.update_detection(
                #         doc_id, {"point_colors": point_colors}
                #     )

        #                 # Process CSV
        #                 csv_processed = process_lots_csv(
        #                     mongodb_uri=mongo_db.connection_string,
        #                     bucket_name="gethome-lots",
        #                     year=str(datetime.now().year),
        #                     doc_id=doc_id,
        #                     confidence=confidence,
        #                 )

        #                 if csv_processed:
        #                     # TODO: Upload CSV to cloud storage and update MongoDB with URL
        #                     csv_url = f"csv_url_for_{doc_id}"  # Placeholder
        #                     await mongo_db.update_detection(
        #                         doc_id, {"csv_elevation_colors": csv_url}
        #                     )

        #                     # Process GLB (only if CSV was processed)
        #                     if doc.get("csv_elevation_colors"):
        #                         glb_processed = process_lots_glb(
        #                             input_data=csv_processed[0],
        #                             confidence=confidence,
        #                         )

        #                         if glb_processed:
        #                             # TODO: Upload GLB to cloud storage and update MongoDB with URL
        #                             glb_url = f"glb_url_for_{doc_id}"  # Placeholder
        #                             await mongo_db.update_detection(
        #                                 doc_id,
        #                                 {"glb_elevation_file": glb_url},
        #                             )

        #                             # Process slope
        #                             slope_processed = process_lots_slope(
        #                                 mongodb_uri=mongo_db.connection_string,
        #                                 year=str(datetime.now().year),
        #                                 doc_id=doc_id,
        #                                 confidence=confidence,
        #                             )

        #                             if slope_processed:
        #                                 slope_data = slope_processed[0].get(
        #                                     "slope_info", {}
        #                                 )
        #                                 await mongo_db.update_detection(
        #                                     doc_id,
        #                                     {"slope_classify": slope_data},
        #                                 )

        # Get final document
        final_doc = await mongo_db.get_detection(doc_id)

        # Convert ObjectId to string before returning
        if final_doc and "_id" in final_doc:
            final_doc["_id"] = str(final_doc["_id"])

        return {"id": doc_id, "status": "success", "results": final_doc}

    except Exception as e:
        return {"id": doc_id, "status": "error", "error": str(e)}


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
