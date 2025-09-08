# routing_logic.py
"""
Routing Logic for Project Synapse LangGraph Workflow
Determines agent routing and coordination patterns
"""

from typing import Dict, Any, List, Optional
from src.models.delivery_state import DeliveryState, DisruptionType

class AgentRouter:
    """Handles routing decisions between agents"""
    
    @staticmethod
    def route_from_coordinator(state: Dict[str, Any]) -> str:
        """Route from coordinator to appropriate specialist"""
        disruption_type = state.get("disruption_type", "")
        severity = state.get("severity_level", 5)
        
        # High-level routing logic
        if disruption_type in ["traffic_jam", "weather_impact"]:
            return "traffic_specialist"
        elif disruption_type == "merchant_delay":
            return "merchant_management"
        elif disruption_type == "dispute":
            return "crisis_resolution"
        elif disruption_type in ["customer_unavailable", "address_issue"]:
            return "customer_relations"
        else:
            return "traffic_specialist"  # Default
    
    @staticmethod
    def should_escalate(state: Dict[str, Any]) -> bool:
        """Determine if scenario should be escalated"""
        confidence = state.get("confidence_score", 0.0)
        attempts = len(state.get("actions_taken", []))
        severity = state.get("severity_level", 5)
        
        return (confidence < 0.6 and attempts >= 3) or severity >= 9
