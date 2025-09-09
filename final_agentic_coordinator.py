"""
Final Working Agentic Coordinator - Project Synapse
Simple version with agent thinking display
"""

import asyncio
import sys
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from config.llm_config import LLMClient
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

class SimpleChainTracker:
    """Simple chain of thought tracker"""
    
    def __init__(self):
        self.scenario_id = None
        self.execution_results = []
        self.chain_of_thought = []
        self.current_step = 0
    
    def start_scenario(self, scenario_id: str):
        self.scenario_id = scenario_id
        self.execution_results = []
        self.chain_of_thought = []
        self.current_step = 0
    
    def add_execution_result(self, agent: str, result_data: Dict[str, Any]):
        self.execution_results.append({"agent": agent, **result_data})
    
    def add_thought(self, agent_name: str, description: str, reasoning: str, 
                   tools_used: List[str] = None, confidence: float = 0.8):
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

chain_tracker = SimpleChainTracker()

class SimpleToolManager:
    """Simple tool manager"""
    
    def __init__(self):
        self.llm_client = LLMClient()
        
        # Project Synapse tools from document
        self.synapse_tools = {
            "initiate_mediation_flow": "Initiate real-time mediation between parties with synchronized interface",
            "collect_evidence": "Guide evidence collection with photos and dynamic questionnaire",
            "analyze_evidence": "Process and analyze collected evidence to determine fault attribution",
            "issue_instant_refund": "Execute instant compensation to customer account",
            "exonerate_driver": "Clear driver from fault and preserve performance rating",
            "log_merchant_packaging_feedback": "Send evidence-backed report to merchant enabling packaging improvements",
            "notify_resolution": "Inform both parties of outcome allowing trip completion without penalty",
            "notify_customer": "Communicate resolution status to customer",
            "check_traffic": "Analyze traffic conditions and delays",
            "calculate_alternative_route": "Compute optimal alternative routes",
            "get_merchant_status": "Check restaurant operational status",
            "contact_recipient_via_chat": "Direct communication with delivery recipient",
            "find_nearby_driver": "Locate available drivers for reassignment",
            "track_driver": "Real-time driver location and status monitoring"
        }
    
    async def get_tools_for_agent(self, agent_type: str, scenario: str) -> List[str]:
        """LLM selects relevant tools for agent based on scenario analysis"""
        
        # Get available tools for agent type
        if agent_type == "customer_agent":
            available_tools = {
                "initiate_mediation_flow": self.synapse_tools["initiate_mediation_flow"],
                "collect_evidence": self.synapse_tools["collect_evidence"], 
                "analyze_evidence": self.synapse_tools["analyze_evidence"],
                "issue_instant_refund": self.synapse_tools["issue_instant_refund"],
                "exonerate_driver": self.synapse_tools["exonerate_driver"],
                "log_merchant_packaging_feedback": self.synapse_tools["log_merchant_packaging_feedback"],
                "notify_resolution": self.synapse_tools["notify_resolution"],
                "contact_recipient_via_chat": self.synapse_tools["contact_recipient_via_chat"]
            }
        elif agent_type == "traffic_agent":
            available_tools = {
                "check_traffic": self.synapse_tools["check_traffic"],
                "calculate_alternative_route": self.synapse_tools["calculate_alternative_route"],
                "find_nearby_driver": self.synapse_tools["find_nearby_driver"],
                "track_driver": self.synapse_tools["track_driver"],
                "notify_resolution": self.synapse_tools["notify_resolution"]
            }
        elif agent_type == "merchant_agent":
            available_tools = {
                "get_merchant_status": self.synapse_tools["get_merchant_status"],
                "log_merchant_packaging_feedback": self.synapse_tools["log_merchant_packaging_feedback"],
                "notify_resolution": self.synapse_tools["notify_resolution"]
            }
        else:
            available_tools = dict(list(self.synapse_tools.items())[:6])
        
        # Let LLM select most relevant tools for this specific scenario
        prompt = f"""
Based on this crisis scenario, select exactly 4 DIFFERENT tools for {agent_type} following Project Synapse methodology:

SCENARIO: {scenario}
AGENT: {agent_type}

AVAILABLE TOOLS:
{chr(10).join([f"- {tool}: {desc}" for tool, desc in available_tools.items()])}

For doorstep disputes with packaging/driver issues, Project Synapse recommends:
• Phase 1: initiate_mediation_flow (start real-time mediation)
• Phase 2: collect_evidence (gather photos/questionnaire)  
• Phase 3: analyze_evidence (determine fault attribution)
• Phase 4: exonerate_driver (if driver not at fault) OR issue_instant_refund (if customer needs compensation)
• Phase 5: log_merchant_packaging_feedback (for packaging issues)
• Phase 6: notify_resolution (inform all parties)

Select exactly 4 DIFFERENT tools that best handle this specific scenario.
For disputes involving packaging and driver fault questions, prioritize tools that:
1. Start mediation 2. Collect evidence 3. Clear driver if innocent 4. Address merchant packaging

Respond with exactly 4 unique tool names, one per line:
"""
        
        try:
            response = await self.llm_client.chat_completion([{"role": "user", "content": prompt}])
            
            selected_tools = []
            seen_tools = set()
            
            for line in response.split('\n'):
                tool_name = line.strip('- ').strip()
                if tool_name in available_tools and tool_name not in seen_tools:
                    selected_tools.append(tool_name)
                    seen_tools.add(tool_name)
            
            # Ensure we have exactly 4 unique tools
            if len(selected_tools) < 4:
                # Add missing tools to reach 4, avoiding duplicates
                for tool in available_tools.keys():
                    if tool not in seen_tools and len(selected_tools) < 4:
                        selected_tools.append(tool)
                        seen_tools.add(tool)
            
            return selected_tools[:4]
            
        except Exception as e:
            console.print(f"[yellow]Tool selection fallback: {e}[/yellow]")
            # Smart fallback based on agent type and scenario - use complete Project Synapse workflow
            if agent_type == "customer_agent":
                # For customer disputes, use full Project Synapse workflow
                if "dispute" in scenario.lower() or "spill" in scenario.lower() or "damage" in scenario.lower():
                    return ["initiate_mediation_flow", "collect_evidence", "analyze_evidence", "exonerate_driver", "log_merchant_packaging_feedback", "notify_resolution"][:4]
                else:
                    return ["collect_evidence", "analyze_evidence", "issue_instant_refund", "notify_resolution"]
            else:
                return list(available_tools.keys())[:4]
    
    async def execute_tool(self, tool_name: str, scenario: str) -> Dict[str, Any]:
        """Execute a single tool"""
        
        # Simulate realistic tool execution
        results = {
            "initiate_mediation_flow": {
                "summary": "Initiated real-time mediation interface on both devices",
                "findings": "Synchronized dispute resolution interface active",
                "actions": "Opened mediation flow, paused order completion"
            },
            "collect_evidence": {
                "summary": "Guided evidence collection from customer and driver",
                "findings": "Photos and questionnaire responses collected",
                "actions": "Collected damage photos, verified packaging seal status"
            },
            "analyze_evidence": {
                "summary": "Processed evidence to determine fault attribution",
                "findings": "Evidence indicates merchant packaging fault",
                "actions": "Analyzed photos, processed questionnaire, determined root cause"
            },
            "issue_instant_refund": {
                "summary": "Processed instant refund of ₹450 to customer account",
                "findings": "Financial compensation approved - refund of ₹450 processed for damaged order",
                "actions": "Executed instant monetary compensation of ₹450, updated customer wallet balance"
            },
            "exonerate_driver": {
                "summary": "Cleared driver from fault in dispute - no financial penalty applied",
                "findings": "Driver exonerated from fault, performance rating preserved, no monetary deductions",
                "actions": "Removed fault attribution, preserved driver rating, prevented financial penalty"
            },
            "log_merchant_packaging_feedback": {
                "summary": "Sent evidence-backed packaging feedback to merchant with potential cost implications",
                "findings": "Packaging quality assessment shows merchant fault - may impact merchant rating and future orders",
                "actions": "Generated detailed report with photos, sent to merchant for quality improvement with business impact assessment"
            },
            "notify_resolution": {
                "summary": "Informed both parties of resolution outcome",
                "findings": "All stakeholders notified of final decision and next steps",
                "actions": "Sent resolution notifications allowing trip completion without penalty"
            }
        }
        
        return results.get(tool_name, {
            "summary": f"Executed {tool_name} for scenario resolution",
            "findings": f"Tool {tool_name} completed successfully",
            "actions": f"Completed {tool_name} operation"
        })

