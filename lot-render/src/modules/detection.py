import os
from pathlib import Path
import json
from typing import List, Dict, Any, Optional
import cv2
import numpy as np
from ultralytics import YOLO


def detect_lots_and_save(
    model_path: str,
    items_list: List[Dict[str, Any]],
    output_dir: str,
    adjust_mask: bool = False,
) -> List[Dict[str, Any]]:
    """
    Detect lots in images and save results.

    Args:
        model_path: Path to YOLO model
        items_list: List of items to process
        output_dir: Output directory
        adjust_mask: Whether to adjust masks

    Returns:
        List of processed documents
    """
    # Load YOLO model
    model = YOLO(model_path)

    processed_docs = []

    for item in items_list:
        try:
            # Load and resize image
            image_path = item["image_path"]
            image = cv2.imread(image_path)
            if image is None:
                continue

            # Get image dimensions
            height, width = image.shape[:2]

            # Run detection
            results = model(image)[0]

            # Process detections
            for i, detection in enumerate(results.boxes.data):
                confidence = float(detection[4])

                # Get mask
                if len(results.masks) > i:
                    mask = results.masks[i].data[0].cpu().numpy()
                    mask = (mask > 0.5).astype(np.uint8) * 255
                else:
                    continue

                # Adjust mask if requested
                if adjust_mask:
                    kernel = np.ones((5, 5), np.uint8)
                    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
                    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

                # Save results
                doc_id = f"{item['object_id']}_{i}"

                # Save mask
                mask_filename = f"mask_{doc_id}.png"
                mask_path = os.path.join(output_dir, "masks", mask_filename)
                cv2.imwrite(mask_path, mask)

                # Save detection visualization
                result_image = image.copy()
                contours, _ = cv2.findContours(
                    mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                )
                cv2.drawContours(result_image, contours, -1, (0, 255, 0), 2)

                result_filename = f"detection_{doc_id}.png"
                result_path = os.path.join(
                    output_dir, "detections", result_filename
                )
                cv2.imwrite(result_path, result_image)

                # Create document
                doc = {
                    "id": doc_id,
                    "original_detection": {
                        "confidence": confidence,
                        "mask_path": mask_path,
                        "result_path": result_path,
                        "image_dimensions": {"width": width, "height": height},
                    },
                    "metadata": {
                        "latitude": item["latitude"],
                        "longitude": item["longitude"],
                        "zoom": item["zoom"],
                        "year": item["year"],
                    },
                }

                if adjust_mask:
                    doc["adjusted_detection"] = {
                        "adjustment_method": "morphological",
                        "mask_path": mask_path,
                    }

                # Save JSON
                json_filename = f"detection_{doc_id}.json"
                json_path = os.path.join(output_dir, "json", json_filename)

                with open(json_path, "w") as f:
                    json.dump(doc, f, indent=2)

                processed_docs.append(doc)

        except Exception as e:
            print(f"Error processing {item['image_path']}: {str(e)}")
            continue

    return processed_docs
