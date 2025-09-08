"""Tool 7: collect_evidence() - Collect photos and statements"""

import asyncio
from datetime import datetime
from typing import Dict, Any
from src.tools.base_tool import BaseTool


class CollectEvidenceTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "collect_evidence"
        self.description = "Collect photos, statements and questionnaire responses"
    
    async def _run(self, order_id: str) -> Dict[str, Any]:
        await asyncio.sleep(2.0)  # Time for evidence collection
        
        return {
            "order_id": order_id,
            "evidence_collected": {
                "customer_photos": [
                    {"photo_id": "cust_001", "description": "Package condition", "timestamp": datetime.now().isoformat()},
                    {"photo_id": "cust_002", "description": "Delivery location", "timestamp": datetime.now().isoformat()}
                ],
                "driver_photos": [
                    {"photo_id": "drv_001", "description": "Package before delivery", "timestamp": datetime.now().isoformat()},
                    {"photo_id": "drv_002", "description": "Handover moment", "timestamp": datetime.now().isoformat()}
                ],
                "customer_statement": "Package was damaged with spilled contents when received.",
                "driver_statement": "Package was properly sealed when handed over to customer.",
                "questionnaire_responses": {
                    "customer": {"was_seal_intact": "no", "damage_visible": "yes"},
                    "driver": {"bag_sealed_by_merchant": "yes", "careful_handling": "yes"}
                }
            },
            "collection_timestamp": datetime.now().isoformat(),
            "status": "complete"
        }
