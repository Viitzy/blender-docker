import os
import requests
from typing import Dict, Any


class GoogleMapsAPI:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GOOGLE_MAPS_API_KEY")
        if not self.api_key:
            raise ValueError("Google Maps API key not found")

    def get_satellite_image(
        self,
        lat: float,
        lng: float,
        zoom: int = 20,
        size: str = "640x640",
        scale: int = 2,
    ) -> bytes:
        """
        Get satellite image from Google Maps Static API.

        Args:
            lat: Latitude
            lng: Longitude
            zoom: Zoom level (0-21)
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
            "key": self.api_key,
        }

        response = requests.get(base_url, params=params)
        if response.status_code != 200:
            raise Exception(
                f"Error getting image: {response.status_code} - {response.text}"
            )

        return response.content

    def get_elevation(self, lat: float, lng: float) -> float:
        """
        Get elevation for a location using Google Maps Elevation API.

        Args:
            lat: Latitude
            lng: Longitude

        Returns:
            float: Elevation in meters
        """
        base_url = "https://maps.googleapis.com/maps/api/elevation/json"

        params = {"locations": f"{lat},{lng}", "key": self.api_key}

        response = requests.get(base_url, params=params)
        if response.status_code != 200:
            raise Exception(
                f"Error getting elevation: {response.status_code} - {response.text}"
            )

        data = response.json()
        if data["status"] != "OK":
            raise Exception(f"Elevation API error: {data['status']}")

        return data["results"][0]["elevation"]
