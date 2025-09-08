"""
Four Core Agents as Specified in Project Synapse Document
"""

from typing import Dict, Any, List
from src.agents.base_agent import BaseAgent
from src.models.delivery_state import DeliveryState, AgentResponse
from src.utils.chain_of_thought import think, ThoughtType
from src.tools.document_tools import *


class CoordinatorAgent(BaseAgent):
    """Master coordinator analyzing disruptions and delegating to specialists"""
    
    def __init__(self):
        super().__init__(
            agent_name="coordinator",
            agent_description="Master orchestrator that analyzes delivery disruptions and coordinates specialist agents",
            tools=[]
        )
        
        self.base_prompt = """
You are the Delivery Crisis Coordinator - the master orchestrator for India's most advanced delivery system.

CORE MISSION:
Analyze incoming delivery disruptions and intelligently coordinate specialist agents to resolve issues efficiently.

RESPONSIBILITIES:
1. 🔍 ANALYZE: Understand the disruption type, severity, and impact on stakeholders
2. 🎯 ASSESS: Evaluate urgency, priority, and required resources
3. 🤝 DELEGATE: Route tasks to appropriate specialist agents (Traffic, Merchant, Customer)
4. ⚡ COORDINATE: Ensure seamless multi-agent collaboration
5. 📊 MONITOR: Track resolution progress and quality

DECISION FRAMEWORK:
- Traffic/Route issues → Traffic Agent
- Merchant/Restaurant delays → Merchant Agent  
- Customer communication/disputes → Customer Agent
- Complex scenarios → Multiple agents in sequence

Always provide clear reasoning for your delegation decisions and expected outcomes.
        """
    
    @think("coordinator", ThoughtType.ANALYSIS, "Analyzing disruption and determining agent coordination strategy")
    async def handle_scenario(self, state: DeliveryState) -> AgentResponse:
        """Analyze scenario and delegate to appropriate agents"""
        
        # Create coordination prompt
        coordination_prompt = f"""
DELIVERY DISRUPTION ANALYSIS

SCENARIO DETAILS:
- Disruption Type: {state.disruption_type}
- Location: {state.location.city}, {state.location.origin_address} → {state.location.destination_address}
- Severity Level: {state.severity_level}/10
- Order Value: ₹{state.order.total_value}
- Customer Tier: {state.stakeholders.customer_tier}

STAKEHOLDERS:
- Customer: {state.stakeholders.customer_id}
- Driver: {state.stakeholders.driver_id}  
- Merchant: {state.stakeholders.merchant_id}

REQUIRED COORDINATION:
1. Analyze the disruption's root cause and impact
2. Determine which specialist agents to involve
3. Define the sequence and priority of agent actions
4. Set success criteria and monitoring approach
5. Provide confidence score for resolution plan

Consider Indian market context: peak hours, weather, customer expectations.
        """
        
        # Execute LLM reasoning
        messages = [
            {"role": "system", "content": self.base_prompt},
            {"role": "user", "content": coordination_prompt}
        ]
        
        reasoning = await self.llm_client.chat_completion(messages)
        
        # Determine next agent based on disruption type
        next_agent = self._determine_next_agent(state.disruption_type, reasoning)
        
        return await self.create_response(
            state=state,
            reasoning=reasoning,
            confidence=0.9,
            next_agent=next_agent
        )
    
    def _determine_next_agent(self, disruption_type: str, reasoning: str) -> str:
        """Determine which specialist agent to route to"""
        
        reasoning_lower = reasoning.lower()
        
        # Check reasoning for agent indicators
        if any(keyword in reasoning_lower for keyword in ["traffic", "route", "congestion", "navigation"]):
            return "traffic_agent"
        elif any(keyword in reasoning_lower for keyword in ["merchant", "restaurant", "kitchen", "preparation"]):
            return "merchant_agent"
        elif any(keyword in reasoning_lower for keyword in ["customer", "communication", "dispute", "satisfaction"]):
            return "customer_agent"
        
        # Fallback to disruption type mapping
        routing_map = {
            "traffic_jam": "traffic_agent",
            "weather_impact": "traffic_agent",
            "merchant_delay": "merchant_agent", 
            "dispute": "customer_agent",
            "customer_unavailable": "customer_agent",
            "address_issue": "customer_agent"
        }
        
        return routing_map.get(disruption_type, "traffic_agent")


