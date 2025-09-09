from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ChainOfThoughtStep(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent: str
    action: str
    reasoning: str
    severity: int
    urgency: int
    outcome: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class ChainOfThoughtLog(BaseModel):
    scenario_id: str
    steps: List[ChainOfThoughtStep]
    summary: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
