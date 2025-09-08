"""Tool 15: calculate_alternative_route() - Calculate alternative routes"""

import asyncio
from datetime import datetime
from typing import Dict, Any
from src.tools.base_tool import BaseTool


class CalculateAlternativeRouteTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "calculate_alternative_route"
        self.description = "Calculate alternative routes avoiding obstructions"
    
    async def _run(self, current_route: Dict[str, Any], obstruction_info: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(0.9)
        
        return {
            "original_route": current_route,
            "obstruction": obstruction_info,
            "alternative_routes": [
                {
                    "route_id": "ALT_A",
                    "description": "Via Ring Road bypass",
                    "estimated_time_minutes": 35,
                    "distance_km": 18.5,
                    "traffic_level": "moderate",
                    "additional_time_minutes": 10
                },
                {
                    "route_id": "ALT_B",
                    "description": "Through city center",
                    "estimated_time_minutes": 42,
                    "distance_km": 15.2,
                    "traffic_level": "heavy",
                    "additional_time_minutes": 17
                }
            ],
            "recommended_route": "ALT_A",
            "time_saved_minutes": 15,
            "timestamp": datetime.now().isoformat()
        }
