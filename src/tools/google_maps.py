import requests
from typing import Dict, Any, Optional

class GoogleMapsClient:
    """Client for Google Maps Directions and Traffic API"""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/directions/json"

    def get_route(self, origin: str, destination: str, mode: str = "driving") -> Optional[Dict[str, Any]]:
        params = {
            "origin": origin,
            "destination": destination,
            "mode": mode,
            "departure_time": "now",
            "key": self.api_key
        }
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Google Maps API error: {e}")
            return None

    def get_traffic_delay(self, origin: str, destination: str) -> Optional[int]:
        data = self.get_route(origin, destination)
        if not data or "routes" not in data or not data["routes"]:
            return None
        try:
            leg = data["routes"][0]["legs"][0]
            duration_in_traffic = leg.get("duration_in_traffic", {}).get("value")
            duration = leg.get("duration", {}).get("value")
            if duration_in_traffic and duration:
                delay_minutes = (duration_in_traffic - duration) // 60
                return max(delay_minutes, 0)
            return None
        except Exception as e:
            print(f"Error parsing traffic delay: {e}")
            return None
