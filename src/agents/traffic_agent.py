"""
Advanced Traffic Agent with Real-Time Google Maps Integration
"""

from typing import List, Dict, Any
from src.agents.base_agent import BaseAgent
from src.models.delivery_state import DeliveryState
from src.models.agent_response import AgentResponse
from src.tools.check_traffic import CheckTrafficTool
from src.tools.calculate_alternative_route import CalculateAlternativeRouteTool
from src.tools.re_route_driver import ReRouteDriverTool
from src.tools.notify_resolution import NotifyResolutionTool
from src.utils.chain_of_thought import chain_of_thought, ThoughtType

class TrafficAgent(BaseAgent):
    """Advanced traffic agent with real-time route optimization"""
    
    def __init__(self):
        tools = [
            CheckTrafficTool(),
            CalculateAlternativeRouteTool(),
            ReRouteDriverTool(),
            NotifyResolutionTool()
        ]
        super().__init__(
            agent_name="traffic_agent",
            agent_description="Expert traffic analyst with real-time Google Maps integration for optimal route planning and delay mitigation",
            tools=tools
        )
    
    async def handle(self, state: DeliveryState) -> AgentResponse:
        """Advanced traffic handling with live data and AI optimization"""
        
        thinking_id = chain_of_thought.start_thought(
            self.agent_name,
            ThoughtType.ANALYSIS,
            f"Analyzing traffic conditions for route: {state.location.origin_address} → {state.location.destination_address}"
        )
        
        actions_taken = []
        tools_used = []
        
        try:
            # Step 1: Get comprehensive live context
            live_context = await self.get_live_context(state)
            traffic_data = live_context.get('traffic', {})
            weather_data = live_context.get('weather', {})
            
            # Step 2: Enhanced traffic analysis with AI
            analysis_prompt = f"""
Analyze this traffic situation with live data:

ROUTE: {state.location.origin_address} → {state.location.destination_address}
CITY: {state.location.city.value}
ORDER URGENCY: {state.severity_level}/10

LIVE TRAFFIC DATA:
- Current Level: {traffic_data.get('traffic_level', 'unknown')}
- Delay: {traffic_data.get('traffic_delay_minutes', 0)} minutes
- Distance: {traffic_data.get('distance', 'unknown')}
- Duration with Traffic: {traffic_data.get('duration_in_traffic', 'unknown')}

WEATHER IMPACT:
- Condition: {weather_data.get('condition', 'unknown')}
- Delivery Impact: {weather_data.get('delivery_impact', 'low')}

Provide specific recommendations for:
1. Route optimization strategy
2. Delay mitigation actions
3. Customer communication approach
4. Driver coordination steps
            """
            
            ai_analysis = await self.get_ai_analysis(analysis_prompt, live_context)
            
            # Step 3: Execute traffic analysis tools
            traffic_result = await self.execute_tool("check_traffic", {
                "origin": state.location.origin_address,
                "destination": state.location.destination_address,
                "city": state.location.city.value,
                "live_data": traffic_data
            })
            
            if traffic_result["success"]:
                traffic_info = traffic_result["data"]
                actions_taken.append(f"Live traffic analysis: {traffic_info.get('traffic_level', 'moderate')} congestion")
                tools_used.append("check_traffic")
                
                # Step 4: Route optimization if needed
                if traffic_info.get("traffic_level") in ["heavy", "severe"] or traffic_info.get("estimated_delay_minutes", 0) > 10:
                    
                    # Calculate alternative routes
                    route_result = await self.execute_tool("calculate_alternative_route", {
                        "current_route": {
                            "origin": state.location.origin_address,
                            "destination": state.location.destination_address
                        },
                        "obstruction_info": {
                            "traffic_level": traffic_info.get("traffic_level"),
                            "delay": traffic_info.get("estimated_delay_minutes", 0),
                            "weather_impact": weather_data.get('delivery_impact', 'low')
                        }
                    })
                    
                    if route_result["success"]:
                        alternative_routes = route_result["data"]
                        actions_taken.append(f"Calculated {len(alternative_routes.get('alternative_routes', []))} alternative routes")
                        tools_used.append("calculate_alternative_route")
                        
                        # Re-route driver to best alternative
                        if alternative_routes.get('alternative_routes'):
                            best_route = alternative_routes['alternative_routes'][0]
                            
                            reroute_result = await self.execute_tool("re_route_driver", {
                                "driver_id": state.stakeholders.driver_id,
                                "new_route": best_route,
                                "reason": f"Traffic optimization: avoiding {traffic_info.get('traffic_level')} congestion"
                            })
                            
                            if reroute_result["success"]:
                                actions_taken.append(f"Driver re-routed via optimized path, saving {best_route.get('time_saved', 0)} minutes")
                                tools_used.append("re_route_driver")
                
                # Step 5: Comprehensive resolution notification
                resolution_result = await self.execute_tool("notify_resolution", {
                    "customer_id": state.stakeholders.customer_id,
                    "driver_id": state.stakeholders.driver_id,
                    "resolution_summary": f"Traffic optimization complete. Route analyzed with live data. {ai_analysis[:100]}...",
                    "outcome": "traffic_optimized",
                    "estimated_arrival": self._calculate_optimized_eta(traffic_info, live_context)
                })
                
                if resolution_result["success"]:
                    actions_taken.append("Sent comprehensive traffic resolution update to all parties")
                    tools_used.append("notify_resolution")
            
            # Compile comprehensive analysis
            comprehensive_analysis = f"""
ADVANCED TRAFFIC ANALYSIS COMPLETE:

LIVE CONDITIONS:
- Traffic Level: {traffic_data.get('traffic_level', 'unknown').title()}
- Current Delay: {traffic_data.get('traffic_delay_minutes', 0)} minutes
- Weather Impact: {weather_data.get('delivery_impact', 'low').title()}
- Route Distance: {traffic_data.get('distance', 'unknown')}

AI RECOMMENDATIONS:
{ai_analysis}

ACTIONS EXECUTED:
{chr(10).join([f"• {action}" for action in actions_taken])}

OPTIMIZATION RESULT: 
{"Route optimized with live traffic intelligence" if len(tools_used) > 1 else "Current route optimal"}
            """
            
            chain_of_thought.complete_thought(
                thinking_id,
                confidence=0.92,
                reasoning=comprehensive_analysis
            )
            
            return AgentResponse(
                agent_name=self.agent_name,
                scenario_id=state.scenario_id,
                response_type="advanced_traffic_optimization",
                content=comprehensive_analysis,
                confidence=0.92,
                reasoning=comprehensive_analysis,
                next_agent="customer_agent",
                tools_used=tools_used,
                actions_recommended=actions_taken
            )
            
        except Exception as e:
            chain_of_thought.complete_thought(
                thinking_id,
                confidence=0.50,
                reasoning=f"Traffic analysis failed: {str(e)}"
            )
            
            return AgentResponse(
                agent_name=self.agent_name,
                scenario_id=state.scenario_id,
                response_type="traffic_analysis_failed",
                content=f"Traffic analysis encountered error: {str(e)}. Using fallback coordination.",
                confidence=0.50,
                reasoning=f"Error in traffic analysis: {str(e)}",
                next_agent="customer_agent"
            )
    
    def _calculate_optimized_eta(self, traffic_info: Dict, live_context: Dict) -> str:
        """Calculate optimized ETA based on live conditions"""
        
        base_minutes = 30  # Default delivery time
        
        # Adjust for traffic
        traffic_delay = traffic_info.get("estimated_delay_minutes", 0)
        weather_delay = 5 if live_context.get('weather', {}).get('delivery_impact') == 'high' else 0
        
        total_minutes = base_minutes + traffic_delay + weather_delay
        
        # Format as time range
        min_time = max(15, total_minutes - 5)
        max_time = total_minutes + 10
        
        return f"{min_time}-{max_time} minutes"
    
    def get_required_tools(self) -> List[str]:
        return ["check_traffic", "calculate_alternative_route", "re_route_driver", "notify_resolution"]
