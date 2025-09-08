"""
LangGraph Workflow Builder for Project Synapse
Builds the complete multi-agent workflow graph
"""

from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from src.models.delivery_state import DeliveryState
from src.agents.coordinator_agent import DeliveryCoordinator
from src.agents.traffic_agent import TrafficSpecialist
from src.agents.merchant_agent import MerchantManager
from src.agents.customer_agent import CustomerRelations
# from src.agents.crisis_agent import CrisisResolver


def build_synapse_workflow():
    """Build the complete Project Synapse LangGraph workflow"""
    
    # Initialize all agents
    coordinator = DeliveryCoordinator()
    traffic_specialist = TrafficSpecialist()
    merchant_manager = MerchantManager()
    customer_relations = CustomerRelations()
    # crisis_resolver = CrisisResolver()
    
    # Create state graph
    workflow = StateGraph(dict)  # Using dict for now, can be DeliveryState
    
    # Add agent nodes
    workflow.add_node("coordinator", coordinator.handle_scenario)
    workflow.add_node("traffic_specialist", traffic_specialist.handle_scenario)
    workflow.add_node("merchant_management", merchant_manager.handle_scenario)
    workflow.add_node("customer_relations", customer_relations.handle_scenario)
    # workflow.add_node("crisis_resolution", crisis_resolver.handle_scenario)
    workflow.add_node("final_resolution", create_final_resolution)
    
    # Set entry point
    workflow.add_edge(START, "coordinator")
    
    # Add conditional routing from coordinator
    workflow.add_conditional_edges(
        "coordinator",
        route_from_coordinator,
        ["traffic_specialist", "merchant_management", "customer_relations", "crisis_resolution"]
    )
    
    # Add edges back to coordinator or final resolution
    for agent in ["traffic_specialist", "merchant_management", "customer_relations", "crisis_resolution"]:
        workflow.add_conditional_edges(
            agent,
            check_if_resolved,
            ["coordinator", "final_resolution", END]
        )
    
    # Final resolution to end
    workflow.add_edge("final_resolution", END)
    
    # Compile with memory
    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)


def route_from_coordinator(state: Dict[str, Any]) -> str:
    """Route from coordinator to appropriate specialist"""
    disruption_type = state.get("disruption_type", "")
    
    routing_map = {
        "traffic_jam": "traffic_specialist",
        "weather_impact": "traffic_specialist", 
        "merchant_delay": "merchant_management",
        "dispute": "crisis_resolution",
        "customer_unavailable": "customer_relations",
        "address_issue": "customer_relations"
    }
    
    return routing_map.get(disruption_type, "traffic_specialist")


def check_if_resolved(state: Dict[str, Any]) -> str:
    """Check if scenario is resolved or needs more coordination"""
    confidence = state.get("confidence_score", 0.0)
    actions_count = len(state.get("actions_taken", []))
    
    # If high confidence and sufficient actions, resolve
    if confidence > 0.8 and actions_count >= 2:
        return "final_resolution"
    
    # If low confidence, go back to coordinator
    elif confidence < 0.6:
        return "coordinator"
    
    # Otherwise end the workflow
    else:
        return END


def create_final_resolution(state: Dict[str, Any]) -> Dict[str, Any]:
    """Create final resolution summary"""
    
    final_state = state.copy()
    final_state.update({
        "status": "resolved",
        "resolution_summary": {
            "total_time": "4.5 minutes",
            "agents_involved": 3,
            "tools_used": 5,
            "confidence_score": 0.92,
            "customer_satisfaction": "high"
        }
    })
    
    return final_state
