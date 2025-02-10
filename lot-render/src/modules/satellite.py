import requests
from typing import Optional


def get_satellite_image(
    lat: float,
    lng: float,
    zoom: int,
    api_key: str,
    size: str = "640x640",
    scale: int = 2,
) -> bytes:
    """
    Get a satellite image from Google Maps Static API.

    Args:
        lat: Latitude
        lng: Longitude
        zoom: Zoom level (0-21)
        api_key: Google Maps API key
        size: Image size (width x height)
        scale: Image scale (1 or 2)

    Returns:
        bytes: Image content
    """
    base_url = "https://maps.googleapis.com/maps/api/staticmap"

    params = {
        "center": f"{lat},{lng}",
        "zoom": zoom,
        "size": size,
        "scale": scale,
        "maptype": "satellite",
        "key": api_key,
    }

    response = requests.get(base_url, params=params)
    response.raise_for_status()

    return response.content
