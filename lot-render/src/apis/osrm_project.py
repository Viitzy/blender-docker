import os
import requests


class OSRMProject:
    def __init__(self):
        self.base_url = os.getenv("OSRM_PROJECT_BASE_URL")

    def get_route(
        self,
        origin_lat: float,
        origin_lon: float,
        destination_lat: float,
        destination_lon: float,
        by: str = "driving",
    ):
        url = f"{self.base_url}/route/v1/{by}/{origin_lon},{origin_lat};{destination_lon},{destination_lat}"
        params = {"steps": "true", "overview": "full"}
        resp = requests.get(url, params=params)
        if not resp.ok:
            return None

        return resp.json()
