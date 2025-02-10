import os
import json
from pathlib import Path
from typing import Dict, List, Any
import cv2
import numpy as np
from PIL import Image


def hex_to_bgr(hex_color: str) -> tuple:
    """Convert hex color to BGR."""
    hex_color = hex_color.lstrip("#")
    rgb = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    return (rgb[2], rgb[1], rgb[0])


def draw_segment_with_watermark(
    image: np.ndarray,
    contours: List,
    hex_color: str = "#e8f34e",
    alpha: float = 0.5,
    outline_alpha: float = 0.8,
    watermark_path: str = None,
    watermark_scale: float = 0.2,
) -> np.ndarray:
    """
    Draw segment with watermark on image.

    Args:
        image: Input image
        contours: List of contours
        hex_color: Hex color for segment
        alpha: Segment transparency
        outline_alpha: Outline transparency
        watermark_path: Path to watermark image
        watermark_scale: Scale factor for watermark

    Returns:
        Image with segment and watermark
    """
    # Create copy of image
    result = image.copy()

    # Create mask for segment
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    cv2.drawContours(mask, contours, -1, 255, -1)

    # Create colored overlay
    overlay = np.zeros_like(image)
    bgr_color = hex_to_bgr(hex_color)
    overlay[mask > 0] = bgr_color

    # Blend overlay with image
    cv2.addWeighted(overlay, alpha, result, 1, 0, result)

    # Draw contours
    outline = np.zeros_like(image)
    cv2.drawContours(outline, contours, -1, bgr_color, 2)
    cv2.addWeighted(outline, outline_alpha, result, 1, 0, result)

    # Add watermark if provided
    if watermark_path and os.path.exists(watermark_path):
        try:
            # Load and resize watermark
            watermark = cv2.imread(watermark_path, cv2.IMREAD_UNCHANGED)
            if (
                watermark is not None and watermark.shape[2] == 4
            ):  # With alpha channel
                h, w = image.shape[:2]
                new_h = int(h * watermark_scale)
                new_w = int(new_h * watermark.shape[1] / watermark.shape[0])
                watermark = cv2.resize(watermark, (new_w, new_h))

                # Position watermark at bottom right
                y = h - new_h - 10
                x = w - new_w - 10

                # Extract alpha channel
                alpha_channel = watermark[:, :, 3] / 255.0

                # Blend watermark
                for c in range(3):
                    result[y : y + new_h, x : x + new_w, c] = (
                        result[y : y + new_h, x : x + new_w, c]
                        * (1 - alpha_channel)
                        + watermark[:, :, c] * alpha_channel
                    )
        except Exception as e:
            print(f"Error adding watermark: {str(e)}")

    return result


def process_lot_images_for_site(
    input_dir: str,
    output_dir: str,
    hex_color: str = "#e8f34e",
    watermark_path: str = None,
    confidence: float = 0.62,
) -> List[Dict[str, Any]]:
    """
    Process lot images for website display.

    Args:
        input_dir: Input directory with processed JSONs
        output_dir: Output directory for site images
        hex_color: Hex color for segments
        watermark_path: Path to watermark image
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

            # Get original image path from detection result path
            result_path = Path(doc["original_detection"]["result_path"])
            image_name = f"satellite_{doc['id'].split('_')[1]}.jpg"
            image_path = (
                result_path.parent.parent.parent / image_name
            )  # Go up one more level

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

            # Get contours
            contours, _ = cv2.findContours(
                mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            if not contours:
                continue

            # Draw segment with watermark
            result = draw_segment_with_watermark(
                image=image,
                contours=contours,
                hex_color=hex_color,
                watermark_path=watermark_path,
            )

            # Save result
            output_filename = f"site_{doc['id']}.jpg"
            output_path = os.path.join(output_dir, output_filename)
            cv2.imwrite(output_path, result)

            # Update document
            site_doc = {
                "object_id": doc["id"],
                "site_image_path": output_path,
                "confidence": confidence_value,
            }

            processed_docs.append(site_doc)

        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            continue

    return processed_docs
