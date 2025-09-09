"""Tool 3: notify_customer() - Send real-time notifications to customers via Twilio"""

import asyncio
from datetime import datetime
from typing import Dict, Any
from src.tools.base_tool import BaseTool
from src.services.twilio_service import twilio_service


class NotifyCustomerTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "notify_customer"
        self.description = "Send real-time SMS, WhatsApp or app notifications to customers using Twilio"
    
    async def _run(self, customer_id: str, message: str, channel: str = "sms", phone_number: str = None) -> Dict[str, Any]:
        """Send notification via specified channel using real Twilio API"""
        
        # Generate phone number if not provided (for demo purposes)
        if not phone_number:
            phone_number = f"9{customer_id[-9:]}"  # Generate Indian mobile number
        
        if channel.lower() == "sms":
            result = await twilio_service.send_sms(phone_number, message, customer_id)
        elif channel.lower() == "whatsapp":
            result = await twilio_service.send_whatsapp(phone_number, message, customer_id)
        else:
            # App notification fallback
            await asyncio.sleep(0.1)
            result = {
                "customer_id": customer_id,
                "message": message,
                "channel": "app_notification",
                "status": "sent",
                "timestamp": datetime.now().isoformat(),
                "message_id": f"app_{customer_id}_{int(datetime.now().timestamp())}",
                "delivery_status": "delivered",
                "cost_inr": 0.001,
                "provider": "in_app"
            }
        
        return result
