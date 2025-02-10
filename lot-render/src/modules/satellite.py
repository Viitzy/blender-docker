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
    Get satellite image from Google Maps Static API.

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
    if response.status_code != 200:
        raise Exception(
            f"Error getting image: {response.status_code} - {response.text}"
        )

    return response.content
