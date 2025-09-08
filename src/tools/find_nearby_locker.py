"""Tool 14: find_nearby_locker() - Find secure parcel lockers"""

import asyncio
from datetime import datetime
from typing import Dict, Any
from src.tools.base_tool import BaseTool


class FindNearbyLockerTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "find_nearby_locker"
        self.description = "Find nearby secure parcel lockers for alternative delivery"
    
    async def _run(self, destination_address: str, radius_km: float = 2.0) -> Dict[str, Any]:
        await asyncio.sleep(0.7)
        
        return {
            "search_address": destination_address,
            "radius_km": radius_km,
            "lockers_found": [
                {
                    "locker_id": "LOC_001",
                    "location": "Metro Station - Central Plaza",
                    "distance_km": 0.8,
                    "availability": "available",
                    "security_level": "high",
                    "access_hours": "24/7"
                },
                {
                    "locker_id": "LOC_002",
                    "location": "Shopping Mall - Ground Floor",
                    "distance_km": 1.2,
                    "availability": "available",
                    "security_level": "medium",
                    "access_hours": "10:00-22:00"
                }
            ],
            "recommended_locker": "LOC_001",
            "timestamp": datetime.now().isoformat()
        }
