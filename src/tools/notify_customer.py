"""Tool 3: notify_customer() - Send notifications to customers"""

import asyncio
from datetime import datetime
from typing import Dict, Any
from src.tools.base_tool import BaseTool


class NotifyCustomerTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "notify_customer"
        self.description = "Send SMS, WhatsApp or app notifications to customers"
    
    async def _run(self, customer_id: str, message: str, channel: str = "sms") -> Dict[str, Any]:
        await asyncio.sleep(0.2)
        
        cost_map = {"sms": 0.05, "whatsapp": 0.02, "app_notification": 0.001}
        
        return {
            "customer_id": customer_id,
            "message": message,
            "channel": channel,
            "status": "sent",
            "timestamp": datetime.now().isoformat(),
            "message_id": f"{channel}_{customer_id}_{int(datetime.now().timestamp())}",
            "delivery_status": "delivered",
            "cost_inr": cost_map.get(channel, 0.05)
        }
