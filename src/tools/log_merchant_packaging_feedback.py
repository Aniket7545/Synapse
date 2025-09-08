"""Tool 11: log_merchant_packaging_feedback() - Send feedback to merchant"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List
from src.tools.base_tool import BaseTool


class LogMerchantPackagingFeedbackTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "log_merchant_packaging_feedback"
        self.description = "Send evidence-backed feedback to merchant for improvement"
    
    async def _run(self, merchant_id: str, feedback_text: str, evidence_links: List[str] = None) -> Dict[str, Any]:
        await asyncio.sleep(0.5)
        
        return {
            "merchant_id": merchant_id,
            "feedback_text": feedback_text,
            "evidence_attached": bool(evidence_links),
            "feedback_id": f"feedback_{merchant_id}_{int(datetime.now().timestamp())}",
            "status": "logged",
            "merchant_notified": True,
            "follow_up_required": True,
            "improvement_tracking": "enabled",
            "timestamp": datetime.now().isoformat()
        }
