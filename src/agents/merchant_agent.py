"""
Merchant Agent - Specialist managing merchant relationships and fulfillment
"""

from typing import List
from src.agents.base_agent import BaseAgent
from src.models.delivery_state import DeliveryState
from src.models.agent_response import AgentResponse
from src.tools.get_merchant_status import GetMerchantStatusTool
from src.tools.get_nearby_merchants import GetNearbyMerchantsTool
from src.tools.log_merchant_packaging_feedback import LogMerchantPackagingFeedbackTool


class MerchantAgent(BaseAgent):
    def __init__(self):
        tools = [
            GetMerchantStatusTool(),
            GetNearbyMerchantsTool(),
            LogMerchantPackagingFeedbackTool()
        ]
        super().__init__(
            agent_name="merchant_agent",
            agent_description="Specialist managing merchant relationships and order fulfillment",
            tools=tools
        )
    
    async def handle(self, state: DeliveryState) -> AgentResponse:
        actions_taken = []
        
        # Step 1: Check merchant status
        merchant_result = await self.execute_tool("get_merchant_status", {
            "merchant_id": state.stakeholders.merchant_id
        })
        actions_taken.append("Assessed merchant capacity and preparation time")
        
        # Step 2: Find alternatives if merchant is overloaded
        merchant_data = merchant_result["data"]
        if merchant_data["current_prep_time_minutes"] > 35:
            alternatives_result = await self.execute_tool("get_nearby_merchants", {
                "location": state.location.origin_address,
                "item_category": state.order.order_type,
                "radius_km": 5.0
            })
            actions_taken.append("Located alternative merchants with shorter prep times")
            
            # Step 3: Log feedback for improvement
            if merchant_data["kitchen_capacity_status"] == "overloaded":
                feedback_result = await self.execute_tool("log_merchant_packaging_feedback", {
                    "merchant_id": state.stakeholders.merchant_id,
                    "feedback_text": f"Kitchen overloaded during {merchant_data['current_prep_time_minutes']} min prep time. Consider capacity planning.",
                    "evidence_links": []
                })
                actions_taken.append("Logged capacity feedback with merchant")
        
        analysis = f"""
MERCHANT COORDINATION COMPLETE:

Current Status:
- Prep Time: {merchant_data["current_prep_time_minutes"]} minutes (normal: {merchant_data["normal_prep_time_minutes"]})
- Kitchen Status: {merchant_data["kitchen_capacity_status"]}
- Queue Length: {merchant_data["orders_in_queue"]} orders

Actions Taken:
{chr(10).join([f"- {action}" for action in actions_taken])}

RECOMMENDATION: {'Alternative merchant coordination required' if merchant_data["current_prep_time_minutes"] > 35 else 'Original merchant can fulfill order'}
        """
        
        return AgentResponse(
            agent_name=self.agent_name,
            scenario_id=state.scenario_id,
            response_type="merchant_coordination",
            content=analysis,
            confidence=0.88,
            reasoning=analysis,
            next_agent="customer_agent",
            tools_used=[tool.name for tool in self.tools],
            actions_recommended=actions_taken
        )
    
    def get_required_tools(self) -> List[str]:
        return ["get_merchant_status", "get_nearby_merchants", "log_merchant_packaging_feedback"]
