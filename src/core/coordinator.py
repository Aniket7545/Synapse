"""
Crisis Coordinator - Project Synapse
Coordinator that analyzes and routes (no tool execution), manages human approval
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from config.llm_config import LLMClient
from src.core.chain_tracker import chain_tracker
from src.core.tool_manager import DynamicToolManager
from src.agents.agentic_agent import ProperAgenticAgent
from src.utils.display import DisplayManager
from rich.console import Console
from rich.prompt import Confirm

console = Console()


class ProperCoordinator:
    """Coordinator that only analyzes and routes (no tool execution)"""
    
    def __init__(self):
        self.llm_client = LLMClient()
        self.display = DisplayManager()
        
        # Available agents
        self.agents = {
            "customer_agent": "Customer satisfaction, dispute resolution, evidence analysis, refund processing",
            "traffic_agent": "Route optimization, traffic analysis, weather assessment, driver coordination", 
            "merchant_agent": "Restaurant operations, food quality, merchant relations, supply chain"
        }
        
        console.print(self.display.get_startup_panel())
    
    async def handle_crisis(self, scenario: str) -> Dict[str, Any]:
        """Handle crisis with proper agentic workflow"""
        
        crisis_id = f"LIVE_{int(datetime.now().timestamp())}"
        
        console.print(self.display.get_crisis_start_panel(scenario, crisis_id))
        
        # Initialize chain tracking
        chain_tracker.start_scenario(crisis_id)
        
        # Phase 1: Coordinator Analysis and Routing
        console.print("\n🧠 [bold yellow]PHASE 1: COORDINATOR ANALYSIS & ROUTING[/bold yellow]")
        routing_result = await self._coordinator_analysis_and_routing(scenario)
        
        # Phase 2: Agent Execution
        selected_agent = routing_result['routing_decision']
        console.print(f"\n🎯 [bold yellow]PHASE 2: {selected_agent.upper().replace('_', ' ')} EXECUTION[/bold yellow]")
        
        # Initialize tool manager and agent
        tool_manager = DynamicToolManager()
        agent = ProperAgenticAgent(
            selected_agent,
            self.agents[selected_agent],
            self.llm_client,
            tool_manager
        )
        
        # Execute agent
        agent_result = await agent.analyze_and_execute(scenario, {"routing_info": routing_result})
        
        # Phase 3: Human approval if needed
        approval_result = await self._check_human_approval(agent_result, scenario)
        
        # Phase 4: Save results and display final output
        log_file = await self._save_proper_results(crisis_id, scenario, routing_result, agent_result, approval_result)
        await self.display.show_final_output(crisis_id, scenario, routing_result, agent_result, approval_result, log_file)
        
        return {
            "status": "RESOLVED" if approval_result.get('approved', True) else "PENDING_APPROVAL",
            "crisis_id": crisis_id,
            "log_file": log_file
        }
    
    async def _get_coordinator_thinking(self, scenario: str) -> str:
        """Get coordinator thinking process (1-2 lines)"""
        
        prompt = f"""
You are a Crisis Coordinator analyzing this scenario:
{scenario}

Show your initial thinking in 1-2 concise lines about what type of crisis this is and which specialist might be needed.
Examples:
- "Customer service crisis detected - requires dispute resolution specialist for immediate mediation..."
- "Traffic disruption identified - need routing specialist to assess alternative delivery paths..."
- "Merchant quality issue - requires food service specialist to handle packaging feedback..."

