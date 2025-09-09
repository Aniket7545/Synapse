"""
CLI Command Handlers for Project Synapse
Handles all command-line operations and user interactions
"""

import json
import asyncio
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from src.models.delivery_state import DeliveryState, DisruptionType, IndianCity
from src.utils.chain_of_thought import chain_of_thought, ThoughtType
from config.settings import settings

console = Console()

class CommandHandler:
    """Handles CLI command execution"""
    
    @staticmethod
    async def handle_scenario_run(scenario_type: str, city: str, severity: int, **kwargs) -> Dict[str, Any]:
        """Handle running a specific scenario"""
        
        console.print(f"🚀 [bold blue]Running scenario: {scenario_type}[/bold blue]")
        console.print(f"📍 Location: {city.title()}")
        console.print(f"⚠️ Severity: {severity}/10")
        
        # Create scenario state
        scenario_state = CommandHandler._create_demo_state(scenario_type, city, severity)
        
        # Simulate multi-agent execution
        result = await CommandHandler._simulate_agent_execution(scenario_state)
        
        return result
    
    @staticmethod
    def _create_demo_state(scenario_type: str, city: str, severity: int) -> Dict[str, Any]:
        """Create demo scenario state"""
        return {
            "scenario_id": f"DEMO_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "disruption_type": scenario_type,
            "city": city,
            "severity_level": severity,
            "status": "analyzing",
            "confidence_score": 0.0,
            "actions_taken": [],
            "agents_involved": []
        }
    
    @staticmethod
    async def _simulate_agent_execution(state: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate the multi-agent execution process"""
        
        from src.utils.chain_of_thought import ThoughtType
        import time
        
        # Coordinator analysis
        console.print("\n🤖 [cyan]COORDINATOR[/cyan] analyzing scenario...")
        step_id = chain_of_thought.start_thought(
            "coordinator",
            ThoughtType.ANALYSIS,
            f"Analyzing {state['disruption_type']} in {state['city']}"
        )
        
        await asyncio.sleep(1)  # Simulate processing
        chain_of_thought.complete_thought(
            step_id,
            confidence=0.9,
            reasoning=f"Identified {state['disruption_type']} requiring specialized coordination"
        )
        
        # Route to specialist
        if state['disruption_type'] == 'traffic_jam':
            specialist = "traffic_specialist"
        elif state['disruption_type'] == 'merchant_delay':
            specialist = "merchant_management"
        else:
            specialist = "customer_relations"
        
        # Specialist processing
        console.print(f"🔧 [green]{specialist.upper()}[/green] handling scenario...")
        step_id = chain_of_thought.start_thought(
            specialist,
            ThoughtType.ACTION,
            f"Executing {specialist} protocols"
        )
        
        await asyncio.sleep(2)  # Simulate processing
        chain_of_thought.complete_thought(
            step_id,
            confidence=0.85,
            reasoning=f"{specialist} completed analysis and recommendations"
        )
        
        # Customer communication
        console.print("💬 [magenta]CUSTOMER RELATIONS[/magenta] sending notifications...")
        step_id = chain_of_thought.start_thought(
            "customer_relations", 
            ThoughtType.COORDINATION,
            "Preparing customer communication"
        )
        
        await asyncio.sleep(1)
        chain_of_thought.complete_thought(
            step_id,
            confidence=0.95,
            reasoning="Customer notified with compensation and updated timeline"
        )
        
        # Final resolution
        state.update({
            "status": "resolved",
            "confidence_score": 0.92,
            "agents_involved": ["coordinator", specialist, "customer_relations"],
            "resolution_time": "3.2 minutes",
            "customer_satisfaction": "high"
        })
        
        return state
    
    @staticmethod
    def show_scenario_templates():
        """Show available scenario templates"""
        
        templates = [
            {
                "id": "mumbai_traffic_monsoon",
                "type": "traffic_jam",
                "city": "mumbai",
                "description": "Heavy monsoon traffic disruption in Mumbai",
                "severity": 8
            },
            {
                "id": "bangalore_restaurant_overload", 
                "type": "merchant_delay",
                "city": "bangalore",
                "description": "Restaurant overload during tech corridor lunch rush",
                "severity": 7
            },
            {
                "id": "delhi_delivery_dispute",
                "type": "dispute",
                "city": "delhi",
                "description": "Customer-driver delivery dispute resolution",
                "severity": 9
            }
        ]
        
        table = Table(title="Available Scenario Templates")
        table.add_column("Template ID", style="cyan")
        table.add_column("Type", style="magenta")
        table.add_column("City", style="yellow")
        table.add_column("Description", style="green")
        table.add_column("Severity", style="red")
        
        for template in templates:
            table.add_row(
                template["id"],
                template["type"],
                template["city"].title(),
                template["description"],
                str(template["severity"])
            )
        
        console.print(table)
    
    @staticmethod
    def export_chain_of_thought(format: str = "json") -> str:
        """Export chain of thought data"""
        
        if not chain_of_thought.thoughts:
            console.print("📭 No chain of thought data to export", style="yellow")
            return ""
        
        if format == "json":
            filename = chain_of_thought.export_thoughts()
            console.print(f"✅ Exported chain of thought to logs/{filename}")
            return filename
        else:
            console.print(f"❌ Format '{format}' not supported", style="red")
            return ""
