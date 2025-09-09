"""
Enhanced Merchant Agent - Real-time merchant API integration a        if merchant_data.get("current_prep_time_minutes", 0) > 35:
            console.print(f"   🛠️ Executing get_nearby_merchants tool...")
            alternatives_result = await self.execute_tool("get_nearby_merchants", {
                "location": state.location.origin_address,
                "item_category": "restaurant",
                "radius_km": 5.0
            }, thinking_id)
            actions_taken.append("Located alternative merchants with shorter prep times")
            tools_used.append("get_nearby_merchants") management
"""

from typing import List
from src.agents.base_agent import BaseAgent
from src.models.delivery_state import DeliveryState
from src.models.agent_response import AgentResponse
from src.tools.get_merchant_status import GetMerchantStatusTool
from src.tools.get_nearby_merchants import GetNearbyMerchantsTool
from src.tools.log_merchant_packaging_feedback import LogMerchantPackagingFeedbackTool
from src.tools.merchant_api_tools import (
    GetMerchantStatusTool as RealTimeMerchantStatusTool,
    CheckOrderStatusTool,
    CreateMerchantOrderTool,
    EstimatePreparationTimeTool,
    MonitorKitchenPerformanceTool,
    GetMerchantMenuTool
)
from src.utils.chain_of_thought import chain_of_thought, ThoughtType


class MerchantAgent(BaseAgent):
    def __init__(self):
        tools = [
            # Legacy tools
            GetMerchantStatusTool(),
            GetNearbyMerchantsTool(),
            LogMerchantPackagingFeedbackTool(),
            # New real-time API tools
            RealTimeMerchantStatusTool(),
            CheckOrderStatusTool(),
            CreateMerchantOrderTool(),
            EstimatePreparationTimeTool(),
            MonitorKitchenPerformanceTool(),
            GetMerchantMenuTool()
        ]
        super().__init__(
            agent_name="merchant_agent",
            agent_description="Enhanced merchant specialist with real-time API integration for order management and kitchen monitoring",
            tools=tools
        )
    
    async def handle(self, state: DeliveryState) -> AgentResponse:
        actions_taken = []
        tools_used = []
        
        # Start chain of thought tracking
        thinking_id = chain_of_thought.start_thought(
            self.agent_name,
            ThoughtType.ANALYSIS,
            f"Analyzing merchant delay: {state.description}"
        )
        
        # Step 1: Check merchant status
        from rich.console import Console
        console = Console()
        
        console.print(f"   🛠️ Executing get_merchant_status tool...")
        merchant_result = await self.execute_tool("get_merchant_status", {
            "merchant_id": state.stakeholders.merchant_id
        }, thinking_id)
        actions_taken.append("Assessed merchant capacity and preparation time")
        tools_used.append("get_merchant_status")
        
        # Step 2: Find alternatives if merchant is overloaded
        merchant_data = merchant_result.get("data", {})
        if merchant_data.get("current_prep_time_minutes", 0) > 35:
            alternatives_result = await self.execute_tool("get_nearby_merchants", {
                "location": state.location.origin_address,
                "item_category": "restaurant",
                "radius_km": 5.0
            })
            actions_taken.append("Located alternative merchants with shorter prep times")
            tools_used.append("get_nearby_merchants")
            
            # Step 3: Log feedback for improvement
            if merchant_data.get("kitchen_capacity_status") == "overloaded":
                console.print(f"   🛠️ Executing log_merchant_packaging_feedback tool...")
                feedback_result = await self.execute_tool("log_merchant_packaging_feedback", {
                    "merchant_id": state.stakeholders.merchant_id,
                    "feedback_text": f"Kitchen overloaded during {merchant_data.get('current_prep_time_minutes', 0)} min prep time. Consider capacity planning.",
                    "evidence_links": []
                }, thinking_id)
                actions_taken.append("Logged capacity feedback with merchant")
                tools_used.append("log_merchant_packaging_feedback")
        
        # Complete chain of thought
        chain_of_thought.complete_thought(
            thinking_id,
            confidence=0.9,
            reasoning=f"Analyzed merchant situation and executed {len(tools_used)} tools for resolution",
            tools_used=tools_used,
            actions_taken=actions_taken
        )
        
        analysis = f"""
MERCHANT COORDINATION COMPLETE:

Current Status:
- Prep Time: {merchant_data.get("current_prep_time_minutes", "unknown")} minutes (normal: {merchant_data.get("normal_prep_time_minutes", "unknown")})
- Kitchen Status: {merchant_data.get("kitchen_capacity_status", "unknown")}
- Queue Length: {merchant_data.get("orders_in_queue", "unknown")} orders

Actions Taken:
{chr(10).join([f"- {action}" for action in actions_taken])}

RECOMMENDATION: {'Alternative merchant coordination required' if merchant_data.get("current_prep_time_minutes", 0) > 35 else 'Original merchant can fulfill order'}
        """
        
        return AgentResponse(
            agent_name=self.agent_name,
            scenario_id=state.scenario_id,
            response_type="merchant_coordination",
            content=analysis,
            confidence=0.88,
            reasoning=analysis,
            next_agent="customer_agent",
            tools_used=tools_used,
            actions_recommended=actions_taken
        )
    
    def get_required_tools(self) -> List[str]:
        return ["get_merchant_status", "get_nearby_merchants", "log_merchant_packaging_feedback"]
