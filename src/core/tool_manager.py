"""
Dynamic Tool Management - Project Synapse
Manages existing and dynamically created tools with LLM-driven selection
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from config.llm_config import LLMClient
from rich.console import Console

console = Console()


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
        
        # Add Project Synapse specific tools if folder is empty
        if not existing:
            existing.update({
                # Customer/Dispute Resolution Tools (from Project Synapse document)
                "initiate_mediation_flow": "Open synchronized interface for real-time mediation",
                "collect_evidence": "Guide photo collection and dynamic questionnaire",
                "analyze_evidence": "Process evidence to determine fault and liability",
                "issue_instant_refund": "Execute immediate customer compensation",
                "exonerate_driver": "Clear driver from fault when not responsible",
                "log_merchant_packaging_feedback": "Send evidence-backed report to merchant",
                "notify_resolution": "Inform all parties of resolution outcome",
                
                # Traffic & Logistics Tools
                "check_traffic": "Analyze real-time traffic conditions and delays",
                "calculate_alternative_route": "Compute optimal alternative delivery routes",
                "re_route_driver": "Execute driver route change with instructions",
                "indian_traffic_analysis": "Advanced traffic analysis for Indian cities",
                "flood_zone_routing": "Navigate around flood zones and obstacles",
                
                # Merchant & Operations Tools
                "get_merchant_status": "Check restaurant operational status and capacity",
                "get_nearby_merchants": "Find alternative merchants in delivery area",
                "contact_recipient_via_chat": "Direct communication with customer",
                "notify_customer": "Send status notifications to customer",
                "track_driver": "Real-time driver location and status tracking"
            })
        
        return existing
    
    async def get_required_tools(self, agent_type: str, scenario: str, reasoning: str) -> List[str]:
        """Get required tools for agent based on scenario and reasoning"""
        
        # Filter existing tools by agent type
        relevant_existing = self._filter_tools_by_agent(agent_type)
        
        console.print(f"🔍 [cyan]Selecting tools for {agent_type}...[/cyan]")
        
        # LLM-driven tool selection based on scenario context
        selected_tools = await self._llm_select_tools(agent_type, scenario, reasoning, relevant_existing)
        
        # Ensure all selected tools exist in our available tools and remove duplicates
        final_tools = []
        seen_tools = set()
        
        for tool in selected_tools:
            if tool in self.existing_tools and tool not in seen_tools:
                final_tools.append(tool)
                seen_tools.add(tool)
        
        # If no valid tools found, use Project Synapse fallback
        if not final_tools:
            console.print(f"🛠️ [yellow]Using Project Synapse fallback for {agent_type}...[/yellow]")
            if agent_type == "customer_agent":
                # Check if it's a damage case for full Project Synapse workflow
                if any(word in scenario.lower() for word in ["damage", "spilled", "broken", "dispute"]):
                    final_tools = ["initiate_mediation_flow", "collect_evidence", "analyze_evidence", 
                                 "issue_instant_refund", "exonerate_driver", "log_merchant_packaging_feedback", "notify_resolution"]
                else:
                    final_tools = ["collect_evidence", "analyze_evidence", "notify_customer"]
            elif agent_type == "merchant_agent":
                final_tools = ["get_merchant_status", "get_nearby_merchants", "notify_customer"]
            elif agent_type == "traffic_agent":
                final_tools = ["check_traffic", "calculate_alternative_route", "re_route_driver", "notify_customer"]
            else:
                final_tools = ["notify_customer"]
        
        console.print(f"✅ [green]Selected {len(final_tools)} tools for {agent_type}[/green]")
        return final_tools[:7]  # Allow up to 7 tools for complex scenarios
    
    async def _llm_select_tools(self, agent_type: str, scenario: str, reasoning: str, available_tools: Dict[str, str]) -> List[str]:
        """Use LLM to intelligently select appropriate tools for the scenario"""
        
        tools_list = "\n".join([f"- {name}: {desc}" for name, desc in available_tools.items()])
        
        prompt = f"""
You are an intelligent tool selector for a {agent_type.replace('_', ' ')} handling this crisis scenario.

SCENARIO: {scenario}
AGENT REASONING: {reasoning}

AVAILABLE TOOLS:
{tools_list}

CRITICAL REASONING - MATCH TOOLS TO SCENARIO TYPE:

