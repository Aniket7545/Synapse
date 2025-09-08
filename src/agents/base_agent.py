"""
Base Agent Interface for Project Synapse
Industry-grade agent abstraction with proper typing and async patterns
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from src.models.delivery_state import DeliveryState
from src.models.agent_response import AgentResponse
from src.tools.base_tool import BaseTool


class BaseAgent(ABC):
    """Abstract base class for all Project Synapse agents"""
    
    def __init__(self, agent_name: str, agent_description: str, tools: Optional[List[BaseTool]] = None):
        self.agent_name = agent_name
        self.agent_description = agent_description
        self.tools = tools or []
        self.execution_id = str(uuid.uuid4())
        
    @abstractmethod
    async def handle(self, state: DeliveryState) -> AgentResponse:
        """Main entry point for agent execution"""
        pass
    
    @abstractmethod
    def get_required_tools(self) -> List[str]:
        """Return list of tool names this agent requires"""
        pass
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool by name"""
        tool = self._find_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool {tool_name} not found")
        return await tool.execute(parameters)
    
    def _find_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Find tool by name"""
        for tool in self.tools:
            if tool.name == tool_name:
                return tool
        return None
