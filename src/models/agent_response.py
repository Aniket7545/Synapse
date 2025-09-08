"""
Agent Response Model for Project Synapse
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class AgentResponse(BaseModel):
    agent_name: str
    scenario_id: str
    response_type: str
    content: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: Optional[str] = None
    next_agent: Optional[str] = None
    tools_used: List[str] = Field(default_factory=list)
    actions_recommended: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
    execution_time_ms: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
