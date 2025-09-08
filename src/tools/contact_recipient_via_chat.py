"""Tool 12: contact_recipient_via_chat() - Initiate chat with customer"""

import asyncio
from datetime import datetime
from typing import Dict, Any
from src.tools.base_tool import BaseTool


class ContactRecipientViaChatTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "contact_recipient_via_chat"
        self.description = "Contact recipient via chat with automated prompts"
    
    async def _run(self, customer_id: str, message: str) -> Dict[str, Any]:
        await asyncio.sleep(0.4)
        
        return {
            "customer_id": customer_id,
            "chat_session_id": f"chat_{customer_id}_{int(datetime.now().timestamp())}",
            "initial_message": message,
            "status": "initiated",
            "customer_online": True,
            "response_time_minutes": 2,
            "automated_prompts": [
                "Are you available to receive the delivery now?",
                "Would you prefer an alternative delivery time?",
                "Should we leave it with building security?"
            ],
            "timestamp": datetime.now().isoformat()
        }
