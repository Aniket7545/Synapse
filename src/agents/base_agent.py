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
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any], current_thinking_id: str = None) -> Dict[str, Any]:
        """Execute a tool by name with chain of thought tracking"""
        from src.utils.chain_of_thought import chain_of_thought, ThoughtType
        
        tool = self._find_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool {tool_name} not found")
        
        try:
            result = await tool.execute(parameters)
            
            # Add tool to current thought if thinking_id provided
            if current_thinking_id:
                chain_of_thought.add_tool_to_thought(
                    current_thinking_id, 
                    tool_name, 
                    result.get('status', 'completed')
                )
            
            return result
        except Exception as e:
            # Add failed tool to current thought if thinking_id provided
            if current_thinking_id:
                chain_of_thought.add_tool_to_thought(
                    current_thinking_id, 
                    tool_name, 
                    f"failed: {str(e)}"
                )
            raise
    
    def _find_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Find tool by name"""
        for tool in self.tools:
            if tool.name == tool_name:
                return tool
        return None
