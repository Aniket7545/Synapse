"""Tool 5: get_nearby_merchants() - Find alternative merchants"""

import asyncio
from datetime import datetime
from typing import Dict, Any
from src.tools.base_tool import BaseTool


class GetNearbyMerchantsTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "get_nearby_merchants"
        self.description = "Find nearby alternative merchants when original is delayed"
    
    async def _run(self, location: str, item_category: str, radius_km: float = 5.0) -> Dict[str, Any]:
        await asyncio.sleep(0.6)
        
        nearby_merchants = [
            {
                "merchant_id": "ALT_001",
                "name": "Quick Bites Restaurant",
                "distance_km": 1.2,
                "prep_time_minutes": 20,
                "rating": 4.5,
                "available_items": ["Biryani", "Curry", "Naan"]
            },
            {
                "merchant_id": "ALT_002",
                "name": "Fast Food Corner", 
                "distance_km": 2.1,
                "prep_time_minutes": 15,
                "rating": 4.2,
                "available_items": ["Burger", "Pizza", "Sandwich"]
            },
            {
                "merchant_id": "ALT_003",
                "name": "Desi Kitchen",
                "distance_km": 3.5,
                "prep_time_minutes": 30,
                "rating": 4.7,
                "available_items": ["Dal", "Roti", "Sabzi"]
            }
        ]
        
        return {
            "search_location": location,
            "item_category": item_category,
            "radius_km": radius_km,
            "merchants_found": len(nearby_merchants),
            "merchants": nearby_merchants,
            "timestamp": datetime.now().isoformat()
        }
