"""
Tool Scanner and Manager for Project Synapse
Scans available tools and manages dynamic tool creation
"""

import os
import importlib
from pathlib import Path
from typing import Dict, List, Any
import inspect

class ToolScanner:
    """Scans and categorizes available tools"""
    
    def __init__(self):
        self.tools_dir = Path(__file__).parent.parent / "src" / "tools"
        self.available_tools = {}
        self.scan_tools()
    
    def scan_tools(self):
        """Scan all available tools in the tools directory"""
        
        # Core categories based on our crisis management needs
        self.tool_categories = {
            "customer_tools": [
                "collect_evidence", "analyze_evidence", "issue_instant_refund", 
                "initiate_mediation_flow", "contact_recipient_via_chat", "notify_customer"
            ],
            "traffic_tools": [
                "check_traffic", "calculate_alternative_route", "re_route_driver",
                "indian_traffic_analysis", "route_optimization", "monsoon_impact"
            ],
            "merchant_tools": [
                "get_merchant_status", "get_nearby_merchants", "log_merchant_packaging_feedback",
                "estimate_preparation_time", "monitor_kitchen_performance"
            ],
            "driver_tools": [
                "track_driver", "find_nearby_driver", "assign_driver", 
                "update_driver_location", "exonerate_driver"
            ],
            "location_tools": [
                "find_nearby_locker", "suggest_safe_drop_off", "flood_zone_routing"
            ],
            "communication_tools": [
                "notify_resolution", "package_damage_assessment"
            ]
        }
        
        # Scan actual tool files
        for tool_file in self.tools_dir.glob("*.py"):
            if tool_file.name.startswith("__"):
                continue
            
            tool_name = tool_file.stem
            self.available_tools[tool_name] = {
                "file": tool_file,
                "category": self._categorize_tool(tool_name),
                "description": self._get_tool_description(tool_file)
            }
    
    def _categorize_tool(self, tool_name: str) -> str:
        """Categorize tool based on name"""
        for category, tools in self.tool_categories.items():
            if any(tool_part in tool_name for tool_part in tools):
                return category
        return "utility_tools"
    
    def _get_tool_description(self, tool_file: Path) -> str:
        """Extract tool description from file"""
        try:
            with open(tool_file, 'r') as f:
                content = f.read()
                # Look for description in class or docstring
                lines = content.split('\n')
                for line in lines:
                    if 'description' in line and '=' in line:
                        return line.split('=')[1].strip().strip('"\'')
                    elif '"""' in line and ('Tool' in line or 'tool' in line):
                        return line.strip('"""').strip()
            return f"Crisis management tool: {tool_file.stem}"
        except:
            return f"Tool: {tool_file.stem}"
    
    def get_tools_for_agent(self, agent_type: str) -> List[Dict[str, str]]:
        """Get relevant tools for specific agent type"""
        
        agent_tool_mapping = {
            "coordinator": ["analyze_evidence", "initiate_mediation_flow", "notify_resolution"],
            "customer_agent": ["collect_evidence", "analyze_evidence", "issue_instant_refund", 
                             "initiate_mediation_flow", "contact_recipient_via_chat", "notify_customer"],
            "traffic_agent": ["check_traffic", "calculate_alternative_route", "re_route_driver",
                            "indian_traffic_tools", "flood_zone_routing"],
            "merchant_agent": ["get_merchant_status", "get_nearby_merchants", 
                             "log_merchant_packaging_feedback", "merchant_api_tools"],
            "driver_agent": ["track_driver", "find_nearby_driver", "assign_driver", 
                           "exonerate_driver", "driver_tracking_tools"]
        }
        
        relevant_tools = []
        tool_names = agent_tool_mapping.get(agent_type, [])
        
        for tool_name in tool_names:
            for available_tool, info in self.available_tools.items():
                if any(part in available_tool for part in tool_name.split('_')):
                    relevant_tools.append({
                        "name": available_tool,
                        "description": info["description"],
                        "category": info["category"]
                    })
        
        return relevant_tools[:8]  # Limit to 8 most relevant tools
    
    def get_tool_recommendations_to_remove(self) -> List[str]:
        """Recommend tools that might be out of context"""
        
        potentially_irrelevant = []
        
        # Check for tools that might be too specific or outdated
        for tool_name, info in self.available_tools.items():
            # Tools that might be too specific for general crisis management
            if any(keyword in tool_name.lower() for keyword in 
                  ['google_maps', 'analytics', 'document_tools']):
                potentially_irrelevant.append({
                    "tool": tool_name,
                    "reason": "Too specific or might have better alternatives",
                    "description": info["description"]
                })
        
        return potentially_irrelevant
    
    def create_new_tool_template(self, tool_name: str, description: str, agent_type: str) -> str:
        """Create template for new tool"""
        
        class_name = ''.join(word.capitalize() for word in tool_name.split('_')) + 'Tool'
        
        template = f'''"""
{tool_name}() - {description}
Dynamically created tool for {agent_type}
"""

import asyncio
from datetime import datetime
from typing import Dict, Any
from src.tools.base_tool import BaseTool


class {class_name}(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "{tool_name}"
        self.description = "{description}"
    
    async def _run(self, **kwargs) -> Dict[str, Any]:
        # Simulate realistic execution time
        await asyncio.sleep(1.0)
        
        return {{
            "tool": "{tool_name}",
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "agent_type": "{agent_type}",
            "description": "{description}",
            "execution_result": "Tool executed successfully with scenario-specific results",
            **kwargs
        }}


# Tool instance for import
{tool_name}_tool = {class_name}()
'''
        
        return template
    
    def suggest_missing_tools(self, scenario: str) -> List[Dict[str, str]]:
        """Suggest tools that might be needed for scenario but don't exist"""
        
        scenario_lower = scenario.lower()
        missing_tools = []
        
        # Analyze scenario for missing capabilities
        if "weather" in scenario_lower and not any("weather" in tool for tool in self.available_tools):
            missing_tools.append({
                "name": "weather_impact_assessment",
                "description": "Assess weather impact on delivery operations",
                "reason": "Scenario mentions weather but no weather tool found"
            })
        
        if "insurance" in scenario_lower and not any("insurance" in tool for tool in self.available_tools):
            missing_tools.append({
                "name": "insurance_claim_processor", 
                "description": "Process insurance claims for damaged packages",
                "reason": "Scenario involves damage that might need insurance"
            })
        
        if "emergency" in scenario_lower and not any("emergency" in tool for tool in self.available_tools):
            missing_tools.append({
                "name": "emergency_escalation",
                "description": "Escalate to emergency response protocols",
                "reason": "Emergency situation detected"
            })
        
        return missing_tools


# Global tool scanner instance
tool_scanner = ToolScanner()
