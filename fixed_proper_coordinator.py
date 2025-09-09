"""
Fixed Proper Agentic Coordinator - Project Synapse
Reverted to working version with just duplicate tool fix and proper financial approval
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

class DynamicToolManager:
    """Manages existing and dynamically created tools"""
    
    def __init__(self):
        self.tools_folder = Path("src/tools")
        self.existing_tools = self._load_existing_tools()
        self.llm_client = LLMClient()
    
    def _load_existing_tools(self) -> Dict[str, str]:
        """Load existing tools from tools folder"""
        existing = {}
        if self.tools_folder.exists():
            for tool_file in self.tools_folder.glob("*.py"):
                if tool_file.name != "__init__.py":
                    tool_name = tool_file.stem
                    # Read tool description from file
                    try:
                        with open(tool_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # Extract description from docstring or comments
                            if '"""' in content:
                                desc_start = content.find('"""') + 3
                                desc_end = content.find('"""', desc_start)
                                if desc_end != -1:
                                    existing[tool_name] = content[desc_start:desc_end].strip().split('\n')[0]
                                else:
                                    existing[tool_name] = f"Existing tool: {tool_name}"
                            else:
                                existing[tool_name] = f"Existing tool: {tool_name}"
                    except:
                        existing[tool_name] = f"Existing tool: {tool_name}"
        
        # Add some known tools if folder is empty
        if not existing:
            existing.update({
                "collect_evidence": "Collect photos, documents, and customer statements",
                "analyze_evidence": "Analyze collected evidence for damage assessment",
                "issue_instant_refund": "Process immediate refund for customer",
                "check_traffic": "Analyze real-time traffic conditions",
                "calculate_alternative_route": "Compute optimal alternative routes",
                "get_merchant_status": "Check restaurant operational status",
                "notify_customer": "Send notifications to customer",
                "contact_recipient_via_chat": "Direct communication with customer",
                "initiate_mediation_flow": "Start structured mediation between parties",
                "exonerate_driver": "Clear driver from fault in case of external issues",
                "log_merchant_packaging_feedback": "Record packaging quality feedback for merchant"
            })
        
        return existing
    
    async def get_required_tools(self, agent_type: str, scenario: str, reasoning: str) -> List[str]:
        """Get required tools for agent based on scenario and reasoning"""
        
        # Filter existing tools by agent type
        relevant_existing = self._filter_tools_by_agent(agent_type)
        
        prompt = f"""
Agent: {agent_type}
Scenario: {scenario}
Agent Reasoning: {reasoning}

Available existing tools:
{chr(10).join([f"- {tool}: {desc}" for tool, desc in relevant_existing.items()])}

Based on the agent's reasoning and scenario, select 3-4 most relevant existing tools.
IMPORTANT: Select DIFFERENT tools - no duplicates. Each tool should serve a different purpose.

Format response:
SELECTED_TOOLS:
- tool_name_1
- tool_name_2
- tool_name_3
- tool_name_4
"""
        
        try:
            response = await self.llm_client.chat_completion([{"role": "user", "content": prompt}])
            
            existing_selected = []
            seen_tools = set()
            
            lines = response.split('\n')
            
            for line in lines:
                line = line.strip()
                if line.startswith('- '):
                    tool_name = line.replace('- ', '').strip()
                    if tool_name in relevant_existing and tool_name not in seen_tools:
                        existing_selected.append(tool_name)
                        seen_tools.add(tool_name)
            
            # Ensure we have at least 3-4 unique tools
            if len(existing_selected) < 3:
                for tool in relevant_existing.keys():
                    if tool not in seen_tools and len(existing_selected) < 4:
                        existing_selected.append(tool)
                        seen_tools.add(tool)
            
            return existing_selected[:4]  # Limit to 4 tools
            
        except Exception as e:
            console.print(f"[yellow]Tool selection fallback: {e}[/yellow]")
            return list(relevant_existing.keys())[:3]
    
    def _filter_tools_by_agent(self, agent_type: str) -> Dict[str, str]:
        """Filter tools relevant to agent type"""
        
        if agent_type == "customer_agent":
            keywords = ["customer", "evidence", "refund", "contact", "chat", "mediation", "collect", "analyze", "packaging", "driver"]
        elif agent_type == "traffic_agent":
            keywords = ["traffic", "route", "driver", "alternative", "navigation", "tracking"]
        elif agent_type == "merchant_agent":
            keywords = ["merchant", "restaurant", "status", "packaging", "food", "kitchen"]
        else:
            return self.existing_tools
        
        filtered = {}
        for tool, desc in self.existing_tools.items():
            if any(keyword in tool.lower() or keyword in desc.lower() for keyword in keywords):
                filtered[tool] = desc
        
        # If no specific tools found, return some general ones
        if not filtered:
            general_tools = list(self.existing_tools.items())[:4]
            filtered = dict(general_tools)
        
        return filtered
    
    async def _create_new_tool(self, tool_name: str, tool_desc: str, agent_type: str, scenario: str):
        """Create new tool dynamically"""
        
        console.print(f"🛠️ [bold yellow]CREATING NEW TOOL:[/bold yellow] {tool_name}")
        console.print(f"   📋 Description: {tool_desc}")
        console.print(f"   🎯 For agent: {agent_type}")
        
        # Ensure tools directory exists
        self.tools_folder.mkdir(parents=True, exist_ok=True)
        
        # Generate tool code
        tool_code = f'''"""
{tool_desc}
Dynamically created for {agent_type} handling: {scenario[:50]}...
"""

def {tool_name}(scenario_context: dict = None) -> dict:
    """
    {tool_desc}
    
    Args:
        scenario_context: Context from the current scenario
    
    Returns:
        dict: Tool execution results
    """
    
    # Simulated tool execution
    result = {{
        "tool_name": "{tool_name}",
        "status": "success",
        "description": "{tool_desc}",
        "findings": f"Executed {{'{tool_name}'}} for scenario requirements",
        "actions_taken": [f"Completed {{'{tool_name}'}} operation"],
        "confidence": 0.85,
        "created_dynamically": True
    }}
    
    return result

# Tool metadata
TOOL_METADATA = {{
    "name": "{tool_name}",
    "description": "{tool_desc}",
    "agent_type": "{agent_type}",
    "created_at": "{datetime.now().isoformat()}",
    "dynamic": True
}}
'''
        
        # Save tool file
        tool_file = self.tools_folder / f"{tool_name}.py"
        with open(tool_file, 'w', encoding='utf-8') as f:
            f.write(tool_code)
        
        # Add to existing tools
        self.existing_tools[tool_name] = tool_desc
        
        console.print(f"   ✅ [green]Tool created:[/green] src/tools/{tool_name}.py")

