"""
Enhanced Coordinator Agent maintaining original analysis format
"""

from typing import List
from src.agents.base_agent import BaseAgent
from src.models.delivery_state import DeliveryState
from src.models.agent_response import AgentResponse
from src.utils.chain_of_thought import chain_of_thought, ThoughtType
from config.llm_config import llm_client

class CoordinatorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="coordinator_agent",
            agent_description="Master coordinator analyzing disruptions and routing to specialists"
        )
    
    async def handle(self, state: DeliveryState) -> AgentResponse:
        """Enhanced coordination maintaining original analysis format"""
        
        thinking_id = chain_of_thought.start_thought(
            self.agent_name,
            ThoughtType.ANALYSIS,
            f"Analyzing {state.disruption_type.value} scenario: {state.description}"
        )
        
        # Enhanced analysis with live data consideration
        analysis_content = await self._comprehensive_analysis(state)
        
        # Smart routing based on description and context
        routing_decision = self._determine_routing(state)
        
        chain_of_thought.complete_thought(
            thinking_id,
            confidence=0.85,
            reasoning=f"Analyzed scenario and routed to {routing_decision}"
        )
        
        return AgentResponse(
            agent_name=self.agent_name,
            scenario_id=state.scenario_id,
            response_type="coordination",
            content=analysis_content,
            confidence=0.85,
            reasoning=analysis_content,
            next_agent=routing_decision
        )
    
    async def _comprehensive_analysis(self, state: DeliveryState) -> str:
        """Comprehensive analysis maintaining original format"""
        
        try:
            if llm_client.available:
                prompt = f"""
Analyze this delivery crisis:

Crisis: {state.disruption_type.value}
Description: {state.description}  
Severity: {state.severity_level}/10
Location: {state.location.city.value}

Provide brief analysis focusing on:
1. Root cause identification
2. Stakeholder impact  
3. Urgency assessment
4. Recommended approach

Keep response concise and actionable.
                """
                
                ai_analysis = await llm_client.chat_completion([
                    {"role": "system", "content": "You are a delivery crisis coordinator. Provide concise analysis."},
                    {"role": "user", "content": prompt}
                ])
                
                return ai_analysis
        except:
            pass
        
        # Fallback analysis
        return f"""
COORDINATOR ANALYSIS:
Scenario: {state.disruption_type.value.replace('_', ' ').title()}
Severity: {state.severity_level}/10 - {"High Priority" if state.severity_level >= 7 else "Standard Priority"}
Assessment: {self._assess_scenario(state)}
Recommended Action: Route to specialist for immediate resolution
        """
    
    def _determine_routing(self, state: DeliveryState) -> str:
        """Enhanced smart routing based on disruption type and context"""
        
        description = state.description.lower()
        
        # Primary routing based on disruption type
        if state.disruption_type.value == "traffic_disruption":
            return "traffic_agent"
        elif state.disruption_type.value == "merchant_delay":
            return "merchant_agent"
        elif state.disruption_type.value == "delivery_failed":
            return "customer_agent"
        elif state.disruption_type.value == "weather_disruption":
            return "traffic_agent"  # Traffic agent handles weather-related routing
        
        # Fallback keyword-based routing for complex scenarios  
        if any(word in description for word in ["damaged", "broken", "spilled", "dispute", "argue", "refund", "complaint"]):
            return "customer_agent"
        elif any(word in description for word in ["traffic", "jam", "road", "blocked", "route", "weather", "rain", "flood"]):
            return "traffic_agent"
            return "merchant_agent"
        else:
            # Default to customer agent for unknown scenarios
            return "customer_agent"
    
    def _assess_scenario(self, state: DeliveryState) -> str:
        """Assess scenario for analysis output"""
        
        if state.severity_level >= 8:
            return "Critical situation requiring immediate specialist intervention"
        elif state.severity_level >= 6:
            return "Moderate issue needing coordinated response"
        else:
            return "Standard issue manageable through normal protocols"
    
    def get_required_tools(self) -> List[str]:
        return []
