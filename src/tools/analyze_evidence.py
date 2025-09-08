"""Tool 8: analyze_evidence() - AI analysis of collected evidence"""

import asyncio
from datetime import datetime
from typing import Dict, Any
from src.tools.base_tool import BaseTool


class AnalyzeEvidenceTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "analyze_evidence"
        self.description = "Analyze collected evidence to determine fault and recommend resolution"
    
    async def _run(self, evidence_data: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(1.5)  # AI processing time
        
        # Simple fault determination logic
        if isinstance(evidence_data, dict) and "customer" in evidence_data:
            customer_resp = evidence_data.get("customer", {})
            driver_resp = evidence_data.get("driver", {})
        else:
            customer_resp = {"was_seal_intact": "no"}
            driver_resp = {"bag_sealed_by_merchant": "yes"}
        
        if (customer_resp.get("was_seal_intact") == "no" and 
            driver_resp.get("bag_sealed_by_merchant") == "yes"):
            fault_determination = "merchant_fault"
            confidence = 0.85
        else:
            fault_determination = "unclear"
            confidence = 0.60
        
        return {
            "analysis_id": f"analysis_{int(datetime.now().timestamp())}",
            "fault_determination": fault_determination,
            "confidence_score": confidence,
            "evidence_consistency": "high",
            "recommended_actions": [
                "issue_instant_refund" if fault_determination == "merchant_fault" else "goodwill_gesture",
                "exonerate_driver" if fault_determination == "merchant_fault" else "driver_training"
            ],
            "compensation_amount_inr": 150 if fault_determination == "merchant_fault" else 50,
            "analysis_timestamp": datetime.now().isoformat()
        }
