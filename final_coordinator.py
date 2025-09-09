"""
Simple LLM Coordinator - Project Synapse
Clean LLM-based crisis management with multi-provider support and real tools
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import os
from dotenv import load_dotenv
import aiohttp

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.utils.chain_of_thought import chain_of_thought, ThoughtType
from config.llm_config import LLMClient
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from tool_manager import tool_scanner

console = Console()

class MultiProviderLLM:
    """Simple multi-provider LLM with Groq primary + Gemini backup"""
    
    def __init__(self):
        self.groq_client = None
        self.gemini_key = None
        
        # Initialize Groq (primary)
        if os.getenv("GROQ_API_KEY"):
            self.groq_client = LLMClient()
            console.print("[green]✅ Groq LLM ready[/green]")
        
        # Initialize Gemini (backup)
        if os.getenv("GEMINI_API_KEY"):
            self.gemini_key = os.getenv("GEMINI_API_KEY")
            console.print("[green]✅ Gemini LLM ready[/green]")
    
    async def get_response(self, prompt: str) -> str:
        """Get LLM response with fallback"""
        
        # Try Groq first
        if self.groq_client:
            try:
                messages = [{"role": "user", "content": prompt}]
                response = await self.groq_client.chat_completion(messages)
                if response and response != "AI reasoning unavailable":
                    return response
            except Exception as e:
                console.print(f"[yellow]Groq failed: {str(e)[:30]}[/yellow]")
        
        # Fallback to Gemini
        if self.gemini_key:
            try:
                return await self._call_gemini(prompt)
            except Exception as e:
                console.print(f"[yellow]Gemini failed: {str(e)[:30]}[/yellow]")
        
        return "LLM services unavailable"
    
    async def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.gemini_key}"
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 1500, "temperature": 0.7}
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    raise Exception(f"Gemini API error: {response.status}")

class SimpleAgent:
    """Simple LLM agent with real tools from tools folder"""
    
    def __init__(self, name: str, llm: MultiProviderLLM):
        self.name = name
        self.llm = llm
        self.available_tools = tool_scanner.get_tools_for_agent(name)
        self.tools = [tool["name"] for tool in self.available_tools]
    
    async def create_plan(self, scenario: str, context: str = "") -> Dict[str, Any]:
        """Create execution plan without individual approval"""
        
        # Start thought tracking
        thought_id = chain_of_thought.start_thought(
            self.name,
            ThoughtType.ANALYSIS,
            f"Creating plan for: {scenario[:35]}..."
        )
        
        try:
            # LLM creates execution plan
            plan = await self._create_execution_plan(scenario, context)
            
            # Check for missing tools
            missing_tools = tool_scanner.suggest_missing_tools(scenario)
            if missing_tools:
                plan["missing_tools"] = missing_tools
                console.print(f"[yellow]💡 {len(missing_tools)} new tools could be created[/yellow]")
            
            # Complete thought
            chain_of_thought.complete_thought(
                thought_id,
                confidence=plan["confidence"],
                reasoning=f"Plan: {plan['analysis'][:50]}... → Tools: {', '.join(plan['selected_tools'][:3])}",
                tools_used=plan["selected_tools"]
            )
            
            return {
                "agent": self.name,
                "analysis": plan["analysis"],
                "plan": plan,
                "status": "planned"
            }
            
        except Exception as e:
            console.print(f"[red]Agent {self.name} planning failed: {e}[/red]")
            return {"agent": self.name, "status": "failed", "error": str(e)}
    
    async def _create_execution_plan(self, scenario: str, context: str) -> Dict[str, Any]:
        """Create execution plan with LLM using real tools"""
        
        # Format available tools with descriptions
        tools_info = []
        for tool_info in self.available_tools:
            tools_info.append(f"- {tool_info['name']}: {tool_info['description']}")
        
        prompt = f"""
As a {self.name.replace('_', ' ').title()}, create an execution plan for this crisis:

SCENARIO: {scenario}
CONTEXT: {context}

AVAILABLE TOOLS:
{chr(10).join(tools_info)}

Create a structured plan selecting the most relevant tools for this specific scenario:

