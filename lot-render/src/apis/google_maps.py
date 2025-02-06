import os
import requests


class GoogleMaps:
    def __init__(self):
        self.api_key = os.getenv("GMAPS_API_KEY_ELEVATION")
        self.base_url = "https://maps.googleapis.com/maps/api"

    def get_elevation(self, lat, lon):
        url = f"{self.base_url}/elevation/json"
        try:
            resp = requests.get(
                url, params={"locations": f"{lat},{lon}", "key": self.api_key}
            )
            result = resp.json()
            if result["status"] != "OK":
                return {"elevation": None, "error": result["status"]}

            return {
                "elevation": result["results"][0]["elevation"],
                "error": None,
            }

        except Exception as e:
            print(e)
            return {"elevation": None, "error": "Error fetching elevation data"}
