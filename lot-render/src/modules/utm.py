import os
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
import pyproj


def convert_to_utm(lat: float, lon: float) -> Tuple[float, float, int]:
    """
    Convert lat/lon to UTM coordinates.

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        Tuple of (easting, northing, zone)
    """
    # Get UTM zone
    zone = int((lon + 180) / 6) + 1

    # Create projections
    wgs84 = pyproj.CRS("EPSG:4326")  # WGS84
    utm = pyproj.CRS(f"+proj=utm +zone={zone} +datum=WGS84")

    # Create transformer
    transformer = pyproj.Transformer.from_crs(wgs84, utm, always_xy=True)

    # Convert coordinates
    easting, northing = transformer.transform(lon, lat)

    return easting, northing, zone


def process_lots_utm_coordinates(
    input_dir: str, output_dir: str, confidence: float = 0.62
) -> List[Dict[str, Any]]:
    """
    Process lot coordinates to UTM.

    Args:
        input_dir: Input directory with elevation JSONs
        output_dir: Output directory for UTM results
        confidence: Minimum confidence threshold

    Returns:
        List of processed documents
    """
    processed_docs = []

    # Process each elevation file
    for filename in os.listdir(input_dir):
        if not filename.endswith(".json"):
            continue

        try:
            # Load document
            with open(os.path.join(input_dir, filename), "r") as f:
                doc = json.load(f)

            # Get points with elevation
            points = doc["point_colors"].get("lat_lon_elevation", [])
            if not points:
                continue

            # Get metadata from original detection
            orig_doc_path = os.path.join(
                os.path.dirname(input_dir), "json", filename
            )
            with open(orig_doc_path, "r") as f:
                orig_doc = json.load(f)

            # Check confidence
            confidence_value = orig_doc["original_detection"]["confidence"]
            if confidence_value < confidence:
                continue

            # Convert each point to UTM
            utm_points = []
            for lat, lon, elevation in points:
                easting, northing, zone = convert_to_utm(lat, lon)
                utm_points.append(
                    {
                        "easting": easting,
                        "northing": northing,
                        "elevation": elevation,
                        "zone": zone,
                    }
                )

            # Create UTM document
            utm_doc = {
                "id": doc["id"],
                "point_colors": doc["point_colors"].copy(),
                "points_utm": utm_points,
            }

            # Save document
            output_path = os.path.join(output_dir, filename)
            with open(output_path, "w") as f:
                json.dump(utm_doc, f, indent=2)

            processed_docs.append(utm_doc)

        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            continue

    return processed_docs