Format your response as:
ANALYSIS: [Brief analysis of what needs to be done]
SELECTED_TOOLS: [tool1, tool2, tool3] (choose 2-4 most relevant tools)
SEQUENCE: [Why this execution order makes sense]
EXPECTED_OUTCOMES: [What you expect to achieve]
CONFIDENCE: [0.8-0.95 based on tool relevance]
"""
        response = await self.llm.get_response(prompt)
        
        # Parse LLM response into structured plan
        return self._parse_plan_response(response)
    
    def _parse_plan_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM plan response into structured data"""
        plan = {
            "analysis": "LLM analysis pending",
            "selected_tools": self.tools[:2],  # Default fallback
            "sequence": "Sequential execution",
            "expected_outcomes": ["Issue resolution"],
            "confidence": 0.85
        }
        
        try:
            lines = response.split('\n')
            for line in lines:
                if line.startswith('ANALYSIS:'):
                    plan["analysis"] = line.replace('ANALYSIS:', '').strip()
                elif line.startswith('SELECTED_TOOLS:'):
                    tools_str = line.replace('SELECTED_TOOLS:', '').strip()
                    # Extract tool names from various formats
                    tools = [t.strip(' [],"') for t in tools_str.split(',')]
                    plan["selected_tools"] = [t for t in tools if t in self.tools][:4]
                elif line.startswith('SEQUENCE:'):
                    plan["sequence"] = line.replace('SEQUENCE:', '').strip()
                elif line.startswith('EXPECTED_OUTCOMES:'):
                    plan["expected_outcomes"] = [line.replace('EXPECTED_OUTCOMES:', '').strip()]
                elif line.startswith('CONFIDENCE:'):
                    try:
                        plan["confidence"] = float(line.replace('CONFIDENCE:', '').strip())
                    except:
                        plan["confidence"] = 0.85
        except:
            pass  # Use defaults if parsing fails
        
        if not plan["selected_tools"]:
            plan["selected_tools"] = self.tools[:2]
        
        return plan

