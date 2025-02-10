import os
import json
from pathlib import Path
from typing import Dict, List, Any
import cv2
import numpy as np
from shapely.geometry import Polygon


def calculate_lot_area(mask_path: str, metadata: Dict) -> float:
    """
    Calculate lot area in square meters from mask and metadata.

    Args:
        mask_path: Path to mask image
        metadata: Metadata with lat/lon and zoom

    Returns:
        Area in square meters
    """
    # Load mask
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    if mask is None:
        return 0.0

    # Get contours
    contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    if not contours:
        return 0.0

    # Get largest contour
    largest_contour = max(contours, key=cv2.contourArea)

    # Convert to polygon points
    points = largest_contour.reshape(-1, 2)

    # Convert pixel coordinates to lat/lon
    lat = metadata["latitude"]
    lon = metadata["longitude"]
    zoom = metadata["zoom"]

    # Calculate meters per pixel at this zoom level
    # Reference: https://wiki.openstreetmap.org/wiki/Zoom_levels
    meters_per_pixel = 156543.03392 * np.cos(lat * np.pi / 180) / (2**zoom)

    # Create polygon and calculate area
    polygon = Polygon(points)
    area_pixels = polygon.area

    # Convert to square meters
    area_m2 = area_pixels * (meters_per_pixel**2)

    return area_m2


def process_lot_areas(
    input_dir: str, output_dir: str, confidence_threshold: float = 0.62
) -> Dict[str, Any]:
    """
    Process lot areas from detection results.

    Args:
        input_dir: Input directory with detection JSONs
        output_dir: Output directory for processed results
        confidence_threshold: Minimum confidence threshold

    Returns:
        Statistics about the processing
    """
    stats = {
        "total_processed": 0,
        "successful": 0,
        "failed": 0,
        "total_area": 0.0,
        "average_area": 0.0,
    }

    # Process each detection file
    for filename in os.listdir(input_dir):
        if not filename.endswith(".json"):
            continue

        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)

        try:
            # Load detection
            with open(input_path, "r") as f:
                doc = json.load(f)

            stats["total_processed"] += 1

            # Check confidence
            confidence = doc["original_detection"]["confidence"]
            if confidence < confidence_threshold:
                stats["failed"] += 1
                continue

            # Get mask path
            if "adjusted_detection" in doc:
                mask_path = doc["adjusted_detection"]["mask_path"]
            else:
                mask_path = doc["original_detection"]["mask_path"]

            # Calculate area
            area_m2 = calculate_lot_area(mask_path, doc["metadata"])

            if area_m2 > 0:
                # Update document
                doc["area_m2"] = area_m2

                # Update stats
                stats["successful"] += 1
                stats["total_area"] += area_m2

                # Save processed document
                with open(output_path, "w") as f:
                    json.dump(doc, f, indent=2)
            else:
                stats["failed"] += 1

        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            stats["failed"] += 1
            continue

    # Calculate average area
    if stats["successful"] > 0:
        stats["average_area"] = stats["total_area"] / stats["successful"]

    return stats
