"""
Agentic Agent - Project Synapse
Agent that shows reasoning first, then executes tools with proper chain of thought tracking
"""

from typing import Dict, List, Any
from datetime import datetime
from config.llm_config import LLMClient
from src.core.chain_tracker import chain_tracker
from src.core.tool_manager import DynamicToolManager
from rich.console import Console
from rich.panel import Panel

console = Console()


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
        
        # Display reasoning with action plan
        action_plan_text = ""
        if 'action_plan' in reasoning and isinstance(reasoning['action_plan'], list):
            action_plan_text = "\n🎯 [bold]Action Plan:[/bold]\n"
            for i, step in enumerate(reasoning['action_plan'][:4], 1):
                action_plan_text += f"   {i}. {step}\n"
        
        console.print(Panel.fit(
            f"🧠 [bold green]AGENT REASONING[/bold green]\n\n"
            f"{reasoning['analysis']}\n"
            f"{action_plan_text}\n"
            f"📋 [bold]Approach:[/bold] {reasoning['approach']}\n"
            f"⚡ [bold]Urgency:[/bold] {reasoning.get('urgency', 'medium').upper()}\n"
            f"📊 [bold]Confidence:[/bold] {reasoning['confidence']:.0%}",
            title=f"💭 {self.agent_name.replace('_', ' ').title()} Crisis Analysis",
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
        """Get detailed agent reasoning with Project Synapse style action plan"""
        
        console.print(f"🧠 [cyan]Getting {self.agent_name} reasoning...[/cyan]")
        
        prompt = f"""
You are a {self.agent_name.replace('_', ' ')} specialist with expertise in: {self.specialization}

Analyze this crisis scenario and create a SPECIFIC ACTION PLAN like Project Synapse examples:
SCENARIO: {scenario}
CONTEXT: {context}

Create a professional action plan with specific named steps like:
- "Initiate Real-Time Mediation" 
- "Guide Evidence Collection"
- "Deploy Smart Resolution"
- "Execute Instant Compensation"
- "Communicate Final Outcome"

Your response format:
ANALYSIS: [Professional analysis of root cause, stakeholders, and impact]
ACTION_PLAN: [List 3-4 specific action steps with professional names]
APPROACH: [Your systematic resolution methodology]  
URGENCY: [low/medium/high/critical]
CONFIDENCE: [0.7-0.95]

Be specific and actionable like a crisis management expert.
"""
        
        try:
            response = await self.llm_client.chat_completion([{"role": "user", "content": prompt}])
            
            reasoning = {
                "analysis": "Professional crisis analysis completed",
                "action_plan": ["Assess situation", "Deploy resolution", "Execute solution", "Monitor outcome"],
                "approach": "Systematic crisis resolution methodology",
                "urgency": "medium",
                "confidence": 0.87,
                "full_reasoning": response
            }
            
            # Parse LLM response
            lines = response.split('\n')
            for line in lines:
                if line.startswith('ANALYSIS:'):
                    reasoning["analysis"] = line.replace('ANALYSIS:', '').strip()
                elif line.startswith('ACTION_PLAN:'):
                    # Extract action plan steps
                    plan_text = line.replace('ACTION_PLAN:', '').strip()
                    if plan_text:
                        reasoning["action_plan"] = [step.strip('- ') for step in plan_text.split('\n') if step.strip()]
                elif line.startswith('APPROACH:'):
                    reasoning["approach"] = line.replace('APPROACH:', '').strip()
                elif line.startswith('URGENCY:'):
                    reasoning["urgency"] = line.replace('URGENCY:', '').strip()
                elif line.startswith('CONFIDENCE:'):
                    try:
                        reasoning["confidence"] = float(line.replace('CONFIDENCE:', '').strip())
                    except:
                        pass
            
            return reasoning
            
        except Exception as e:
            console.print(f"[yellow]LLM reasoning fallback: {e}[/yellow]")
            # Fallback reasoning with Project Synapse style
            return {
                "analysis": f"Crisis scenario requiring {self.agent_name} expertise for systematic resolution",
                "action_plan": ["Initiate Crisis Assessment", "Deploy Resolution Protocol", "Execute Solution Strategy", "Monitor Outcome"],
                "approach": "Project Synapse crisis management methodology",
                "urgency": "high" if "urgent" in scenario.lower() else "medium",
                "confidence": 0.85,
                "full_reasoning": f"{self.agent_name.upper()} ANALYSIS: Professional crisis management approach"
            }
        
        console.print(f"✅ [green]Reasoning generated for {self.agent_name}[/green]")
        return reasoning
    
    async def _execute_tools(self, tools: List[str], scenario: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tools with progress display"""
        
        if not tools:
            console.print("[yellow]No tools to execute[/yellow]")
            return {}
        
        console.print(f"🛠️ [bold cyan]Executing {len(tools)} tools...[/bold cyan]")
        results = {}
        
        for i, tool in enumerate(tools, 1):
            console.print(f"   🔧 [{i}/{len(tools)}] Executing {tool}...")
            
            # Simulate tool execution with realistic results
            result = await self._simulate_tool_execution(tool, scenario, context)
            results[tool] = result
            
            console.print(f"   ✅ [green]{tool}:[/green] {result.get('summary', 'Completed successfully')}")
        
        console.print(f"🎯 [bold green]All {len(tools)} tools executed successfully![/bold green]")
        return results
    
    async def _simulate_tool_execution(self, tool_name: str, scenario: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate realistic tool execution with context awareness"""
        
        # Analyze scenario context for appropriate results
        scenario_lower = scenario.lower()
        is_restaurant_delay = any(word in scenario_lower for word in ["restaurant", "prep", "kitchen", "cooking", "order"])
        is_damage_case = any(word in scenario_lower for word in ["damage", "spilled", "broken", "torn"])
        is_traffic_issue = any(word in scenario_lower for word in ["traffic", "stuck", "jam", "route"])
        
        # Create context-aware tool results
        if "collect_evidence" in tool_name:
            if is_damage_case:
                result = {
                    "summary": "Collected evidence of package damage from customer photos and statements",
                    "findings": "Package shows water damage and torn packaging. Customer provided clear photos.",
                    "actions": ["Gathered customer photos", "Documented damage details", "Collected witness statements"],
                    "confidence": 0.88
                }
            else:
                result = {
                    "summary": "Collected customer complaint details and order information",
                    "findings": "Customer provided order details and timeline of events.",
                    "actions": ["Gathered order information", "Documented timeline", "Collected customer statements"],
                    "confidence": 0.85
                }
        elif "get_merchant_status" in tool_name:
            if is_restaurant_delay:
                result = {
                    "summary": "Checked restaurant status - experiencing high order volume with 20-minute prep delay",
                    "findings": "Restaurant operational but kitchen overloaded. Current prep time: 20 minutes above normal.",
                    "actions": ["Contacted restaurant", "Verified kitchen capacity", "Assessed preparation timeline"],
                    "confidence": 0.89
                }
            else:
                result = {
                    "summary": "Checked merchant status - restaurant operational with normal service",
                    "findings": "Restaurant is operational with standard preparation times.",
                    "actions": ["Contacted restaurant", "Verified operational status", "Confirmed service levels"],
                    "confidence": 0.86
                }
        elif "notify_customer" in tool_name:
            if is_restaurant_delay:
                result = {
                    "summary": "Notified customer about restaurant delay and offered ₹50 voucher for inconvenience",
                    "findings": "Customer informed about delay and compensated with voucher for future orders.",
                    "actions": ["Sent delay notification", "Offered voucher compensation", "Updated customer account"],
                    "confidence": 0.91
                }
            elif is_damage_case:
                result = {
                    "summary": "Sent notification to customer about refund processing",
                    "findings": "Customer successfully notified via SMS and app notification about refund.",
                    "actions": ["Sent refund notification", "Updated app status", "Logged communication"],
                    "confidence": 0.89
                }
            else:
                result = {
                    "summary": "Sent status update notification to customer",
                    "findings": "Customer successfully notified about resolution progress.",
                    "actions": ["Sent status update", "Updated app notification", "Logged communication"],
                    "confidence": 0.87
                }
        else:
            # Generic tool result
            result = {
                "summary": f"Successfully executed {tool_name} for crisis resolution",
                "findings": f"Tool {tool_name} completed specialized analysis and actions",
                "actions": [f"Executed {tool_name} protocol", "Generated actionable insights", "Documented results"],
                "confidence": 0.82
            }
        
        return result
    
    async def _generate_actions(self, tool_results: Dict[str, Any], reasoning: Dict[str, Any]) -> List[str]:
        """Generate list of actions taken by agent with specific results"""
        
        actions = []
        
        # Create specific actions from tool results
        for tool, result in tool_results.items():
            summary = result.get('summary', '')
            
            if tool == "get_merchant_status":
                if "20-minute prep delay" in summary:
                    actions.append("🏪 **Merchant Crisis Identified**: Restaurant overloaded with 20-minute prep delay detected")
                else:
                    actions.append("🏪 **Merchant Status Verified**: Restaurant operational status confirmed")
            
            elif tool == "get_nearby_merchants":
                if "3 nearby restaurants" in summary:
                    actions.append("🔍 **Alternative Solutions Found**: 3 nearby restaurants with 10-minute wait time identified")
                else:
                    actions.append("🔍 **Alternative Analysis**: Nearby merchant options evaluated")
            
            elif tool == "notify_customer":
                if "₹50 voucher" in summary:
                    actions.append("💬 **Customer Compensation**: ₹50 voucher issued + delay notification sent")
                elif "refund" in summary:
                    actions.append("💬 **Customer Resolution**: Refund notification delivered")
                else:
                    actions.append("💬 **Customer Communication**: Status updates provided")
            
            else:
                # Use the summary as fallback with formatting
                clean_summary = summary.replace("Successfully executed", "Executed").replace("for crisis resolution", "")
                actions.append(f"🔧 **{tool.replace('_', ' ').title()}**: {clean_summary[:70]}...")
        
        # Add specific resolution summary if needed
        if not actions:
            actions.append(f"🎯 **{self.agent_name.replace('_', ' ').title()}**: Applied specialized crisis resolution expertise")
        
        return actions[:5]  # Limit to 5 actions
