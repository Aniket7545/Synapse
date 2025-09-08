"""
Notify Resolution Tool - Final resolution communication
Renamed from notify_passenger_and_driver as per document specifications
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List
from src.tools.base_tool import BaseTool


class NotifyResolutionTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "notify_resolution"
        self.description = "Send final resolution notification to all parties involved"
    
    async def _run(self, 
                   customer_id: str, 
                   driver_id: str, 
                   resolution_summary: str,
                   outcome: str = "resolved",
                   alternatives: List[Dict] = None,
                   **kwargs) -> Dict[str, Any]:
        """Send comprehensive resolution notification"""
        
        await asyncio.sleep(0.3)
        
        return {
            "customer_id": customer_id,
            "driver_id": driver_id,
            "resolution_summary": resolution_summary,
            "outcome": outcome,
            "alternatives_provided": alternatives or [],
            "notifications_sent": {
                "customer": {
                    "status": "delivered",
                    "channel": "app_notification",
                    "message": f"Resolution: {resolution_summary}",
                    "timestamp": datetime.now().isoformat()
                },
                "driver": {
                    "status": "delivered",
                    "channel": "driver_app", 
                    "message": f"Order resolution: {outcome}",
                    "timestamp": datetime.now().isoformat()
                }
            },
            "coordination_status": "resolution_complete",
            "all_parties_notified": True,
            "timestamp": datetime.now().isoformat()
        }
