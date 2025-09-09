"""
Chain of Thought Tracking - Project Synapse
Handles execution results and thought tracking in the exact required format
"""

from datetime import datetime
from typing import Dict, List, Any


class ProperChainOfThought:
    """Chain of thought tracking matching your exact format"""
    
    def __init__(self):
        self.scenario_id = None
        self.execution_results = []
        self.chain_of_thought = []
        self.current_step = 0
    
    def start_scenario(self, scenario_id: str):
        """Start new scenario tracking"""
        self.scenario_id = scenario_id
        self.execution_results = []
        self.chain_of_thought = []
        self.current_step = 0
    
    def add_execution_result(self, agent: str, result_data: Dict[str, Any]):
        """Add execution result"""
        self.execution_results.append({
            "agent": agent,
            **result_data
        })
    
    def add_thought(self, agent_name: str, description: str, reasoning: str, 
                   tools_used: List[str] = None, confidence: float = 0.8):
        """Add thought step"""
        thought = {
            "step_id": f"{agent_name}_{self.current_step}_{self.scenario_id.split('_')[-1]}",
            "agent_name": agent_name,
            "thought_type": "ThoughtType.ANALYSIS",
            "description": description,
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "end_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "confidence": confidence,
            "reasoning": reasoning,
            "tools_used": tools_used or [],
            "metadata": None
        }
        self.chain_of_thought.append(thought)
        self.current_step += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary matching your format"""
        agents_involved = list(set([result["agent"] for result in self.execution_results]))
        avg_confidence = sum([step["confidence"] for step in self.chain_of_thought]) / len(self.chain_of_thought) if self.chain_of_thought else 0.8
        
        return {
            "total_steps": len(self.chain_of_thought),
            "completed_steps": len(self.chain_of_thought),
            "average_confidence": avg_confidence,
            "agents_involved": agents_involved,
            "thought_types": ["analysis"]
        }


# Global chain of thought tracker
chain_tracker = ProperChainOfThought()
