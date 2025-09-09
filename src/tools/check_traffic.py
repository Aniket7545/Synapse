"""Tool 1: check_traffic() - Get real-time traffic conditions"""

import asyncio
from datetime import datetime
from typing import Dict, Any
from src.tools.base_tool import BaseTool


class CheckTrafficTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "check_traffic"
        self.description = "Get real-time traffic conditions and congestion data"
    
    async def _run(self, origin: str, destination: str, city: str) -> Dict[str, Any]:
        import os
        from src.tools.google_maps import GoogleMapsClient
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        client = GoogleMapsClient(api_key)

        # Call Google Maps API for route and traffic delay
        route_data = client.get_route(origin, destination)
        delay = client.get_traffic_delay(origin, destination)

        traffic_level = "unknown"
        if delay is not None:
            if delay > 20:
                traffic_level = "heavy"
            elif delay > 5:
                traffic_level = "moderate"
            else:
                traffic_level = "light"

        # Parse alternative routes if available
        alternative_routes = []
        if route_data and "routes" in route_data:
            for idx, route in enumerate(route_data["routes"]):
                leg = route["legs"][0]
                alt = {
                    "route_name": f"Route {idx+1}",
                    "time_minutes": leg.get("duration", {}).get("value", 0) // 60,
                    "distance_km": leg.get("distance", {}).get("value", 0) / 1000
                }
                alternative_routes.append(alt)

        return {
            "origin": origin,
            "destination": destination,
            "city": city,
            "traffic_level": traffic_level,
            "estimated_delay_minutes": delay if delay is not None else -1,
            "alternative_routes": alternative_routes,
            "timestamp": datetime.now().isoformat()
        }
