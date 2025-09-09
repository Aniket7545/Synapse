"""Tool 3: notify_customer() - Send real-time notifications to customers (LLM-driven simulation)"""

import asyncio
from datetime import datetime
from typing import Dict, Any
from src.tools.base_tool import BaseTool


class NotifyCustomerTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "notify_customer"
        self.description = "Send real-time SMS, WhatsApp or app notifications to customers using Twilio"
    
    async def _run(self, customer_id: str, message: str, channel: str = "sms", phone_number: str = None) -> Dict[str, Any]:
        """Send notification via specified channel (LLM-driven simulation - NO external APIs)"""
        
        # Generate phone number if not provided (for demo purposes)
        if not phone_number:
            phone_number = f"+91{customer_id[-9:]}"  # Generate Indian mobile number
        
        # LLM-driven simulation - no external API calls
        await asyncio.sleep(0.3)  # Simulate processing time
        
        result = {
            "tool_name": self.name,
            "status": "success",
            "customer_id": customer_id,
            "message": message,
            "channel": channel.lower(),
            "phone_number": phone_number,
            "timestamp": datetime.now().isoformat(),
            "message_id": f"SYN_{channel.upper()}_{customer_id}_{int(datetime.now().timestamp())}",
            "delivery_status": "delivered",
            "provider": "synapse_llm_simulation",
            "summary": f"Customer notification sent via {channel.upper()} successfully",
            "findings": f"Customer {customer_id} successfully notified about resolution progress",
            "actions": [f"Sent {channel.upper()} to {phone_number}", "Updated communication log", "Confirmed delivery"]
        }
        
        return result