class ProperAgenticAgent:
    """Proper agent that shows reasoning then executes tools"""
    
    def __init__(self, agent_name: str, specialization: str, llm_client: LLMClient, tool_manager: DynamicToolManager):
        self.agent_name = agent_name
        self.specialization = specialization
        self.llm_client = llm_client
        self.tool_manager = tool_manager
    
    async def analyze_and_execute(self, scenario: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Proper agent execution with reasoning first, then tools"""
        
        console.print(f"\n🤖 [bold blue]{self.agent_name.upper().replace('_', ' ')} STARTING ANALYSIS[/bold blue]")
        
        # Show agent thinking process
        agent_thinking = await self._get_agent_thinking(scenario)
        console.print(f"💭 [italic yellow]{agent_thinking}[/italic yellow]")
        
        # Step 1: Agent reasoning
        reasoning = await self._get_agent_reasoning(scenario, context or {})
        
        # Display reasoning
        console.print(Panel.fit(
            f"🧠 [bold green]AGENT REASONING[/bold green]\n\n"
            f"{reasoning['analysis']}\n\n"
            f"🎯 [bold]Approach:[/bold] {reasoning['approach']}\n"
            f"📊 [bold]Confidence:[/bold] {reasoning['confidence']:.0%}",
            title=f"💭 {self.agent_name.replace('_', ' ').title()} Analysis",
            border_style="blue"
        ))
        
        # Step 2: Get required tools
        required_tools = await self.tool_manager.get_required_tools(
            self.agent_name, scenario, reasoning['analysis']
        )
        
        # Step 3: Execute tools
        console.print(f"\n🛠️ [bold yellow]{self.agent_name.upper().replace('_', ' ')} TOOL EXECUTION[/bold yellow]")
        tool_results = await self._execute_tools(required_tools, scenario, context or {})
        
        # Step 4: Generate actions taken
        actions_taken = await self._generate_actions(tool_results, reasoning)
        
        # Step 5: Add to chain of thought
        chain_tracker.add_thought(
            self.agent_name,
            f"Analyzing {scenario[:40]}..." if len(scenario) > 40 else scenario,
            reasoning['full_reasoning'],
            required_tools,
            reasoning['confidence']
        )
        
        # Step 6: Add execution result
        chain_tracker.add_execution_result(self.agent_name, {
            "tools_used": required_tools,
            "actions_taken": actions_taken,
            "confidence": reasoning['confidence'],
            "conclusion": f"{self.agent_name.replace('_', ' ').title()} completed successfully using {len(required_tools)} tools"
        })
        
        return {
            "agent": self.agent_name,
            "confidence": reasoning['confidence'],
            "reasoning": reasoning,
            "tools_used": required_tools,
            "tool_results": tool_results,
            "actions_taken": actions_taken,
            "status": "completed"
        }
    
    async def _get_agent_thinking(self, scenario: str) -> str:
        """Get short agent thinking process (1-2 lines)"""
        
        prompt = f"""
You are a {self.agent_name.replace('_', ' ')} specialist analyzing this scenario:
{scenario}

Show your initial thinking process in 1-2 concise lines. What's your first professional assessment?
Examples:
- "This appears to be a customer dispute requiring evidence collection and mediation..."
- "Traffic congestion detected - need to assess alternative routes and driver safety..."
- "Merchant packaging issue identified - requires quality assessment and feedback..."

Respond with just 1-2 lines of your professional thinking:
"""
        
        try:
            response = await self.llm_client.chat_completion([{"role": "user", "content": prompt}])
            # Clean and limit the response
            thinking = response.strip().replace('\n', ' ')[:150]
            return f"{self.agent_name.replace('_', ' ').title()} thinking: {thinking}"
        except:
            return f"{self.agent_name.replace('_', ' ').title()} thinking: Analyzing scenario requirements and determining optimal resolution approach..."

    async def _get_agent_reasoning(self, scenario: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed agent reasoning"""
        
        console.print(f"🧠 [cyan]Getting {self.agent_name} reasoning...[/cyan]")
        
        prompt = f"""
You are a {self.agent_name.replace('_', ' ')} specialist with expertise in: {self.specialization}

Analyze this crisis scenario and provide your professional reasoning:
SCENARIO: {scenario}
CONTEXT: {json.dumps(context, indent=2)}

Provide detailed reasoning in this format:
ANALYSIS: [Your detailed analysis of the situation]
APPROACH: [Your approach to solving this]
URGENCY: [low/medium/high/critical]
CONFIDENCE: [0.7-0.95]
REASONING: [Complete reasoning for chain of thought]
"""
        
        try:
            response = await self.llm_client.chat_completion([{"role": "user", "content": prompt}])
            
            reasoning = {
                "analysis": "Professional analysis of the scenario",
                "approach": "Systematic resolution approach",
                "urgency": "medium",
                "confidence": 0.85,
                "full_reasoning": response
            }
            
            # Parse structured response
            lines = response.split('\n')
            for line in lines:
                if line.startswith('ANALYSIS:'):
                    reasoning["analysis"] = line.replace('ANALYSIS:', '').strip()
                elif line.startswith('APPROACH:'):
                    reasoning["approach"] = line.replace('APPROACH:', '').strip()
                elif line.startswith('URGENCY:'):
                    reasoning["urgency"] = line.replace('URGENCY:', '').strip()
                elif line.startswith('CONFIDENCE:'):
                    try:
                        reasoning["confidence"] = float(line.replace('CONFIDENCE:', '').strip())
                    except:
                        pass
                elif line.startswith('REASONING:'):
                    reasoning["full_reasoning"] = line.replace('REASONING:', '').strip()
            
            return reasoning
            
        except Exception as e:
            return {
                "analysis": f"Professional {self.agent_name} analysis of the scenario",
                "approach": "Systematic problem-solving approach",
                "urgency": "medium", 
                "confidence": 0.8,
                "full_reasoning": f"{self.agent_name} analysis completed"
            }
    
    async def _execute_tools(self, tools: List[str], scenario: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tools with progress display"""
        
        results = {}
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=False
        ) as progress:
            
            for tool in tools:
                task = progress.add_task(f"🔧 Executing {tool}...", total=100)
                
                # Simulate tool execution
                result = await self._simulate_tool_execution(tool, scenario, context)
                results[tool] = result
                
                progress.update(task, completed=100)
                console.print(f"   ✅ [green]{tool}:[/green] {result.get('summary', 'Completed successfully')}")
        
        return results
    
    async def _simulate_tool_execution(self, tool_name: str, scenario: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate realistic tool execution"""
        
        prompt = f"""
Execute tool: {tool_name}
Scenario: {scenario}
Context: {json.dumps(context, indent=2)}

Simulate realistic execution results for this tool in this specific scenario.
Be specific and actionable.

Format:
SUMMARY: [One line summary]
FINDINGS: [Specific findings]
ACTIONS: [Actions completed]
CONFIDENCE: [0.7-0.95]
"""
        
        try:
            response = await self.llm_client.chat_completion([{"role": "user", "content": prompt}])
            
            result = {
                "summary": f"Executed {tool_name} successfully",
                "findings": f"Tool {tool_name} completed analysis",
                "actions": [f"Completed {tool_name} operation"],
                "confidence": 0.85
            }
            
            # Parse response
            lines = response.split('\n')
            for line in lines:
                if line.startswith('SUMMARY:'):
                    result["summary"] = line.replace('SUMMARY:', '').strip()
                elif line.startswith('FINDINGS:'):
                    result["findings"] = line.replace('FINDINGS:', '').strip()
                elif line.startswith('ACTIONS:'):
                    result["actions"] = [line.replace('ACTIONS:', '').strip()]
                elif line.startswith('CONFIDENCE:'):
                    try:
                        result["confidence"] = float(line.replace('CONFIDENCE:', '').strip())
                    except:
                        pass
            
            return result
            
        except:
            return {
                "summary": f"Executed {tool_name} for scenario",
                "findings": f"Tool {tool_name} processed successfully", 
                "actions": [f"Completed {tool_name}"],
                "confidence": 0.8
            }
    
    async def _generate_actions(self, tool_results: Dict[str, Any], reasoning: Dict[str, Any]) -> List[str]:
        """Generate list of actions taken by agent"""
        
        actions = []
        for tool, result in tool_results.items():
            if isinstance(result.get('actions'), list):
                actions.extend(result['actions'])
            else:
                actions.append(f"Executed {tool}: {result.get('summary', 'completed')}")
        
        return actions[:5]  # Limit to 5 actions

class ProperCoordinator:
    """Coordinator that only analyzes and routes (no tool execution)"""
    
    def __init__(self):
        self.llm_client = LLMClient()
        
        # Available agents
        self.agents = {
            "customer_agent": "Customer satisfaction, dispute resolution, evidence analysis, refund processing",
            "traffic_agent": "Route optimization, traffic analysis, weather assessment, driver coordination", 
            "merchant_agent": "Restaurant operations, food quality, merchant relations, supply chain"
        }
        
        console.print(Panel.fit(
            "🎯 [bold green]PROPER AGENTIC COORDINATOR INITIALIZED[/bold green]\n\n"
            "✅ Coordinator: Analysis and routing only\n"
            "✅ Agents: Full reasoning and tool execution\n"
            "✅ Dynamic tool creation\n"
            "✅ Proper chain of thought tracking\n"
            "✅ Human approval workflow",
            title="🚀 Project Synapse - Proper Agentic System",
            border_style="green"
        ))
    
    async def handle_crisis(self, scenario: str) -> Dict[str, Any]:
        """Handle crisis with proper agentic workflow"""
        
        crisis_id = f"LIVE_{int(datetime.now().timestamp())}"
        
        console.print(Panel.fit(
            f"🚨 [bold red]CRISIS SCENARIO INITIATED[/bold red]\n\n"
            f"📋 [bold]Scenario:[/bold] {scenario}\n"
            f"🆔 [bold]Crisis ID:[/bold] {crisis_id}\n"
            f"🎯 [bold]System:[/bold] Proper Agentic Coordination",
            title="🚨 Crisis Management Started",
            border_style="red"
        ))
        
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
        await self._display_final_output(crisis_id, scenario, routing_result, agent_result, approval_result, log_file)
        
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
        
        prompt = f"""
You are the Crisis Coordinator. Your ONLY job is to analyze scenarios and route to the right specialist agent.

SCENARIO: {scenario}

AVAILABLE AGENTS:
- customer_agent: {self.agents['customer_agent']}
- traffic_agent: {self.agents['traffic_agent']}  
- merchant_agent: {self.agents['merchant_agent']}

Analyze the scenario and determine which agent should handle it.

Format response:
ANALYSIS: [Your analysis of the scenario type and requirements]
ROUTING_DECISION: [agent_name]
CONFIDENCE: [0.7-0.95]
REASONING: [Why this agent is the best choice]
"""
        
        try:
            response = await self.llm_client.chat_completion([{"role": "user", "content": prompt}])
            
            # Parse response
            analysis = "Scenario analysis completed"
            routing_decision = "customer_agent"  # Default
            confidence = 0.8
            reasoning = "Standard routing decision"
            
            lines = response.split('\n')
            for line in lines:
                if line.startswith('ANALYSIS:'):
                    analysis = line.replace('ANALYSIS:', '').strip()
                elif line.startswith('ROUTING_DECISION:'):
                    agent_name = line.replace('ROUTING_DECISION:', '').strip()
                    if agent_name in self.agents:
                        routing_decision = agent_name
                elif line.startswith('CONFIDENCE:'):
                    try:
                        confidence = float(line.replace('CONFIDENCE:', '').strip())
                    except:
                        pass
                elif line.startswith('REASONING:'):
                    reasoning = line.replace('REASONING:', '').strip()
            
            # Display routing decision
            console.print(Panel.fit(
                f"🎯 [bold green]ROUTING DECISION[/bold green]\n\n"
                f"📊 [bold]Analysis:[/bold] {analysis[:60]}...\n"
                f"🤖 [bold]Routing to:[/bold] {routing_decision}\n"
                f"📈 [bold]Confidence:[/bold] {confidence:.0%}\n"
                f"💭 [bold]Reasoning:[/bold] {reasoning[:50]}...",
                title="📡 Coordinator Routing",
                border_style="green"
            ))
            
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
            
        except Exception as e:
            console.print(f"[yellow]Coordinator fallback routing: {e}[/yellow]")
            return {
                "analysis": "Fallback scenario analysis",
                "routing_decision": "customer_agent",
                "confidence": 0.7,
                "reasoning": "Default routing due to analysis error"
            }
    
    async def _check_human_approval(self, agent_result: Dict[str, Any], scenario: str) -> Dict[str, Any]:
        """Check if human approval is needed for financial or critical decisions"""
        
        # Check if scenario involves financial decisions
        financial_keywords = ["refund", "money", "payment", "cost", "charge", "compensation", "financial", "damage", "₹", "rupees"]
        scenario_financial = any(keyword in scenario.lower() for keyword in financial_keywords)
        
        # Check if tools used involve financial actions
        financial_tools = ["issue_instant_refund", "exonerate_driver", "log_merchant_packaging_feedback"]  
        tools_used = agent_result.get('tools_used', [])
        tools_financial = any(tool in tools_used for tool in financial_tools)
        
        # Check tool results for financial mentions
        tool_results = agent_result.get('tool_results', {})
        results_financial = False
        for tool, result in tool_results.items():
            result_text = str(result).lower()
            if any(keyword in result_text for keyword in financial_keywords):
                results_financial = True
                break
        
        needs_approval = scenario_financial or tools_financial or results_financial
        
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
    
    async def _display_final_output(self, crisis_id: str, scenario: str, routing_result: Dict, agent_result: Dict, approval_result: Dict, log_file: str):
        """Display final output with proper statements in boxes"""
        
        # Agent performance summary
        console.print("\n📊 [bold blue]AGENT PERFORMANCE SUMMARY[/bold blue]")
        
        performance_table = Table()
        performance_table.add_column("Agent", style="cyan", width=15)
        performance_table.add_column("Role", style="yellow", width=20) 
        performance_table.add_column("Confidence", style="green", width=12)
        performance_table.add_column("Tools Used", style="magenta", width=10)
        performance_table.add_column("Status", style="bright_green", width=12)
        
        performance_table.add_row(
            "Coordinator",
            "Analysis & Routing",
            f"{routing_result['confidence']:.0%}",
            "0",
            "✅ Completed"
        )
        
        performance_table.add_row(
            agent_result['agent'].replace('_', ' ').title(),
            "Execution & Resolution", 
            f"{agent_result['confidence']:.0%}",
            str(len(agent_result.get('tools_used', []))),
            "✅ Completed"
        )
        
        console.print(performance_table)
        
        # Actions taken summary
        console.print("\n📋 [bold blue]ACTIONS TAKEN SUMMARY[/bold blue]")
        actions_taken = agent_result.get('actions_taken', [])
        for i, action in enumerate(actions_taken[:5], 1):
            console.print(f"   {i}. {action}")
        
        # Final status box
        status = "CRISIS SUCCESSFULLY RESOLVED" if approval_result.get('approved', True) else "CRISIS ANALYZED - PENDING APPROVAL"
        status_color = "green" if approval_result.get('approved', True) else "yellow"
        
        final_statements = [
            f"✅ Crisis scenario successfully analyzed and processed",
            f"🎯 Intelligent routing: Coordinator → {agent_result['agent'].replace('_', ' ').title()}",
            f"🛠️ Dynamic tool execution: {len(agent_result.get('tools_used', []))} tools utilized",
            f"🧠 LLM-powered reasoning: High confidence decision making",
            f"💰 Financial governance: {'Human approved' if approval_result.get('approved') else 'Pending approval'}",
            f"📄 Complete audit trail: Saved to {log_file.split('/')[-1]}"
        ]
        
        console.print(Panel.fit(
            f"🏆 [bold {status_color}]{status}[/bold {status_color}]\n\n" +
            "\n".join(final_statements) + f"\n\n"
            f"🆔 [bold]Crisis ID:[/bold] {crisis_id}\n"
            f"📊 [bold]Overall Confidence:[/bold] {((routing_result['confidence'] + agent_result['confidence']) / 2):.0%}\n"
            f"⏱️ [bold]Processing:[/bold] Complete\n\n"
            f"[bold green]🎯 Multi-agent coordination successfully completed![/bold green]" if approval_result.get('approved', True) else
            f"[bold yellow]⏸️ Analysis complete - awaiting human approval for execution.[/bold yellow]",
            title="🚀 Project Synapse - Crisis Resolution Complete",
            border_style=status_color
        ))
    
    async def _save_proper_results(self, crisis_id: str, scenario: str, coord_result: Dict, 
                                   spec_result: Dict, approved: bool) -> str:
        """Save enhanced results with full tracking"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"logs/chain_of_thought_{crisis_id}_{timestamp}.json"
        
        Path("logs").mkdir(exist_ok=True)
        
        log_data = {
            "scenario_id": crisis_id,
            "timestamp": datetime.now().isoformat(),
            "execution_results": chain_tracker.execution_results,
            "chain_of_thought": chain_tracker.chain_of_thought,
            "summary": chain_tracker.get_summary(),
            "scenario": scenario,
            "financial_approval": approved
        }
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        return log_file

async def main():
    """Main execution"""
    
    if len(sys.argv) < 2:
        console.print(Panel.fit(
            "🤖 [bold blue]PROPER AGENTIC COORDINATOR[/bold blue]\n\n"
            "[bold yellow]Usage:[/bold yellow]\n"
            "python fixed_proper_coordinator.py \"Your crisis scenario\"\n\n"
            "[bold green]System Features:[/bold green]\n"
            "• 🧠 Coordinator: Analysis and routing only\n"
            "• 🤖 Agents: Full reasoning and tool execution\n"
            "• 🛠️ Dynamic tool creation when needed\n"
            "• 📊 Proper chain of thought tracking\n"
            "• 💰 Human approval for financial decisions\n\n"
            "[bold cyan]Example Scenarios:[/bold cyan]\n"
            "• \"Customer wants refund for damaged package\"\n"
            "• \"Delivery stuck in Mumbai traffic jam\"\n"
            "• \"Restaurant delay causing order issues\"",
            title="🚀 Proper Agentic Crisis Management",
            border_style="blue"
        ))
        return
    
    scenario = " ".join(sys.argv[1:])
    
    coordinator = ProperCoordinator()
    await coordinator.handle_crisis(scenario)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        console.print(f"[red]System Error: {e}[/red]")
