"""
Enhanced Chain of Thought tracking for Project Synapse
Captures detailed reasoning from all agents and tools
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, asdict
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

class ThoughtType(Enum):
    ANALYSIS = "analysis"
    TOOL_SELECTION = "tool_selection"
    COORDINATION = "coordination"
    DECISION = "decision"
    REASONING = "reasoning"

@dataclass
class ThoughtStep:
    step_id: str
    agent_name: str
    thought_type: ThoughtType
    description: str
    start_time: datetime
    end_time: Optional[datetime] = None
    confidence: Optional[float] = None
    reasoning: Optional[str] = None
    tools_used: List[str] = None
    metadata: Dict[str, Any] = None

class ChainOfThought:
    """Enhanced chain of thought tracking"""
    
    def __init__(self):
        self.thoughts: List[ThoughtStep] = []
        self.current_scenario_id: Optional[str] = None
        
    def start_thought(self, agent_name: str, thought_type: ThoughtType, description: str) -> str:
        """Start a new thinking step"""
        step_id = f"{agent_name}_{len(self.thoughts)}_{int(datetime.now().timestamp())}"
        
        thought_step = ThoughtStep(
            step_id=step_id,
            agent_name=agent_name,
            thought_type=thought_type,
            description=description,
            start_time=datetime.now(),
            tools_used=[]
        )
        
        self.thoughts.append(thought_step)
        
        # Display thinking in real-time
        self._display_thinking_start(thought_step)
        
        return step_id
    
    def complete_thought(self, step_id: str, confidence: float, reasoning: str):
        """Complete a thinking step"""
        for thought in self.thoughts:
            if thought.step_id == step_id:
                thought.end_time = datetime.now()
                thought.confidence = confidence
                thought.reasoning = reasoning
                
                # Display completion
                self._display_thinking_complete(thought)
                break
    
    def _display_thinking_start(self, thought: ThoughtStep):
        """Display thinking step start"""
        console.print(f"🧠 [{thought.thought_type.value.upper()}] {thought.agent_name}: {thought.description}")
    
    def _display_thinking_complete(self, thought: ThoughtStep):
        """Display thinking step completion"""
        duration = (thought.end_time - thought.start_time).total_seconds() if thought.end_time else 0
        console.print(f"   ✅ Confidence: {thought.confidence:.2f} | Duration: {duration:.1f}s")
    
    def display_full_chain(self):
        """Display complete chain of thought"""
        
        if not self.thoughts:
            console.print("No chain of thought data available")
            return
        
        console.print("\n🧠 [bold]Complete Chain of Thought[/bold]")
        
        for i, thought in enumerate(self.thoughts, 1):
            duration = ((thought.end_time - thought.start_time).total_seconds() 
                       if thought.end_time else 0)
            
            panel_content = f"""
[bold]{thought.agent_name.upper()}[/bold] - {thought.thought_type.value.title()}

📋 Task: {thought.description}
🤔 Reasoning: {thought.reasoning or 'In progress...'}
⚡ Duration: {duration:.1f} seconds
🎯 Confidence: {thought.confidence or 'N/A'}
            """.strip()
            
            console.print(Panel(
                panel_content,
                title=f"Step {i}",
                border_style="blue" if thought.confidence and thought.confidence > 0.8 else "yellow"
            ))
    
    def get_chain_summary(self) -> Dict[str, Any]:
        """Get summary of chain of thought"""
        
        if not self.thoughts:
            return {"total_steps": 0, "average_confidence": 0}
        
        total_confidence = sum(t.confidence for t in self.thoughts if t.confidence)
        completed_thoughts = [t for t in self.thoughts if t.confidence is not None]
        
        return {
            "total_steps": len(self.thoughts),
            "completed_steps": len(completed_thoughts),
            "average_confidence": total_confidence / len(completed_thoughts) if completed_thoughts else 0,
            "agents_involved": list(set(t.agent_name for t in self.thoughts)),
            "thought_types": list(set(t.thought_type.value for t in self.thoughts))
        }
    
    def get_full_chain(self) -> List[Dict[str, Any]]:
        """Get full chain as serializable data"""
        return [asdict(thought) for thought in self.thoughts]
    
    def export_thoughts(self, filename: Optional[str] = None) -> str:
        """Export chain of thought to JSON file"""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chain_of_thought_{timestamp}.json"
        
        export_data = {
            "scenario_id": self.current_scenario_id,
            "export_timestamp": datetime.now().isoformat(),
            "summary": self.get_chain_summary(),
            "complete_chain": self.get_full_chain()
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        return filename

# Global chain of thought instance
chain_of_thought = ChainOfThought()
