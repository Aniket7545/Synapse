"""Tool 16: notify_passenger_and_driver() - Notify both parties"""

import asyncio
from datetime import datetime
from typing import Dict, Any
from src.tools.base_tool import BaseTool


class NotifyPassengerAndDriverTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "notify_passenger_and_driver"
        self.description = "Notify both passenger and driver about route changes"
    
    async def _run(self, passenger_id: str, driver_id: str, new_route: Dict[str, Any], new_eta: str) -> Dict[str, Any]:
        await asyncio.sleep(0.4)
        
        return {
            "passenger_id": passenger_id,
            "driver_id": driver_id,
            "new_route": new_route,
            "new_eta": new_eta,
            "notifications_sent": {
                "passenger": {
                    "status": "sent",
                    "channel": "app_notification",
                    "message": f"Route updated. New ETA: {new_eta}",
                    "timestamp": datetime.now().isoformat()
                },
                "driver": {
                    "status": "sent", 
                    "channel": "driver_app",
                    "message": f"New route assigned. Updated ETA: {new_eta}",
                    "timestamp": datetime.now().isoformat()
                }
            },
            "coordination_status": "synchronized",
            "timestamp": datetime.now().isoformat()
        }
