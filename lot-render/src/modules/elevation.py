import os
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Tuple
import requests
import time
import numpy as np


def init_elevation_cache(db_path: str) -> None:
    """Initialize elevation cache database."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS elevations
                 (lat REAL, lon REAL, elevation REAL,
                  PRIMARY KEY (lat, lon))"""
    )
    conn.commit()
    conn.close()


def get_elevations_batch(
    locations: List[Tuple[float, float]], api_key: str
) -> List[float]:
    """
    Get elevations for multiple locations using Google Maps Elevation API.

    Args:
        locations: List of (lat, lon) tuples
        api_key: Google Maps API key

    Returns:
        List of elevations in meters
    """
    base_url = "https://maps.googleapis.com/maps/api/elevation/json"

    # Format locations for API
    locations_str = "|".join(f"{lat},{lon}" for lat, lon in locations)

    params = {"locations": locations_str, "key": api_key}

    response = requests.get(base_url, params=params)
    response.raise_for_status()
    data = response.json()

    if data["status"] != "OK":
        raise Exception(f"Elevation API error: {data['status']}")

    return [result["elevation"] for result in data["results"]]


def get_elevations_with_cache(
    locations: List[Tuple[float, float]], api_key: str, db_path: str
) -> List[float]:
    """
    Get elevations with caching.

    Args:
        locations: List of (lat, lon) tuples
        api_key: Google Maps API key
        db_path: Path to SQLite cache database

    Returns:
        List of elevations in meters
    """
    # Initialize cache if needed
    if not os.path.exists(db_path):
        init_elevation_cache(db_path)

    # Connect to cache
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Check cache for each location
    elevations = []
    locations_to_fetch = []
    locations_map = {}  # Map original index to new index

    for i, (lat, lon) in enumerate(locations):
        c.execute(
            "SELECT elevation FROM elevations WHERE lat=? AND lon=?", (lat, lon)
        )
        result = c.fetchone()

        if result is not None:
            elevations.append(result[0])
        else:
            locations_to_fetch.append((lat, lon))
            locations_map[len(locations_to_fetch) - 1] = i
            elevations.append(None)

    # Fetch missing elevations
    if locations_to_fetch:
        try:
            fetched_elevations = get_elevations_batch(
                locations_to_fetch, api_key
            )

            # Update cache and results
            for i, elevation in enumerate(fetched_elevations):
                orig_index = locations_map[i]
                lat, lon = locations_to_fetch[i]

                # Update cache
                c.execute(
                    "INSERT OR REPLACE INTO elevations VALUES (?, ?, ?)",
                    (lat, lon, elevation),
                )

                # Update results
                elevations[orig_index] = elevation

            conn.commit()

        except Exception as e:
            print(f"Error fetching elevations: {str(e)}")
            # Fill missing elevations with None
            for i in locations_map.values():
                if elevations[i] is None:
                    elevations[i] = 0.0

    conn.close()

    return elevations


def process_lots_elevation(
    input_dir: str,
    output_dir: str,
    api_key: str,
    db_path: str,
    confidence: float = 0.62,
) -> List[Dict[str, Any]]:
    """
    Process lot elevations.

    Args:
        input_dir: Input directory with color JSONs
        output_dir: Output directory for elevation results
        api_key: Google Maps API key
        db_path: Path to SQLite cache database
        confidence: Minimum confidence threshold

    Returns:
        List of processed documents
    """
    processed_docs = []

    # Process each color file
    for filename in os.listdir(input_dir):
        if not filename.endswith(".json"):
            continue

        try:
            # Load document
            with open(os.path.join(input_dir, filename), "r") as f:
                doc = json.load(f)

            # Get points
            points = doc["point_colors"]["points"]
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

            # Get image dimensions
            dimensions = orig_doc["original_detection"]["image_dimensions"]
            width = dimensions["width"]
            height = dimensions["height"]

            # Get center coordinates
            lat = orig_doc["metadata"]["latitude"]
            lon = orig_doc["metadata"]["longitude"]
            zoom = orig_doc["metadata"]["zoom"]

            # Convert pixel coordinates to lat/lon
            # Based on Google Maps API tile system
            # Reference: https://developers.google.com/maps/documentation/javascript/coordinates

            lat_rad = lat * np.pi / 180
            n = 2.0**zoom
            world_coord = (
                n
                * (1 - (np.log(np.tan(lat_rad) + 1 / np.cos(lat_rad)) / np.pi))
                / 2
            )

            pixels_per_lon_degree = width / 360.0
            pixels_per_lon_radian = width / (2 * np.pi)

            # Convert points to lat/lon
            locations = []
            for x, y in points:
                # Convert to relative coordinates
                rel_x = (x - width / 2) / width
                rel_y = (y - height / 2) / height

                # Calculate lat/lon
                point_lon = lon + (rel_x * 360 / n)
                mercator_y = world_coord + (rel_y * n)
                point_lat = np.degrees(
                    np.arctan(np.sinh(np.pi * (1 - 2 * mercator_y / n)))
                )

                locations.append((point_lat, point_lon))

            # Get elevations
            elevations = get_elevations_with_cache(locations, api_key, db_path)

            # Create elevation document
            elevation_doc = {
                "id": doc["id"],
                "point_colors": doc["point_colors"].copy(),
            }

            # Add lat/lon/elevation to points
            elevation_doc["point_colors"]["lat_lon_elevation"] = [
                [lat, lon, elev]
                for (lat, lon), elev in zip(locations, elevations)
            ]

            # Save document
            output_path = os.path.join(output_dir, filename)
            with open(output_path, "w") as f:
                json.dump(elevation_doc, f, indent=2)

            processed_docs.append(elevation_doc)

        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            continue

    return processed_docs