Respond with just 1-2 lines of coordinator thinking:
"""
        
        try:
            response = await self.llm_client.chat_completion([{"role": "user", "content": prompt}])
            thinking = response.strip().replace('\n', ' ')[:150]
            return f"Coordinator thinking: {thinking}"
        except:
            return "Coordinator thinking: Analyzing crisis type and determining optimal specialist routing..."

    async def _coordinator_analysis_and_routing(self, scenario: str) -> Dict[str, Any]:
        """Coordinator analyzes scenario and routes to appropriate agent"""
        
        console.print("🔍 [bold blue]Coordinator analyzing scenario...[/bold blue]")
        
        # Show coordinator thinking
        coord_thinking = await self._get_coordinator_thinking(scenario)
        console.print(f"💭 [italic cyan]{coord_thinking}[/italic cyan]")
        
        # Simple but reliable routing logic based on keywords (specific first)
        scenario_lower = scenario.lower()
        
        # Priority 1: Merchant/Restaurant issues (most specific)
        if any(word in scenario_lower for word in ["merchant", "restaurant", "food", "kitchen", "prep", "order", "overload"]):
            routing_decision = "merchant_agent"
            analysis = "Merchant and restaurant issue detected - requires coordination with food preparation and restaurant operations"
            reasoning = "Restaurant/merchant-related keywords indicate need for merchant relations specialist"
        # Priority 2: Traffic/Logistics issues 
        elif any(word in scenario_lower for word in ["traffic", "route", "delivery", "driver", "stuck", "jam"]) and not any(word in scenario_lower for word in ["restaurant", "prep", "kitchen", "overload"]):
            routing_decision = "traffic_agent"
            analysis = "Traffic and logistics issue detected - requires route optimization and delivery coordination"
            reasoning = "Traffic-related keywords indicate need for logistics specialist with route optimization capabilities"
        # Priority 3: Customer service issues (general keywords)
        elif any(word in scenario_lower for word in ["refund", "complaint", "damaged", "evidence", "dispute", "spilled", "broken"]):
            routing_decision = "customer_agent"
            analysis = "Customer service issue detected - requires evidence collection, damage assessment, and potential refund processing"
            reasoning = "Customer service keywords indicate need for dispute resolution specialist"
        else:
            routing_decision = "customer_agent"  # Default to customer service
            analysis = "General crisis scenario - routing to customer service for comprehensive handling"
            reasoning = "Default routing to customer service agent for general crisis management"
        
        confidence = 0.85
        
        # Display routing decision
        console.print(self.display.get_routing_panel(analysis, routing_decision, confidence, reasoning))
        
        # Add to chain of thought
        chain_tracker.add_thought(
            "coordinator",
            f"Analyzing scenario and routing decision",
            f"COORDINATOR ANALYSIS:\n{analysis}\n\nRouting: {routing_decision}\nConfidence: {confidence}\nReasoning: {reasoning}",
            [],
            confidence
        )
        
        # Add execution result
        chain_tracker.add_execution_result("coordinator", {
            "routing_decision": routing_decision,
            "confidence": confidence,
            "conclusion": f"Analyzed scenario and routed to {routing_decision}"
        })
        
        return {
            "analysis": analysis,
            "routing_decision": routing_decision,
            "confidence": confidence,
            "reasoning": reasoning
        }
    
    async def _check_human_approval(self, agent_result: Dict[str, Any], scenario: str) -> Dict[str, Any]:
        """Check if human approval is needed for financial or critical decisions"""
        
        # Check if scenario involves financial decisions
        financial_keywords = ["refund", "money", "payment", "cost", "charge", "compensation", "financial"]
        needs_approval = any(keyword in scenario.lower() for keyword in financial_keywords)
        
        # Also check tool results for financial actions
        for tool, result in agent_result.get('tool_results', {}).items():
            if any(keyword in tool.lower() or keyword in str(result).lower() for keyword in financial_keywords):
                needs_approval = True
                break
        
        if needs_approval:
            console.print(self.display.get_approval_panel(agent_result))
            
            approved = Confirm.ask("💰 [bold yellow]Approve financial actions?[/bold yellow]", default=True)
            
            return {
                "approval_required": True,
                "approved": approved,
                "approval_type": "financial",
                "reason": "Financial impact detected in scenario or tools"
            }
        else:
            return {
                "approval_required": False,
                "approved": True,
                "approval_type": "automatic",
                "reason": "No financial impact detected"
            }
    
    async def _save_proper_results(self, crisis_id: str, scenario: str, routing_result: Dict, 
                                 agent_result: Dict, approval_result: Dict) -> str:
        """Save results in proper chain of thought format"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"logs/chain_of_thought_{crisis_id}_{timestamp}.json"
        
        Path("logs").mkdir(exist_ok=True)
        
        # Create log data matching your exact format
        log_data = {
            "scenario_id": crisis_id,
            "timestamp": datetime.now().isoformat(),
            "execution_results": chain_tracker.execution_results,
            "chain_of_thought": chain_tracker.chain_of_thought,
            "summary": chain_tracker.get_summary(),
            "scenario": scenario,
            "financial_approval": approval_result
        }
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        return log_file