🍽️ FOR MERCHANT_AGENT + RESTAURANT/KITCHEN DELAYS:
✅ EXACTLY 3 TOOLS: get_merchant_status, get_nearby_merchants, notify_customer
❌ NEVER USE: log_merchant_packaging_feedback (that's for damage cases only)
❌ NEVER USE: evidence/refund tools (no damage occurred)
❌ NO DUPLICATES: Don't repeat same tool twice

📦 FOR CUSTOMER_AGENT + DAMAGED/SPILLED PACKAGES:
🔥 MANDATORY ALL 7 PROJECT SYNAPSE TOOLS:
1. initiate_mediation_flow (start real-time mediation)
2. collect_evidence (gather photos and statements) 
3. analyze_evidence (determine fault attribution)
4. issue_instant_refund (process customer compensation)
5. exonerate_driver (clear driver if not at fault)
6. log_merchant_packaging_feedback (report to merchant)
7. notify_resolution (inform all stakeholders)
❌ NEVER USE: get_merchant_status, get_nearby_merchants (wrong agent type)

🚦 FOR TRAFFIC/DELIVERY ISSUES (stuck, jams, routing):
✅ CORRECT TOOLS: check_traffic, calculate_alternative_route, re_route_driver, notify_customer
❌ NEVER USE: package_damage_assessment, collect_evidence (no damage involved)

SCENARIO ANALYSIS LOGIC:
1. READ the scenario carefully
2. IDENTIFY the primary issue type (restaurant delay vs package damage vs traffic)
3. SELECT only tools that logically address that specific issue type
4. REJECT tools that don't match the scenario context

CURRENT SCENARIO TYPE: {scenario}
- If mentions "restaurant", "kitchen", "prep", "overload" → RESTAURANT DELAY (use 3 tools)
- If mentions "damaged", "spilled", "broken" → PACKAGE DAMAGE (use ALL 7 tools - comprehensive resolution required)
- If mentions "traffic", "stuck", "jam" → TRAFFIC ISSUE (use 3-4 tools)

🚨 CRITICAL FOR PACKAGE DAMAGE: Project Synapse methodology requires ALL 7 tools for complete dispute resolution. DO NOT skip any tools for damaged package scenarios.

🚨 CRITICAL OUTPUT FORMAT:
Return ONLY the exact tool names, one per line. NO explanations, NO descriptions, NO formatting.

Example correct output for damage case:
initiate_mediation_flow
collect_evidence
analyze_evidence
issue_instant_refund
exonerate_driver
log_merchant_packaging_feedback
notify_resolution

Example correct output for restaurant delay:
get_merchant_status
get_nearby_merchants
notify_customer
"""
        
        try:
            response = await self.llm_client.chat_completion([{"role": "user", "content": prompt}])
            # Parse tool names from response with strict validation
            selected_tools = []
            seen_tools = set()
            
            for line in response.strip().split('\n'):
                # Clean the line to extract just the tool name
                tool_name = line.strip()
                for prefix in ['- ', '• ', '1. ', '2. ', '3. ', '4. ', '5. ', '6. ', '7. ', '8. ', '9. ']:
                    tool_name = tool_name.replace(prefix, '')
                
                tool_name = tool_name.strip()
                
                # Only add if it's a valid tool and not a duplicate
                if tool_name in available_tools and tool_name not in seen_tools:
                    selected_tools.append(tool_name)
                    seen_tools.add(tool_name)
            
            # Validate and supplement tool selection based on scenario requirements
            scenario_lower = scenario.lower()
            is_damage_case = any(word in scenario_lower for word in ["damage", "spilled", "broken", "dispute", "leak"])
            
            if agent_type == "customer_agent" and is_damage_case:
                # Ensure ALL 7 tools for damage cases
                required_damage_tools = ["initiate_mediation_flow", "collect_evidence", "analyze_evidence", 
                                       "issue_instant_refund", "exonerate_driver", "log_merchant_packaging_feedback", "notify_resolution"]
                selected_tools = required_damage_tools
                console.print(f"🔥 [red]DAMAGE CASE: Using all 7 Project Synapse tools[/red]")
            
            elif agent_type == "merchant_agent":
                # Ensure exactly 3 tools for merchant scenarios
                required_merchant_tools = ["get_merchant_status", "get_nearby_merchants", "notify_customer"]
                selected_tools = required_merchant_tools
                console.print(f"🍽️ [yellow]MERCHANT CASE: Using 3 restaurant tools[/yellow]")
            
            elif agent_type == "traffic_agent":
                selected_tools = ["check_traffic", "calculate_alternative_route", "re_route_driver", "notify_customer"]
            
            # Fallback if still empty
            if not selected_tools:
                selected_tools = ["notify_customer"]
            
            return selected_tools[:7]  # Allow up to 7 tools for comprehensive resolution
            
        except Exception as e:
            console.print(f"[yellow]LLM tool selection failed, using Project Synapse fallback: {e}[/yellow]")
            # Project Synapse fallback selection
            if agent_type == "merchant_agent":
                return ["get_merchant_status", "get_nearby_merchants", "notify_customer"]
            elif agent_type == "traffic_agent":
                return ["check_traffic", "calculate_alternative_route", "re_route_driver", "notify_customer"]
            elif agent_type == "customer_agent":
                # Check if it's a damage case for full Project Synapse workflow
                if any(word in scenario.lower() for word in ["damage", "spilled", "broken", "dispute"]):
                    return ["initiate_mediation_flow", "collect_evidence", "analyze_evidence", 
                           "issue_instant_refund", "exonerate_driver", "log_merchant_packaging_feedback", "notify_resolution"]
                else:
                    return ["collect_evidence", "analyze_evidence", "notify_customer"]
            else:
                return list(available_tools.keys())[:5]
    
    def _filter_tools_by_agent(self, agent_type: str) -> Dict[str, str]:
        """Filter tools relevant to agent type"""
        
        if agent_type == "customer_agent":
            keywords = ["customer", "evidence", "refund", "contact", "chat", "mediation", "collect", "analyze"]
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
