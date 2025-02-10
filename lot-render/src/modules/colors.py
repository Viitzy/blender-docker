import os
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
import cv2
import numpy as np
from PIL import Image


def compute_number_of_points(area_m2: float) -> int:
    """
    Compute number of points based on lot area.

    Args:
        area_m2: Lot area in square meters

    Returns:
        Number of points to sample
    """
    # Base number of points
    base_points = 50

    # Additional points based on area
    additional_points = int(area_m2 / 100)  # 1 point per 100m²

    # Total points capped at max_points
    total_points = min(base_points + additional_points, 130)

    return total_points


def get_points_inside_mask(
    mask: np.ndarray, area_m2: float, max_points: int = 130
) -> List[Tuple[int, int]]:
    """
    Get random points inside mask.

    Args:
        mask: Binary mask
        area_m2: Lot area in square meters
        max_points: Maximum number of points

    Returns:
        List of (x, y) points
    """
    # Get mask contours
    contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    if not contours:
        return []

    # Get largest contour
    contour = max(contours, key=cv2.contourArea)

    # Create point mask
    point_mask = np.zeros_like(mask)
    cv2.drawContours(point_mask, [contour], -1, 255, -1)

    # Get points inside mask
    y_coords, x_coords = np.where(point_mask > 0)
    if len(x_coords) == 0:
        return []

    # Compute number of points
    n_points = min(compute_number_of_points(area_m2), max_points)

    # Randomly sample points
    indices = np.random.choice(len(x_coords), size=n_points, replace=False)
    points = [(int(x_coords[i]), int(y_coords[i])) for i in indices]

    return points


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """Convert RGB to hex color."""
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def process_lot_colors(
    input_dir: str,
    output_dir: str,
    max_points: int = 130,
    dark_threshold: int = 70,
    bright_threshold: int = 215,
    confidence: float = 0.62,
) -> List[Dict[str, Any]]:
    """
    Process lot colors from satellite images.

    Args:
        input_dir: Input directory with processed JSONs
        output_dir: Output directory for color results
        max_points: Maximum number of points to sample
        dark_threshold: Threshold for dark colors
        bright_threshold: Threshold for bright colors
        confidence: Minimum confidence threshold

    Returns:
        List of processed documents
    """
    processed_docs = []

    # Process each detection file
    for filename in os.listdir(input_dir):
        if not filename.endswith(".json"):
            continue

        try:
            # Load document
            with open(os.path.join(input_dir, filename), "r") as f:
                doc = json.load(f)

            # Check confidence
            confidence_value = doc["original_detection"]["confidence"]
            if confidence_value < confidence:
                continue

            # Get area
            area_m2 = doc.get("area_m2", 0)
            if area_m2 <= 0:
                continue

            # Get original image path
            result_path = Path(doc["original_detection"]["result_path"])
            image_name = f"satellite_{doc['id'].split('_')[1]}.jpg"
            # Look for image in the satellite images directory
            image_path = (
                result_path.parent.parent / "satellite_images" / image_name
            )

            print(f"Looking for image at: {image_path}")  # Debug print

            # Load image
            image = cv2.imread(str(image_path))
            if image is None:
                print(f"Error loading image: {image_path}")
                continue

            # Get mask
            if "adjusted_detection" in doc:
                mask_path = doc["adjusted_detection"]["mask_path"]
            else:
                mask_path = doc["original_detection"]["mask_path"]

            mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
            if mask is None:
                print(f"Error loading mask: {mask_path}")
                continue

            # Get points inside mask
            points = get_points_inside_mask(mask, area_m2, max_points)
            if not points:
                continue

            # Get colors at points
            colors = []
            colors_adjusted = []

            for x, y in points:
                # Get BGR color
                bgr_color = image[y, x].tolist()
                # Convert to RGB
                rgb_color = bgr_color[::-1]

                # Adjust color if too dark or bright
                adjusted = rgb_color.copy()
                for i in range(3):
                    if adjusted[i] < dark_threshold:
                        adjusted[i] = dark_threshold
                    elif adjusted[i] > bright_threshold:
                        adjusted[i] = bright_threshold

                # Convert to hex
                hex_color = rgb_to_hex(tuple(rgb_color))
                hex_color_adjusted = rgb_to_hex(tuple(adjusted))

                colors.append(hex_color)
                colors_adjusted.append(hex_color_adjusted)

            # Create color document
            color_doc = {
                "id": doc["id"],
                "point_colors": {
                    "points": [(int(x), int(y)) for x, y in points],
                    "colors": colors,
                    "colors_adjusted": colors_adjusted,
                },
            }

            # Save document
            output_path = os.path.join(output_dir, filename)
            with open(output_path, "w") as f:
                json.dump(color_doc, f, indent=2)

            processed_docs.append(color_doc)

        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            continue

    return processed_docs
