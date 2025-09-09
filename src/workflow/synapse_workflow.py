"""
Enhanced Project Synapse with Proper Terminal Organization
"""

import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from src.agents.coordinator_agent import CoordinatorAgent
from src.agents.traffic_agent import TrafficAgent
from src.agents.merchant_agent import MerchantAgent
from src.agents.customer_agent import CustomerAgent
from src.models.delivery_state import DeliveryState
from src.utils.chain_of_thought import chain_of_thought

console = Console()

class SynapseWorkflow:
    """Enhanced multi-agent orchestration with organized terminal output"""
    
    def __init__(self):
        self.agents = {
            "coordinator": CoordinatorAgent(),
            "traffic_agent": TrafficAgent(),
            "merchant_agent": MerchantAgent(),
            "customer_agent": CustomerAgent()
        }
        
        # Ensure logs directory exists
        Path("logs").mkdir(exist_ok=True)
        
        self.execution_results = []
    
    async def execute_scenario(self, delivery_state: DeliveryState) -> Dict[str, Any]:
        """Execute scenario with organized terminal output"""
        
        # Clean scenario display
        scenario_panel = Panel.fit(
            f"🎯 [bold]Scenario:[/bold] {delivery_state.disruption_type.value.replace('_', ' ').title()}\n"
            f"📍 [bold]Location:[/bold] {delivery_state.location.city.value.title()}\n"
            f"⚠️ [bold]Severity:[/bold] {delivery_state.severity_level}/10\n"
            f"💰 [bold]Order Value:[/bold] ₹{delivery_state.order.total_value}\n"
            f"📦 [bold]Items:[/bold] {', '.join(delivery_state.order.items)}",
            title="🚛 Delivery Crisis Analysis",
            border_style="blue"
        )
        console.print(scenario_panel)
        
        # Clear previous data
        chain_of_thought.thoughts.clear()
        chain_of_thought.current_scenario_id = delivery_state.scenario_id
        self.execution_results = []
        
        console.print("\n🤖 [bold blue]Multi-Agent Coordination Starting...[/bold blue]\n")
        
        try:
            # Step 1: Coordinator Agent
            coordinator_result = await self._execute_coordinator(delivery_state)
            
            # Step 2: Specialist Agent
            specialist_result = None
            if coordinator_result["routing_decision"]:
                specialist_result = await self._execute_specialist(
                    delivery_state, 
                    coordinator_result["routing_decision"]
                )
            
            # Step 3: Customer Agent (if not already executed)
            customer_result = None
            if coordinator_result["routing_decision"] != "customer_agent":
                customer_result = await self._execute_customer_agent(delivery_state)
            
            # Step 4: Display Final Results & Save Chain of Thought
            chain_file = self._save_chain_of_thought(delivery_state.scenario_id)
            
            # Final Summary
            self._display_final_summary(coordinator_result, specialist_result, customer_result)
            
            console.print(f"\n📄 [bold]Chain of Thought saved to:[/bold] [cyan]{chain_file}[/cyan]")
            
            return {
                "status": "success",
                "scenario_id": delivery_state.scenario_id,
                "execution_results": self.execution_results,
                "chain_of_thought_file": chain_file
            }
            
        except Exception as e:
            console.print(f"\n❌ [bold red]Error during execution:[/bold red] {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def _execute_coordinator(self, delivery_state: DeliveryState) -> Dict[str, Any]:
        """Execute coordinator with organized output"""
        
        console.print("┌" + "─" * 70 + "┐")
        console.print("│" + " " * 25 + "🧭 COORDINATOR AGENT" + " " * 24 + "│")
        console.print("├" + "─" * 70 + "┤")
        console.print("│ Role: Master orchestrator analyzing disruptions and routing        │")
        console.print("└" + "─" * 70 + "┘")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("🔍 Analyzing scenario and determining routing...", total=None)
            
            coordinator_response = await self.agents["coordinator"].handle(delivery_state)
            
            progress.update(task, completed=True, description="✅ Analysis complete")
        
        # Display Coordinator Results
        coord_panel = Panel.fit(
            f"📊 [bold]Analysis:[/bold] {coordinator_response.content[:100]}...\n"
            f"🎯 [bold]Routing Decision:[/bold] {coordinator_response.next_agent}\n"
            f"📈 [bold]Confidence:[/bold] {coordinator_response.confidence:.2f}/1.0\n"
            f"💡 [bold]Conclusion:[/bold] Route to {coordinator_response.next_agent.replace('_', ' ').title()} for specialized handling",
            title="🧭 Coordinator Results",
            border_style="green"
        )
        console.print(coord_panel)
        
        result = {
            "agent": "coordinator",
            "routing_decision": coordinator_response.next_agent,
            "confidence": coordinator_response.confidence,
            "conclusion": f"Analyzed {delivery_state.disruption_type.value} scenario and routed to {coordinator_response.next_agent}"
        }
        
        self.execution_results.append(result)
        return result
    
    async def _execute_specialist(self, delivery_state: DeliveryState, agent_name: str) -> Dict[str, Any]:
        """Execute specialist agent with organized output"""
        
        agent_display_names = {
            "traffic_agent": ("🚦 TRAFFIC AGENT", "Specialist in traffic analysis and route optimization"),
            "merchant_agent": ("🏪 MERCHANT AGENT", "Specialist in merchant coordination and fulfillment"),
            "customer_agent": ("💬 CUSTOMER AGENT", "Specialist in customer communication and satisfaction")
        }
        
        display_name, description = agent_display_names.get(agent_name, ("🤖 AGENT", "Specialist agent"))
        
        console.print("\n┌" + "─" * 70 + "┐")
        console.print(f"│{display_name:^70}│")
        console.print("├" + "─" * 70 + "┤")
        console.print(f"│ Role: {description:<59} │")
        console.print("└" + "─" * 70 + "┘")
        
        tools_used = []
        actions_taken = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("🛠️ Executing specialized tasks...", total=None)
            
            # Execute with tool logging
            specialist_response = await self._execute_with_detailed_logging(
                self.agents[agent_name], delivery_state, agent_name
            )
            
            tools_used = specialist_response.tools_used
            actions_taken = specialist_response.actions_recommended
            
            progress.update(task, completed=True, description="✅ Specialist tasks complete")
        
        # Display Specialist Results
        tools_display = ", ".join(tools_used) if tools_used else "None"
        actions_display = "\n".join([f"• {action}" for action in actions_taken[:3]]) if actions_taken else "• No specific actions"
        
        specialist_panel = Panel.fit(
            f"🛠️ [bold]Tools Used:[/bold] {tools_display}\n"
            f"⚡ [bold]Actions Taken:[/bold]\n{actions_display}\n"
            f"📈 [bold]Confidence:[/bold] {specialist_response.confidence:.2f}/1.0\n"
            f"💡 [bold]Conclusion:[/bold] {self._get_specialist_conclusion(agent_name, specialist_response)}",
            title=f"{display_name.split()[1]} Results",
            border_style="yellow"
        )
        console.print(specialist_panel)
        
        result = {
            "agent": agent_name,
            "tools_used": tools_used,
            "actions_taken": actions_taken,
            "confidence": specialist_response.confidence,
            "conclusion": self._get_specialist_conclusion(agent_name, specialist_response)
        }
        
        self.execution_results.append(result)
        return result
    
    async def _execute_customer_agent(self, delivery_state: DeliveryState) -> Dict[str, Any]:
        """Execute customer agent for final communication"""
        
        console.print("\n┌" + "─" * 70 + "┐")
        console.print("│" + " " * 24 + "💬 CUSTOMER AGENT" + " " * 25 + "│")
        console.print("├" + "─" * 70 + "┤")
        console.print("│ Role: Final customer communication and satisfaction management     │")
        console.print("└" + "─" * 70 + "┘")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("📞 Managing customer communication...", total=None)
            
            customer_response = await self._execute_with_detailed_logging(
                self.agents["customer_agent"], delivery_state, "customer_agent"
            )
            
            progress.update(task, completed=True, description="✅ Customer communication complete")
        
        # Display Customer Results
        customer_panel = Panel.fit(
            f"📱 [bold]Communication:[/bold] {', '.join(customer_response.tools_used)}\n"
            f"😊 [bold]Satisfaction Score:[/bold] {customer_response.confidence:.2f}/1.0\n"
            f"💡 [bold]Conclusion:[/bold] Customer informed and satisfied with resolution approach",
            title="💬 Customer Agent Results",
            border_style="magenta"
        )
        console.print(customer_panel)
        
        result = {
            "agent": "customer_agent",
            "tools_used": customer_response.tools_used,
            "confidence": customer_response.confidence,
            "conclusion": "Customer communication completed successfully"
        }
        
        self.execution_results.append(result)
        return result
    
    async def _execute_with_detailed_logging(self, agent, delivery_state: DeliveryState, agent_name: str):
        """Execute agent with detailed tool logging"""
        
        original_execute_tool = agent.execute_tool
        
        async def logged_execute_tool(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
            # Show tool execution
            params_str = self._format_params_clean(parameters)
            console.print(f"   🔧 Executing [bold cyan]{tool_name}[/bold cyan]({params_str})")
            
            result = await original_execute_tool(tool_name, parameters)
            
            if result.get("success"):
                summary = self._get_tool_summary(tool_name, result.get("data", {}))
                console.print(f"   ✅ Result: {summary}")
            else:
                console.print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
            
            return result
        
        agent.execute_tool = logged_execute_tool
        
        try:
            return await agent.handle(delivery_state)
        finally:
            agent.execute_tool = original_execute_tool
    
    def _format_params_clean(self, params: Dict[str, Any]) -> str:
        """Format parameters cleanly"""
        if not params:
            return ""
        
        clean_params = []
        for k, v in list(params.items())[:2]:  # Show first 2 params
            if isinstance(v, str) and len(v) > 20:
                clean_params.append(f"{k}='{v[:20]}...'")
            else:
                clean_params.append(f"{k}={v}")
        
        return ", ".join(clean_params)
    
    def _get_tool_summary(self, tool_name: str, data: Dict[str, Any]) -> str:
        """Get concise tool result summary"""
        
        summaries = {
            "check_traffic": f"Traffic: {data.get('traffic_level', 'unknown')}, Delay: {data.get('estimated_delay_minutes', 0)}min",
            "get_merchant_status": f"Prep: {data.get('current_prep_time_minutes', 0)}min, Status: {data.get('kitchen_capacity_status', 'unknown')}",
            "notify_customer": f"Notification sent via {data.get('channel', 'unknown')}",
            "get_nearby_merchants": f"Found {len(data.get('merchants', []))} alternatives",
            "collect_evidence": f"Evidence collected from both parties",
            "analyze_evidence": f"Fault: {data.get('fault_determination', 'unknown')}, Confidence: {data.get('confidence_score', 0):.2f}",
            "issue_instant_refund": f"₹{data.get('refund_amount_inr', 0)} refund processed"
        }
        
        return summaries.get(tool_name, "Completed successfully")
    
    def _get_specialist_conclusion(self, agent_name: str, response) -> str:
        """Get specialist-specific conclusion"""
        
        conclusions = {
            "traffic_agent": "Traffic conditions analyzed and optimal route determined",
            "merchant_agent": "Merchant capacity assessed and alternatives coordinated if needed",
            "customer_agent": "Customer communication handled and satisfaction ensured"
        }
        
        base_conclusion = conclusions.get(agent_name, "Specialized handling completed")
        
        if hasattr(response, 'tools_used') and response.tools_used:
            tool_count = len(response.tools_used)
            return f"{base_conclusion} using {tool_count} specialized tools"
        
        return base_conclusion
    
    def _display_final_summary(self, coordinator_result, specialist_result, customer_result):
        """Display comprehensive final summary"""
        
        console.print("\n" + "="*70)
        console.print("                    🎉 RESOLUTION SUMMARY")
        console.print("="*70)
        
        # Create summary table
        summary_table = Table(title="📊 Multi-Agent Coordination Results")
        summary_table.add_column("Agent", style="cyan", width=15)
        summary_table.add_column("Conclusion", style="white", width=40)
        summary_table.add_column("Confidence", style="green", width=10)
        
        # Add coordinator
        summary_table.add_row(
            "🧭 Coordinator", 
            coordinator_result["conclusion"],
            f"{coordinator_result['confidence']:.2f}"
        )
        
        # Add specialist
        if specialist_result:
            agent_display = specialist_result["agent"].replace("_", " ").title()
            summary_table.add_row(
                f"🔧 {agent_display}",
                specialist_result["conclusion"],
                f"{specialist_result['confidence']:.2f}"
            )
        
        # Add customer agent
        if customer_result:
            summary_table.add_row(
                "💬 Customer Agent",
                customer_result["conclusion"],
                f"{customer_result['confidence']:.2f}"
            )
        
        console.print(summary_table)
        
        # Overall outcome
        total_tools = sum(len(result.get("tools_used", [])) for result in self.execution_results)
        avg_confidence = sum(result["confidence"] for result in self.execution_results) / len(self.execution_results)
        
        outcome_panel = Panel.fit(
            f"✅ [bold green]Scenario Successfully Resolved[/bold green]\n\n"
            f"🤝 Agents Coordinated: {len(self.execution_results)}\n"
            f"🛠️ Tools Executed: {total_tools}\n"
            f"📊 Average Confidence: {avg_confidence:.2f}/1.0\n"
            f"⏱️ Resolution Status: Complete\n"
            f"🎯 Outcome: All stakeholders aligned and issue resolved",
            title="🏆 Final Outcome",
            border_style="green"
        )
        console.print(outcome_panel)
    
    def _save_chain_of_thought(self, scenario_id: str) -> str:
        """Save chain of thought to logs folder using Pydantic model"""
        from src.models.chain_of_thought_log import ChainOfThoughtLog, ChainOfThoughtStep
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"logs/chain_of_thought_{scenario_id}_{timestamp}.json"

        # Build steps from chain_of_thought utility (assumed to provide list of dicts)
        steps_raw = chain_of_thought.get_full_chain()
        steps = [ChainOfThoughtStep(**step) for step in steps_raw]

        log = ChainOfThoughtLog(
            scenario_id=scenario_id,
            steps=steps,
            summary=chain_of_thought.get_chain_summary(),
            metrics={"execution_results": self.execution_results}
        )

        with open(filename, 'w') as f:
            f.write(log.json(indent=2, default=str))

        return filename


# Global workflow instance
synapse_workflow = SynapseWorkflow()