class TrafficAgent(BaseAgent):
    """Traffic specialist handling routing and navigation optimization"""
    
    def __init__(self):
        tools = [
            CheckTrafficTool(),
            CalculateAlternativeRouteTool(),
            ReRouteDriverTool(),
            NotifyPassengerAndDriverTool()
        ]
        
        super().__init__(
            agent_name="traffic_agent",
            agent_description="Specialist in traffic analysis and route optimization for Indian cities",
            tools=tools
        )
        
        self.base_prompt = """
You are the Traffic Intelligence Specialist for India's delivery network.

EXPERTISE:
- Real-time traffic analysis across Indian cities (Mumbai, Delhi, Bangalore, etc.)
- Route optimization considering local conditions (monsoons, peak hours, road quality)
- Multi-modal coordination (roads, metro, highways)
- Driver communication and navigation updates

TOOLS AVAILABLE:
- check_traffic(): Get real-time traffic conditions
- calculate_alternative_route(): Find optimal alternative routes  
- re_route_driver(): Update driver navigation
- notify_passenger_and_driver(): Coordinate communication

APPROACH:
1. Check current traffic conditions using live data
2. Calculate multiple alternative route options
3. Select optimal route based on time, distance, and reliability
4. Update driver navigation and notify all parties
5. Monitor route performance and adjust if needed

Focus on Indian traffic patterns: rush hours, weather impact, city-specific challenges.
        """


class MerchantAgent(BaseAgent):
    """Merchant specialist handling restaurant and vendor coordination"""
    
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
        
        self.base_prompt = """
You are the Merchant Relations Specialist for India's delivery ecosystem.

EXPERTISE:
- Restaurant and merchant capacity management
- Order preparation time optimization
- Alternative vendor coordination
- Quality control and feedback management

TOOLS AVAILABLE:
- get_merchant_status(): Check current prep times and capacity
- get_nearby_merchants(): Find alternative merchants when needed
- log_merchant_packaging_feedback(): Send improvement feedback

APPROACH:
1. Check merchant status and preparation capacity
2. If delays detected, find suitable alternative merchants
3. Coordinate merchant switching or manage delay expectations
4. Provide feedback to improve merchant performance
5. Ensure order quality and timing standards

Consider Indian meal times, festival impacts, and regional merchant variations.
        """


class CustomerAgent(BaseAgent):
    """Customer specialist handling communication and dispute resolution"""
    
    def __init__(self):
        tools = [
            NotifyCustomerTool(),
            ContactRecipientViaChatTool(),
            InitiateMediationFlowTool(),
            CollectEvidenceTool(),
            AnalyzeEvidenceTool(),
            IssueInstantRefundTool(),
            ExonerateDriverTool(),
            SuggestSafeDropOffTool(),
            FindNearbyLockerTool()
        ]
        
        super().__init__(
            agent_name="customer_agent",
            agent_description="Specialist in customer communication and satisfaction management",
            tools=tools
        )
        
        self.base_prompt = """
You are the Customer Experience Specialist for India's premier delivery service.

EXPERTISE:
- Multi-channel customer communication (SMS, WhatsApp, app notifications)
- Real-time dispute resolution and mediation
- Evidence-based conflict resolution
- Customer satisfaction and retention

TOOLS AVAILABLE:
- notify_customer(): Send updates via SMS/WhatsApp/app
- contact_recipient_via_chat(): Direct chat communication
- initiate_mediation_flow(): Start dispute resolution process
- collect_evidence(): Gather photos and statements
- analyze_evidence(): AI-powered evidence analysis
- issue_instant_refund(): Process compensations
- exonerate_driver(): Clear driver from fault
- suggest_safe_drop_off(): Alternative delivery options
- find_nearby_locker(): Secure locker locations

APPROACH:
1. Communicate transparently with customers about issues
2. For disputes: collect evidence from both parties
3. Use AI analysis to determine fault fairly
4. Execute appropriate resolution (refund, compensation, etc.)
5. Ensure all parties are satisfied with outcome

Focus on Indian customer preferences: language, cultural sensitivity, communication channels.
        """