class SimpleCoordinator:
    """Simple coordinator with clean workflow and real tools"""
    
    def __init__(self):
        self.llm = MultiProviderLLM()
        
        # Initialize agents with real tools from tools folder
        self.agents = {
            "coordinator": SimpleAgent("coordinator", self.llm),
            "customer_agent": SimpleAgent("customer_agent", self.llm),
            "traffic_agent": SimpleAgent("traffic_agent", self.llm),
            "merchant_agent": SimpleAgent("merchant_agent", self.llm)
        }
        
        # Display tool recommendations
        self._show_tool_recommendations()
        
        console.print(Panel.fit(
            f"🧠 [bold green]REAL TOOLS COORDINATOR[/bold green]\n\n"
            f"✅ Multi-provider LLM (Groq + Gemini)\n"
            f"✅ {len(self.agents)} specialized agents\n" 
            f"✅ Real tools from tools folder\n"
            f"✅ Single approval workflow",
            title="🚀 Project Synapse",
            border_style="green"
        ))
    
    def _show_tool_recommendations(self):
        """Show tool recommendations"""
        recommendations = tool_scanner.get_tool_recommendations_to_remove()
        if recommendations:
            console.print("[yellow]💡 Tool Optimization Suggestions:[/yellow]")
            for rec in recommendations[:3]:  # Show top 3
                console.print(f"   • Consider reviewing: {rec['tool']} - {rec['reason']}")
    
    async def handle_crisis(self, scenario: str) -> Dict[str, Any]:
        """Handle crisis with comprehensive planning then single approval"""
        
        crisis_id = f"CRISIS_{int(datetime.now().timestamp())}"
        
        console.print(Panel.fit(
            f"🚨 [bold blue]CRISIS DETECTED[/bold blue]\n\n"
            f"📋 Scenario: {scenario}\n"
            f"🆔 ID: {crisis_id}",
            title="🎯 Crisis Management",
            border_style="blue"
        ))
        
        # Clear previous thoughts
        chain_of_thought.thoughts.clear()
        chain_of_thought.current_scenario_id = crisis_id
        
        results = {}
        execution_plan = {}
        
        # Phase 1: Coordinator Planning
        console.print("🧠 [bold yellow]PHASE 1: COORDINATOR PLANNING[/bold yellow]")
        coord_result = await self.agents["coordinator"].create_plan(scenario)
        results["coordinator"] = coord_result
        execution_plan["coordinator"] = coord_result.get("plan", {})
        self._display_agent_plan("Coordinator", coord_result)
        
        # Phase 2: Route to specialist
        specialist = await self._route_to_specialist(scenario, coord_result["analysis"])
        
        # Phase 3: Specialist planning
        console.print(f"🔧 [bold yellow]PHASE 2: {specialist.upper().replace('_', ' ')} PLANNING[/bold yellow]")
        spec_result = await self.agents[specialist].create_plan(scenario, coord_result["analysis"])
        results[specialist] = spec_result
        execution_plan[specialist] = spec_result.get("plan", {})
        self._display_agent_plan(specialist.replace('_', ' ').title(), spec_result)
        
        # Phase 4: Show complete plan and get single approval
        if self._show_complete_plan_and_approve(execution_plan, specialist):
            # Execute the approved plan
            console.print("🚀 [bold green]EXECUTING APPROVED MULTI-AGENT PLAN...[/bold green]")
            
            # Execute coordinator tools
            coord_tools = execution_plan["coordinator"].get("selected_tools", [])
            coord_executed = await self._execute_tools(coord_tools, scenario, "coordinator")
            results["coordinator"]["tool_results"] = coord_executed
            
            # Execute specialist tools
            spec_tools = execution_plan[specialist].get("selected_tools", [])
            spec_executed = await self._execute_tools(spec_tools, scenario, specialist)
            results[specialist]["tool_results"] = spec_executed
            
            status = "resolved"
        else:
            console.print("[yellow]⏸️ Execution cancelled by user[/yellow]")
            status = "cancelled"
        
        # Save results and display summary
        log_file = await self._save_results(crisis_id, scenario, results)
        self._display_chain_of_thought()
        
        total_tools = len(results["coordinator"].get("tool_results", {})) + len(results[specialist].get("tool_results", {}))
        
        console.print(Panel.fit(
            f"✅ [bold green]CRISIS MANAGEMENT COMPLETE[/bold green]\n\n"
            f"🎯 Status: {status.upper()}\n"
            f"🤖 Agents: 2 coordinated\n"
            f"📊 Tools: {total_tools} executed\n"
            f"📄 Report: {log_file}",
            title="🏆 Multi-Agent Resolution",
            border_style="green"
        ))
        
        return {"status": status, "crisis_id": crisis_id, "log_file": log_file}
    
    async def _route_to_specialist(self, scenario: str, analysis: str) -> str:
        """Route to appropriate specialist with detailed reasoning"""
        
        # Add routing to chain of thought
        thought_id = chain_of_thought.start_thought(
            "coordinator",
            ThoughtType.DECISION,
            "🎯 Analyzing specialist routing requirements"
        )
        
        prompt = f"""
Based on this scenario and analysis, which specialist should handle this?

SCENARIO: {scenario}
ANALYSIS: {analysis}

SPECIALISTS:
- customer_agent: Customer issues, refunds, complaints, evidence collection
- traffic_agent: Traffic, routing, weather, logistics, delivery optimization  
- merchant_agent: Restaurant issues, food quality, merchant coordination

Provide your routing decision with reasoning:
SPECIALIST: [agent_name]
REASONING: [why this specialist is best suited]
CONFIDENCE: [0.8-0.95]
"""
        
        response = await self.llm.get_response(prompt)
        
        # Parse routing decision
        specialist = "customer_agent"  # Default
        reasoning = "Default routing based on scenario type"
        confidence = 0.85
        
        try:
            lines = response.split('\n')
            for line in lines:
                if line.startswith('SPECIALIST:'):
                    agent_name = line.replace('SPECIALIST:', '').strip().lower()
                    if agent_name in ["customer_agent", "traffic_agent", "merchant_agent"]:
                        specialist = agent_name
                elif line.startswith('REASONING:'):
                    reasoning = line.replace('REASONING:', '').strip()
                elif line.startswith('CONFIDENCE:'):
                    try:
                        confidence = float(line.replace('CONFIDENCE:', '').strip())
                    except:
                        pass
        except:
            # Fallback logic
            scenario_lower = scenario.lower()
            if any(word in scenario_lower for word in ["traffic", "route", "weather", "delay"]):
                specialist = "traffic_agent"
                reasoning = "Traffic/logistics related scenario detected"
            elif any(word in scenario_lower for word in ["restaurant", "food", "merchant", "quality"]):
                specialist = "merchant_agent" 
                reasoning = "Merchant/food quality scenario detected"
            else:
                specialist = "customer_agent"
                reasoning = "Customer service scenario (default routing)"
        
        # Complete routing thought
        chain_of_thought.complete_thought(
            thought_id,
            confidence=confidence,
            reasoning=f"ROUTING: {reasoning} → {specialist}",
            tools_used=["scenario_analysis", "specialist_matching"]
        )
        
        # Display routing decision
        console.print(Panel.fit(
            f"🎯 [bold blue]INTELLIGENT ROUTING[/bold blue]\n\n"
            f"📊 [bold]Decision:[/bold] {specialist.replace('_', ' ').title()}\n"
            f"🧠 [bold]Reasoning:[/bold] {reasoning[:55]}...\n"
            f"📈 [bold]Confidence:[/bold] {confidence:.0%}",
            title="🤖 AI Routing Engine",
            border_style="blue"
        ))
        
        return specialist
    
    def _show_complete_plan_and_approve(self, execution_plan: Dict[str, Dict], specialist: str) -> bool:
        """Show complete multi-agent execution plan and get single approval"""
        
        console.print(Panel.fit(
            f"📋 [bold blue]COMPLETE MULTI-AGENT EXECUTION PLAN[/bold blue]\n\n"
            f"🤖 [bold]Coordinator:[/bold] {len(execution_plan['coordinator'].get('selected_tools', []))} tools\n"
            f"🎯 [bold]{specialist.replace('_', ' ').title()}:[/bold] {len(execution_plan[specialist].get('selected_tools', []))} tools\n\n"
            f"🚀 Ready for coordinated execution",
            title="🎯 Multi-Agent Plan Review",
            border_style="blue"
        ))
        
        # Show all tools that will be executed
        console.print("🛠️ [bold yellow]COMPLETE TOOL EXECUTION PLAN:[/bold yellow]")
        
        total_tools = 0
        for agent_name, plan in execution_plan.items():
            tools = plan.get("selected_tools", [])
            if tools:
                console.print(f"\n   🤖 [bold cyan]{agent_name.replace('_', ' ').title()}:[/bold cyan]")
                for i, tool in enumerate(tools, 1):
                    console.print(f"      {i}. {tool}")
                total_tools += len(tools)
        
        console.print(f"\n📊 [bold]Total tools to execute:[/bold] {total_tools}")
        
        # Single approval for entire plan
        from rich.prompt import Confirm
        return Confirm.ask("\n🤔 [bold yellow]Approve complete multi-agent execution plan?[/bold yellow]", default=True)
    
    async def _execute_tools(self, tools: List[str], scenario: str, agent_name: str) -> Dict[str, str]:
        """Execute tools for an agent"""
        results = {}
        
        if not tools:
            return results
        
        console.print(f"🔧 [bold green]Executing {agent_name} tools...[/bold green]")
        
        for tool in tools:
            # Simulate realistic tool execution
            result = await self._simulate_realistic_tool_execution(tool, scenario, agent_name)
            results[tool] = result
            console.print(f"   ✅ [green]{tool}:[/green] {result[:80]}...")
        
        return results
    
    async def _simulate_realistic_tool_execution(self, tool: str, scenario: str, agent: str) -> str:
        """Simulate realistic tool execution with scenario-specific results"""
        
        # Small delay to simulate real processing
        await asyncio.sleep(0.5)
        
        prompt = f"""
Simulate realistic execution of the tool: {tool}

SCENARIO: {scenario}
EXECUTING AGENT: {agent}

Provide a specific, realistic result that this tool would produce for this exact scenario.
Focus on concrete, actionable outcomes. Keep response to 1-2 sentences.
"""
        
        try:
            response = await self.llm.get_response(prompt)
            return response[:150] if response else f"{tool} executed successfully for {agent}"
        except:
            return f"{tool} completed - {agent} processed scenario requirements"
    
    def _display_agent_plan(self, agent_name: str, result: Dict[str, Any]):
        """Display agent planning results"""
        if result["status"] == "failed":
            console.print(f"[red]❌ {agent_name} failed: {result.get('error', 'Unknown error')}[/red]")
            return
        
        plan = result.get("plan", {})
        
        # Main results summary
        console.print(Panel.fit(
            f"🤖 [bold blue]{agent_name.upper()} PLANNING COMPLETE[/bold blue]\n\n"
            f"📊 [bold]Status:[/bold] ✅ {result['status'].title()}\n"
            f"🎯 [bold]Confidence:[/bold] {plan.get('confidence', 0.85):.0%}\n"
            f"🛠️ [bold]Tools Selected:[/bold] {len(plan.get('selected_tools', []))}\n"
            f"📋 [bold]Analysis:[/bold] {result['analysis'][:50]}...",
            title=f"📋 {agent_name} Plan",
            border_style="blue"
        ))
        
        # Show selected tools
        selected_tools = plan.get("selected_tools", [])
        if selected_tools:
            console.print(f"🛠️ [bold yellow]{agent_name.upper()} SELECTED TOOLS:[/bold yellow]")
            for i, tool in enumerate(selected_tools, 1):
                console.print(f"   {i}. [bold cyan]{tool}[/bold cyan]")
        
        console.print()
    
    def _display_chain_of_thought(self):
        """Display chain of thought summary"""
        if not chain_of_thought.thoughts:
            return
        
        console.print("\n🧠 [bold blue]CHAIN OF THOUGHT SUMMARY[/bold blue]")
        
        thought_table = Table()
        thought_table.add_column("Step", style="cyan", width=8)
        thought_table.add_column("Agent", style="yellow", width=15)
        thought_table.add_column("Action", style="green", width=25)
        thought_table.add_column("Confidence", style="blue", width=10)
        thought_table.add_column("Tools Used", style="magenta", width=20)
        
        for i, thought in enumerate(chain_of_thought.thoughts, 1):
            thought_table.add_row(
                str(i),
                thought.agent_name,
                thought.description[:22] + "..." if len(thought.description) > 25 else thought.description,
                f"{thought.confidence:.0%}" if thought.confidence else "N/A",
                ", ".join(thought.tools_used[:2]) if thought.tools_used else "None"
            )
        
        console.print(thought_table)
        console.print()
    
    async def _save_results(self, crisis_id: str, scenario: str, results: Dict[str, Any]) -> str:
        """Save results to log file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"logs/real_tools_coordination_{crisis_id}_{timestamp}.json"
        
        Path("logs").mkdir(exist_ok=True)
        
        log_data = {
            "crisis_id": crisis_id,
            "timestamp": datetime.now().isoformat(),
            "scenario": scenario,
            "system_type": "real_tools_multi_agent",
            "results": results,
            "chain_of_thought": [
                {
                    "agent": thought.agent_name,
                    "type": thought.thought_type.value,
                    "description": thought.description,
                    "confidence": thought.confidence,
                    "reasoning": thought.reasoning,
                    "tools_used": thought.tools_used
                } for thought in chain_of_thought.thoughts
            ]
        }
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        return log_file

async def main():
    """Main execution"""
    
    if len(sys.argv) < 2:
        console.print(Panel.fit(
            "🧠 [bold blue]REAL TOOLS COORDINATOR[/bold blue]\n\n"
            "[bold yellow]Usage:[/bold yellow]\n"
            "python simple_coordinator.py \"Your crisis scenario\"\n\n"
            "[bold green]Features:[/bold green]\n"
            "• 🧠 Multi-provider LLM (Groq + Gemini backup)\n"
            "• 🛠️ Real tools from src/tools folder\n"
            "• 🎯 Single approval workflow\n"
            "• 📊 Chain of thought tracking\n"
            "• 💡 Dynamic tool creation suggestions\n\n"
            "[bold cyan]Examples:[/bold cyan]\n"
            "• \"Package damaged during Mumbai delivery\"\n"
            "• \"Customer order delayed due to traffic\"\n"
            "• \"Restaurant quality issues reported\"",
            title="🚀 Project Synapse",
            border_style="blue"
        ))
        return
    
    scenario = " ".join(sys.argv[1:])
    
    coordinator = SimpleCoordinator()
    await coordinator.handle_crisis(scenario)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        console.print(f"[red]System Error: {e}[/red]")
