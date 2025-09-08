"""
Base Tool Interface for Project Synapse
Industry-grade tool abstraction with proper async patterns and error handling
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import uuid


class BaseTool(ABC):
    """Abstract base class for all Project Synapse tools"""
    
    def __init__(self):
        self.name = self.__class__.__name__.lower().replace('tool', '')
        self.description = "Base tool description"
        self.logger = logging.getLogger(f"tools.{self.name}")
        self.execution_id = None
        
    @abstractmethod
    async def _run(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool - must be implemented by subclasses"""
        pass
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool with proper error handling and logging"""
        self.execution_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            self.logger.info(f"Executing {self.name} with parameters: {parameters}")
            result = await self._run(**parameters)
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                "success": True,
                "data": result,
                "execution_time_ms": execution_time,
                "tool_name": self.name,
                "execution_id": self.execution_id
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            self.logger.error(f"Tool {self.name} failed: {str(e)}")
            
            return {
                "success": False,
                "error": str(e),
                "execution_time_ms": execution_time,
                "tool_name": self.name,
                "execution_id": self.execution_id
            }