class SimpleAgent:
    """Simple agent with thinking display"""
    
    def __init__(self, agent_name: str, specialization: str, llm_client: LLMClient, tool_manager: SimpleToolManager):
        self.agent_name = agent_name
        self.specialization = specialization
        self.llm_client = llm_client
        self.tool_manager = tool_manager
    
    async def analyze_and_execute(self, scenario: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute with thinking display"""
        
        console.print(f"\n🤖 [bold blue]{self.agent_name.upper().replace('_', ' ')} STARTING ANALYSIS[/bold blue]")
        
        # Show agent thinking
        thinking = await self._get_thinking(scenario)
        console.print(f"💭 [italic yellow]{thinking}[/italic yellow]")
        
        # Get reasoning and action plan
        reasoning = await self._get_reasoning(scenario)
        
        # Display reasoning
        console.print(Panel.fit(
            f"🧠 [bold green]AGENT REASONING[/bold green]\n\n"
            f"{reasoning['analysis']}\n\n"
            f"🎯 [bold]Action Plan:[/bold]\n"
            + "\n".join([f"   {i}. {step}" for i, step in enumerate(reasoning['action_plan'], 1)]) + "\n\n"
            f"📋 [bold]Approach:[/bold] {reasoning['approach']}\n"
            f"⚡ [bold]Urgency:[/bold] {reasoning['urgency'].upper()}\n"
            f"📊 [bold]Confidence:[/bold] {reasoning['confidence']:.0%}",
            title=f"💭 {self.agent_name.replace('_', ' ').title()} Crisis Analysis",
            border_style="blue"
        ))
        
        # Execute tools
        tools = await self.tool_manager.get_tools_for_agent(self.agent_name, scenario)
        tool_results = await self._execute_tools(tools, scenario)
        
        # Generate actions
        actions = [result.get('actions', f'Executed {tool}') for tool, result in tool_results.items()]
        
        # Add to chain tracker
        chain_tracker.add_thought(
            self.agent_name,
            f"Analyzing {scenario[:40]}...",
            reasoning['full_reasoning'],
            tools,
            reasoning['confidence']
        )
        
        chain_tracker.add_execution_result(self.agent_name, {
            "tools_used": tools,
            "actions_taken": actions,
            "confidence": reasoning['confidence'],
            "conclusion": f"{self.agent_name.replace('_', ' ').title()} completed successfully using {len(tools)} tools"
        })
        
        return {
            "agent": self.agent_name,
            "confidence": reasoning['confidence'],
            "tools_used": tools,
            "tool_results": tool_results,
            "actions_taken": actions,
            "status": "completed"
        }
    
    async def _get_thinking(self, scenario: str) -> str:
        """Get agent thinking process"""
        
        thinking_map = {
            "customer_agent": "Customer dispute detected - need to mediate, collect evidence, and resolve fairly...",
            "traffic_agent": "Traffic disruption identified - analyzing routes and optimizing delivery path...",
            "merchant_agent": "Merchant quality issue detected - need to assess operations and provide feedback..."
        }
        
        try:
            prompt = f"You are a {self.agent_name.replace('_', ' ')} analyzing: {scenario}. What's your initial professional assessment in 1 line?"
            response = await self.llm_client.chat_completion([{"role": "user", "content": prompt}])
            return f"{self.agent_name.replace('_', ' ').title()} thinking: {response.strip()[:120]}..."
        except:
            return f"{self.agent_name.replace('_', ' ').title()} thinking: {thinking_map.get(self.agent_name, 'Analyzing scenario requirements...')}"
    
    async def _get_reasoning(self, scenario: str) -> Dict[str, Any]:
        """Get agent reasoning with action plan"""
        
        action_plans = {
            "customer_agent": [
                "Initiate Real-Time Mediation at doorstep",
                "Guide Evidence Collection with photos and questionnaire",
                "Analyze Evidence to determine fault attribution",
                "Execute Instant Resolution with compensation"
            ],
            "traffic_agent": [
                "Assess Traffic Conditions and delays",
                "Calculate Alternative Routes for optimal delivery",
                "Coordinate with Driver for route optimization",
                "Monitor Progress and provide updates"
            ],
            "merchant_agent": [
                "Evaluate Restaurant Operations and capacity",
                "Assess Food Quality and packaging standards",
                "Provide Operational Feedback to merchant",
                "Monitor Improvement Implementation"
            ]
        }
        
        try:
            prompt = f"""
You are a {self.agent_name.replace('_', ' ')} specialist analyzing this crisis scenario:
{scenario}

Provide professional analysis considering Project Synapse methodology:

ANALYSIS: [Detailed analysis of the situation, stakeholders, and impact]
APPROACH: [Your systematic resolution methodology]  
URGENCY: [low/medium/high/critical based on scenario severity]
CONFIDENCE: [0.8-0.95 based on scenario clarity and your expertise]

Focus on evidence-based resolution and stakeholder satisfaction.
"""
            response = await self.llm_client.chat_completion([{"role": "user", "content": prompt}])
            
            # Parse response
            analysis = "Professional crisis analysis completed"
            approach = "Systematic resolution methodology"
            urgency = "medium"
            confidence = 0.87
            
            for line in response.split('\n'):
                if line.startswith('ANALYSIS:'):
                    analysis = line.replace('ANALYSIS:', '').strip()
                elif line.startswith('APPROACH:'):
                    approach = line.replace('APPROACH:', '').strip()
                elif line.startswith('URGENCY:'):
                    urgency = line.replace('URGENCY:', '').strip()
                elif line.startswith('CONFIDENCE:'):
                    try:
                        confidence = float(line.replace('CONFIDENCE:', '').strip())
                    except:
                        pass
            
            return {
                "analysis": analysis,
                "action_plan": action_plans.get(self.agent_name, ["Assess situation", "Deploy solution", "Execute resolution", "Monitor outcome"]),
                "approach": approach,
                "urgency": urgency,
                "confidence": confidence,
                "full_reasoning": response
            }
            
        except:
            return {
                "analysis": f"Professional {self.agent_name.replace('_', ' ')} analysis of crisis scenario",
                "action_plan": action_plans.get(self.agent_name, ["Assess situation", "Deploy solution"]),
                "approach": "Expert crisis resolution methodology",
                "urgency": "medium",
                "confidence": 0.87,
                "full_reasoning": f"{self.agent_name} crisis analysis completed"
            }
    
    async def _execute_tools(self, tools: List[str], scenario: str) -> Dict[str, Any]:
        """Execute tools with display"""
        
        console.print(f"\n🛠️ [bold yellow]{self.agent_name.upper().replace('_', ' ')} TOOL EXECUTION[/bold yellow]")
        console.print(f"🛠️ Executing {len(tools)} tools...")
        
        results = {}
        
        for i, tool in enumerate(tools, 1):
            console.print(f"   🔧 [{i}/{len(tools)}] Executing {tool}...")
            result = await self.tool_manager.execute_tool(tool, scenario)
            results[tool] = result
            console.print(f"   ✅ {tool}: {result.get('summary', 'Completed successfully')}")
        
        console.print(f"🎯 All {len(tools)} tools executed successfully!")
        return results

class FinalCoordinator:
    """Final coordinator with thinking display"""
    
    def __init__(self):
        self.llm_client = LLMClient()
        self.tool_manager = SimpleToolManager()
        
        self.agents = {
            "customer_agent": "Customer satisfaction, dispute resolution, evidence analysis, refund processing",
            "traffic_agent": "Route optimization, traffic analysis, weather assessment, driver coordination",
            "merchant_agent": "Restaurant operations, food quality, merchant relations, supply chain"
        }
        
        console.print(Panel.fit(
            "🎯 [bold green]FINAL AGENTIC COORDINATOR INITIALIZED[/bold green]\n\n"
            "✅ Enhanced with agent thinking display\n"
            "✅ Project Synapse style action plans\n"
            "✅ Specific tool execution workflow\n"
            "✅ Complete chain of thought tracking",
            title="🚀 Project Synapse - Final System",
            border_style="green"
        ))
    
    async def handle_crisis(self, scenario: str) -> Dict[str, Any]:
        """Handle crisis with final workflow"""
        
        crisis_id = f"LIVE_{int(datetime.now().timestamp())}"
        
        console.print(Panel.fit(
            f"🚨 [bold red]CRISIS SCENARIO INITIATED[/bold red]\n\n"
            f"📋 [bold]Scenario:[/bold] {scenario}\n"
            f"🆔 [bold]Crisis ID:[/bold] {crisis_id}\n"
            f"🎯 [bold]System:[/bold] Final Agentic Coordination",
            title="🚨 Crisis Management Started",
            border_style="red"
        ))
        
        # Initialize tracking
        chain_tracker.start_scenario(crisis_id)
        
        # Phase 1: Coordinator Analysis
        console.print("\n🧠 [bold yellow]PHASE 1: COORDINATOR ANALYSIS & ROUTING[/bold yellow]")
        routing = await self._coordinator_routing(scenario)
        
        # Phase 2: Agent Execution
        selected_agent = routing['routing_decision']
        console.print(f"\n🎯 [bold yellow]PHASE 2: {selected_agent.upper().replace('_', ' ')} EXECUTION[/bold yellow]")
        
        agent = SimpleAgent(selected_agent, self.agents[selected_agent], self.llm_client, self.tool_manager)
        agent_result = await agent.analyze_and_execute(scenario, {"routing_info": routing})
        
        # Phase 3: Approval
        approval = await self._get_approval(agent_result, scenario)
        
        # Phase 4: Results
        log_file = await self._save_results(crisis_id, scenario, routing, agent_result, approval)
        await self._display_final_results(crisis_id, scenario, routing, agent_result, approval, log_file)
        
        return {"status": "RESOLVED", "crisis_id": crisis_id, "log_file": log_file}
    
    async def _coordinator_routing(self, scenario: str) -> Dict[str, Any]:
        """Coordinator analysis and routing"""
        
        console.print("🔍 [bold blue]Coordinator analyzing scenario...[/bold blue]")
        
        # Coordinator thinking
        try:
            thinking_prompt = f"You are a Crisis Coordinator analyzing: {scenario}. What type of crisis is this and which specialist is needed? Answer in 1 line."
            thinking_response = await self.llm_client.chat_completion([{"role": "user", "content": thinking_prompt}])
            coord_thinking = f"Coordinator thinking: {thinking_response.strip()[:120]}..."
        except:
            coord_thinking = "Coordinator thinking: Analyzing crisis type and determining optimal specialist routing..."
        
        console.print(f"💭 [italic cyan]{coord_thinking}[/italic cyan]")
        
        # Routing logic
        if any(word in scenario.lower() for word in ["customer", "dispute", "refund", "damage", "complaint"]):
            routing_decision = "customer_agent"
        elif any(word in scenario.lower() for word in ["traffic", "route", "driver", "delivery", "jam"]):
            routing_decision = "traffic_agent"
        elif any(word in scenario.lower() for word in ["restaurant", "merchant", "food", "kitchen", "packaging"]):
            routing_decision = "merchant_agent"
        else:
            routing_decision = "customer_agent"
        
        confidence = 0.85
        
        # Display routing
        console.print(Panel.fit(
            f"🎯 [bold green]ROUTING DECISION[/bold green]\n\n"
            f"📊 [bold]Analysis:[/bold] Crisis type identified for specialist handling\n"
            f"🤖 [bold]Routing to:[/bold] {routing_decision}\n"
            f"📈 [bold]Confidence:[/bold] {confidence:.0%}\n"
            f"💭 [bold]Reasoning:[/bold] Optimal specialist for this crisis type",
            title="📡 Coordinator Routing",
            border_style="green"
        ))
        
        # Add to chain tracker
        chain_tracker.add_thought(
            "coordinator",
            "Analyzing scenario and routing decision",
            f"COORDINATOR ANALYSIS: Crisis type identified. Routing: {routing_decision}. Confidence: {confidence}",
            [],
            confidence
        )
        
        chain_tracker.add_execution_result("coordinator", {
            "routing_decision": routing_decision,
            "confidence": confidence,
            "conclusion": f"Analyzed scenario and routed to {routing_decision}"
        })
        
        return {
            "routing_decision": routing_decision,
            "confidence": confidence,
            "analysis": "Crisis type identified for specialist handling"
        }
    
    async def _get_approval(self, agent_result: Dict, scenario: str) -> Dict[str, Any]:
        """Get human approval if needed"""
        
        # Check for financial keywords in scenario
        financial_keywords = ["refund", "money", "payment", "compensation", "financial", "damage", "spill"]
        scenario_needs_approval = any(keyword in scenario.lower() for keyword in financial_keywords)
        
        # Check for financial tools used
        financial_tools = ["issue_instant_refund", "exonerate_driver", "log_merchant_packaging_feedback"]
        tools_used = agent_result.get('tools_used', [])
        tools_need_approval = any(tool in tools_used for tool in financial_tools)
        
        # Check tool results for financial mentions
        tool_results = agent_result.get('tool_results', {})
        results_mention_financial = False
        for tool, result in tool_results.items():
            result_text = str(result).lower()
            if any(keyword in result_text for keyword in financial_keywords + ["₹", "rupees", "cost"]):
                results_mention_financial = True
                break
        
        needs_approval = scenario_needs_approval or tools_need_approval or results_mention_financial
        
        if needs_approval:
            console.print(Panel.fit(
                f"💰 [bold yellow]HUMAN APPROVAL REQUIRED[/bold yellow]\n\n"
                f"🎯 [bold]Agent:[/bold] {agent_result['agent']}\n"
                f"📊 [bold]Confidence:[/bold] {agent_result['confidence']:.0%}\n"
                f"🛠️ [bold]Tools Used:[/bold] {len(agent_result.get('tools_used', []))}\n"
                f"💳 [bold]Financial Impact:[/bold] Detected\n\n"
                f"[bold green]Approve agent's financial decisions?[/bold green]",
                title="🔐 Financial Approval Required",
                border_style="yellow"
            ))
            
            approved = Confirm.ask("💰 [bold yellow]Approve financial actions?[/bold yellow]", default=True)
            return {"approval_required": True, "approved": approved, "approval_type": "financial"}
        else:
            return {"approval_required": False, "approved": True, "approval_type": "automatic"}
    
    async def _save_results(self, crisis_id: str, scenario: str, routing: Dict, agent_result: Dict, approval: Dict) -> str:
        """Save results to chain of thought file"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"logs/chain_of_thought_{crisis_id}_{timestamp}.json"
        
        Path("logs").mkdir(exist_ok=True)
        
        log_data = {
            "scenario_id": crisis_id,
            "timestamp": datetime.now().isoformat(),
            "execution_results": chain_tracker.execution_results,
            "chain_of_thought": chain_tracker.chain_of_thought,
            "summary": {
                "total_steps": len(chain_tracker.chain_of_thought),
                "completed_steps": len(chain_tracker.chain_of_thought),
                "average_confidence": sum([r.get('confidence', 0.8) for r in chain_tracker.execution_results]) / len(chain_tracker.execution_results),
                "agents_involved": [r['agent'] for r in chain_tracker.execution_results],
                "thought_types": ["analysis"]
            },
            "scenario": scenario,
            "financial_approval": approval
        }
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        return log_file
    
    async def _display_final_results(self, crisis_id: str, scenario: str, routing: Dict, agent_result: Dict, approval: Dict, log_file: str):
        """Display final results with Project Synapse style outcomes"""
        
        # Performance table
        console.print("\n📊 [bold blue]AGENT PERFORMANCE SUMMARY[/bold blue]")
        
        performance_table = Table()
        performance_table.add_column("Agent", style="cyan", width=15)
        performance_table.add_column("Role", style="yellow", width=20)
        performance_table.add_column("Confidence", style="green", width=12)
        performance_table.add_column("Tools Used", style="magenta", width=10)
        performance_table.add_column("Status", style="bright_green", width=12)
        
        performance_table.add_row("Coordinator", "Analysis & Routing", f"{routing['confidence']:.0%}", "0", "✅ Completed")
        performance_table.add_row(
            agent_result['agent'].replace('_', ' ').title(),
            "Execution & Resolution",
            f"{agent_result['confidence']:.0%}",
            str(len(agent_result.get('tools_used', []))),
            "✅ Completed"
        )
        
        console.print(performance_table)
        
        # Actions summary
        console.print("\n📋 [bold blue]ACTIONS TAKEN SUMMARY[/bold blue]")
        actions = agent_result.get('actions_taken', [])
        for i, action in enumerate(actions[:5], 1):
            console.print(f"   {i}. {action}")
        
        # Generate specific resolution statements
        resolution_statements = await self._get_resolution_statements(agent_result, scenario)
        
        # Final outcome box
        status = "CRISIS SUCCESSFULLY RESOLVED" if approval.get('approved', True) else "CRISIS ANALYZED - PENDING APPROVAL"
        status_color = "green" if approval.get('approved', True) else "yellow"
        
        console.print(Panel.fit(
            f"🏆 [bold {status_color}]{status}[/bold {status_color}]\n\n" +
            "\n".join([f"✅ {stmt}" for stmt in resolution_statements]) + f"\n\n"
            f"🆔 [bold]Crisis ID:[/bold] {crisis_id}\n"
            f"📊 [bold]Overall Confidence:[/bold] {((routing['confidence'] + agent_result['confidence']) / 2):.0%}\n"
            f"📄 [bold]Report:[/bold] {log_file.split('/')[-1]}\n\n"
            f"[bold green]🎯 Multi-agent coordination successfully completed![/bold green]" if approval.get('approved', True) else
            f"[bold yellow]⏸️ Analysis complete - awaiting execution approval.[/bold yellow]",
            title="🚀 Project Synapse - Crisis Resolution Complete",
            border_style=status_color
        ))
    
    async def _get_resolution_statements(self, agent_result: Dict, scenario: str) -> List[str]:
        """Generate specific resolution statements"""
        
        tools_used = agent_result.get('tools_used', [])
        agent_type = agent_result.get('agent', '')
        
        # Generate statements based on tools used
        statements = []
        
        if 'initiate_mediation_flow' in tools_used:
            statements.append("Initiated real-time mediation interface for at-doorstep resolution")
        if 'collect_evidence' in tools_used:
            statements.append("Guided evidence collection with photos and dynamic questionnaire")
        if 'analyze_evidence' in tools_used:
            statements.append("Processed evidence to determine fault attribution accurately")
        if 'issue_instant_refund' in tools_used:
            statements.append("Executed instant refund compensation to customer account")
        if 'exonerate_driver' in tools_used:
            statements.append("Cleared driver from fault and preserved performance rating")
        if 'log_merchant_packaging_feedback' in tools_used:
            statements.append("Sent evidence-backed packaging report to merchant for quality improvements")
        if 'notify_resolution' in tools_used:
            statements.append("Informed both parties of outcome enabling trip completion without penalty")
        
        # Add generic statements if no specific tools
        if not statements:
            statements = [
                f"Applied {agent_type.replace('_', ' ')} expertise to analyze crisis scenario",
                f"Deployed systematic resolution approach for stakeholder satisfaction",
                f"Coordinated multi-party communication for optimal outcome"
            ]
        
        return statements[:4]

async def main():
    """Main execution"""
    
    if len(sys.argv) < 2:
        console.print(Panel.fit(
            "🤖 [bold blue]FINAL AGENTIC COORDINATOR[/bold blue]\n\n"
            "[bold yellow]Usage:[/bold yellow]\n"
            "python final_agentic_coordinator.py \"Your crisis scenario\"\n\n"
            "[bold green]Enhanced Features:[/bold green]\n"
            "• 🧠 Agent thinking display (1-2 lines)\n"
            "• 🎯 Project Synapse style action plans\n"
            "• 🛠️ Specific tool execution workflow\n"
            "• 📊 Complete chain of thought tracking\n"
            "• 💰 Human approval for financial decisions\n\n"
            "[bold cyan]Example Scenarios:[/bold cyan]\n"
            "• \"At doorstep dispute over spilled drink packaging\"\n"
            "• \"Customer needs urgent refund for damaged order\"\n"
            "• \"Traffic jam causing delivery delays in Mumbai\"",
            title="🚀 Final AI Crisis Management",
            border_style="blue"
        ))
        return
    
    scenario = " ".join(sys.argv[1:])
    
    coordinator = FinalCoordinator()
    await coordinator.handle_crisis(scenario)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        console.print(f"[red]System Error: {e}[/red]")
