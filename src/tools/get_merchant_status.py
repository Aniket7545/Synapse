"""Tool 2: get_merchant_status() - Check merchant preparation times"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
from src.tools.base_tool import BaseTool


class GetMerchantStatusTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "get_merchant_status"
        self.description = "Get current merchant status including preparation times and capacity"
    
    async def _run(self, merchant_id: str) -> Dict[str, Any]:
        await asyncio.sleep(0.3)
        
        current_hour = datetime.now().hour
        
        # Simulate realistic merchant status based on time
        if 12 <= current_hour <= 14:  # Lunch rush
            prep_time = 40
            queue_length = 8
            capacity = "overloaded"
        elif 19 <= current_hour <= 21:  # Dinner rush
            prep_time = 35
            queue_length = 12
            capacity = "busy"
        else:
            prep_time = 25
            queue_length = 3
            capacity = "normal"
        
        return {
            "merchant_id": merchant_id,
            "merchant_name": f"Restaurant_{merchant_id}",
            "current_prep_time_minutes": prep_time,
            "normal_prep_time_minutes": 25,
            "orders_in_queue": queue_length,
            "kitchen_capacity_status": capacity,
            "estimated_ready_time": (datetime.now() + timedelta(minutes=prep_time)).isoformat(),
            "alternative_available": prep_time > 35,
            "last_updated": datetime.now().isoformat()
        }
