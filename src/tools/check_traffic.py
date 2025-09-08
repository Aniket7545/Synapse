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
        # Simulate API call delay
        await asyncio.sleep(0.5)
        
        # Realistic traffic simulation based on time and city
        current_hour = datetime.now().hour
        
        city_traffic_patterns = {
            "mumbai": {"peak_hours": [(8, 11), (18, 21)], "base_delay": 15, "multiplier": 2.5},
            "delhi": {"peak_hours": [(9, 12), (17, 20)], "base_delay": 12, "multiplier": 2.0},
            "bangalore": {"peak_hours": [(8, 10), (18, 20)], "base_delay": 18, "multiplier": 2.2}
        }
        
        pattern = city_traffic_patterns.get(city.lower(), city_traffic_patterns["delhi"])
        is_peak = any(start <= current_hour <= end for start, end in pattern["peak_hours"])
        
        if is_peak:
            traffic_level = "heavy"
            delay = int(pattern["base_delay"] * pattern["multiplier"])
        else:
            traffic_level = "moderate"
            delay = pattern["base_delay"]
        
        return {
            "origin": origin,
            "destination": destination,
            "city": city,
            "traffic_level": traffic_level,
            "estimated_delay_minutes": delay,
            "alternative_routes": [
                {"route_name": "Main Road", "time_minutes": delay + 10, "distance_km": 12.5},
                {"route_name": "Ring Road", "time_minutes": delay + 25, "distance_km": 15.2},
                {"route_name": "Highway", "time_minutes": delay + 5, "distance_km": 18.0}
            ],
            "timestamp": datetime.now().isoformat()
        }
