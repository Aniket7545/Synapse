"""Tool 9: issue_instant_refund() - Process immediate refunds"""

import asyncio
from datetime import datetime
from typing import Dict, Any
from src.tools.base_tool import BaseTool


class IssueInstantRefundTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "issue_instant_refund"
        self.description = "Process instant refund or compensation to customer"
    
    async def _run(self, customer_id: str, order_id: str, amount: float, reason: str) -> Dict[str, Any]:
        await asyncio.sleep(0.8)
        
        return {
            "customer_id": customer_id,
            "order_id": order_id,
            "refund_amount_inr": amount,
            "reason": reason,
            "status": "processed",
            "transaction_id": f"refund_{order_id}_{int(datetime.now().timestamp())}",
            "expected_credit_time": "2-3 business days",
            "customer_notified": True,
            "timestamp": datetime.now().isoformat()
        }
