"""
Fixed Query Processor - Robust Natural Language Analysis
Handles LLM failures gracefully with intelligent fallback
"""

import json
import re
from datetime import datetime
from typing import Dict, Any, List, Tuple
from pydantic import BaseModel
from rich.console import Console

from config.llm_config import llm_client
from src.models.delivery_state import (
    DeliveryState, DisruptionType, IndianCity, 
    LocationInfo, StakeholderInfo, OrderDetails
)
from src.utils.chain_of_thought import chain_of_thought, ThoughtType

console = Console()

class QueryAnalysis(BaseModel):
    """Structured analysis of natural language query"""
    crisis_type: str
    severity: int  # 1-10
    location: str
    stakeholders: List[str]
    urgency: str  # low, medium, high, critical
    key_factors: List[str]
    recommended_agents: List[str]
    estimated_resolution_time: int  # minutes
    confidence: float

class DeliveryCrisisProcessor:
    """Robust processor for delivery crisis natural language queries"""
    
    def __init__(self):
        self.crisis_patterns = {
            "delivery_delay": ["delay", "late", "waiting", "not received", "supposed to get", "expected", "overdue"],
            "traffic_issue": ["traffic", "jam", "congestion", "road", "blocked", "accident", "route"],
            "merchant_delay": ["restaurant", "kitchen", "food", "prep", "cooking", "merchant", "taking too long"],
            "customer_dispute": ["dispute", "complaint", "argue", "fighting", "disagree", "damaged", "spilled"],
            "customer_unavailable": ["unavailable", "not home", "absent", "wrong address", "can't reach"],
            "package_damage": ["damaged", "broken", "spilled", "leaked", "crushed", "package issue"]
        }
        
        self.severity_keywords = {
            "emergency": 10, "urgent": 9, "critical": 8, "serious": 7,
            "angry": 7, "frustrated": 6, "unhappy": 5, "concerned": 4,
            "minor": 3, "small": 2
        }
        
        self.indian_cities = [
            "mumbai", "delhi", "bangalore", "hyderabad", "chennai", 
            "kolkata", "pune", "ahmedabad", "jaipur", "surat"
        ]
    
    async def process_query(self, natural_query: str) -> Tuple[QueryAnalysis, DeliveryState]:
        """Process natural language query into structured analysis"""
        
        console.print(f"🧠 [bold blue]Analyzing:[/bold blue] {natural_query}")
        
        # Start chain of thought
        thinking_id = chain_of_thought.start_thought(
            "query_processor",
            ThoughtType.ANALYSIS, 
            f"Processing query: {natural_query[:50]}..."
        )
        
        try:
            # Try LLM analysis first
            structured_analysis = await self._safe_llm_analyze(natural_query)
        except Exception:
            # Silent fallback to rule-based analysis
            structured_analysis = self._intelligent_fallback_analysis(natural_query)
        
        # Complete chain of thought
        chain_of_thought.complete_thought(
            thinking_id,
            confidence=structured_analysis.confidence,
            reasoning=f"Classified as {structured_analysis.crisis_type} (severity: {structured_analysis.severity})"
        )
        
        # Create delivery state
        delivery_state = self._create_delivery_state(natural_query, structured_analysis)
        
        return structured_analysis, delivery_state
    
    async def _safe_llm_analyze(self, query: str) -> QueryAnalysis:
        """LLM analysis with robust JSON parsing and error handling"""
        
        # Constrained prompt for reliable JSON output
        analysis_prompt = f"""
Analyze this delivery crisis and respond with ONLY valid JSON in this exact format:

Query: "{query}"
{{
"crisis_type": "delivery_delay|traffic_issue|merchant_delay|customer_dispute|customer_unavailable|package_damage",
"severity": 5,
"location": "mumbai|delhi|bangalore|unknown",
"stakeholders": ["customer", "driver"],
"urgency": "low|medium|high|critical",
"key_factors": ["factor1", "factor2"],
"recommended_agents": ["coordinator", "customer_agent"],
"estimated_resolution_time": 15,
"confidence": 0.8
}}

Respond with ONLY the JSON object above. No explanations or extra text.
        """
        
        try:
            llm_response = await llm_client.chat_completion([
                {
                    "role": "system", 
                    "content": "You are a JSON-only response system. Respond ONLY with valid JSON. No explanations, no extra text."
                },
                {
                    "role": "user", 
                    "content": analysis_prompt
                }
            ])
            
            # Extract and parse JSON
            json_data = self._extract_json_safely(llm_response)
            
            # Validate and return
            return QueryAnalysis(**json_data)
            
        except Exception as e:
            raise ValueError(f"LLM analysis failed: {str(e)}")
    
    def _extract_json_safely(self, response: str) -> Dict[str, Any]:
        """Extract JSON from LLM response with multiple fallback strategies"""
        
        # Strategy 1: Extract from code block
        code_block_pattern = r'``````'
        match = re.search(code_block_pattern, response, re.DOTALL)
        
        if match:
            json_text = match.group(1)
        else:
            # Strategy 2: Find JSON object boundaries
            start_idx = response.find('{')
            if start_idx == -1:
                raise ValueError("No JSON object found in response")
            
            # Find matching closing brace
            brace_count = 0
            end_idx = start_idx
            
            for i, char in enumerate(response[start_idx:], start_idx):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break
            
            json_text = response[start_idx:end_idx]
        
        # Clean up JSON text
        json_text = json_text.strip()
        
        # Parse JSON with error handling
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
    
    def _intelligent_fallback_analysis(self, query: str) -> QueryAnalysis:
        """Intelligent rule-based analysis when LLM fails"""
        
        query_lower = query.lower()
        
        # Detect crisis type using pattern matching
        crisis_type = "delivery_delay"  # Default
        max_score = 0
        
        for crisis, patterns in self.crisis_patterns.items():
            score = sum(1 for pattern in patterns if pattern in query_lower)
            if score > max_score:
                max_score = score
                crisis_type = crisis
        
        # Determine severity based on keywords and context
        severity = 5  # Default moderate severity
        
        for keyword, score in self.severity_keywords.items():
            if keyword in query_lower:
                severity = max(severity, score)
        
        # Adjust severity based on time mentions
        if any(time_word in query_lower for time_word in ["30 minutes", "hour", "hours", "long time"]):
            severity = min(10, severity + 2)
        
        # Extract location
        location = "unknown"
        for city in self.indian_cities:
            if city in query_lower:
                location = city
                break
        
        # Determine urgency
        if severity >= 8:
            urgency = "critical"
        elif severity >= 6:
            urgency = "high"
        elif severity >= 4:
            urgency = "medium"
        else:
            urgency = "low"
        
        # Extract key factors
        key_factors = []
        if "30 minutes" in query_lower or "mins" in query_lower:
            key_factors.append("Time-sensitive delay")
        if any(word in query_lower for word in ["waiting", "not received"]):
            key_factors.append("Customer waiting for delivery")
        if not key_factors:
            key_factors.append(f"{crisis_type.replace('_', ' ').title()} situation")
        
        # Recommend agents based on crisis type
        agent_mapping = {
            "delivery_delay": ["coordinator", "customer_agent"],
            "traffic_issue": ["coordinator", "traffic_agent"],
            "merchant_delay": ["coordinator", "merchant_agent"],
            "customer_dispute": ["coordinator", "customer_agent"],
            "customer_unavailable": ["coordinator", "customer_agent"],
            "package_damage": ["coordinator", "customer_agent"]
        }
        
        recommended_agents = agent_mapping.get(crisis_type, ["coordinator", "customer_agent"])
        
        # Estimate resolution time
        base_time = {
            "delivery_delay": 10,
            "traffic_issue": 15,
            "merchant_delay": 20,
            "customer_dispute": 25,
            "customer_unavailable": 15,
            "package_damage": 30
        }
        
        estimated_time = base_time.get(crisis_type, 15)
        estimated_time = min(60, estimated_time + (severity - 5) * 2)
        
        return QueryAnalysis(
            crisis_type=crisis_type,
            severity=min(10, severity),
            location=location,
            stakeholders=["customer", "driver"],
            urgency=urgency,
            key_factors=key_factors,
            recommended_agents=recommended_agents,
            estimated_resolution_time=max(5, estimated_time),
            confidence=0.7  # Fallback analysis confidence
        )
    
    def _create_delivery_state(self, query: str, analysis: QueryAnalysis) -> DeliveryState:
        """Create delivery state from query analysis"""
        
        # Map crisis types to disruption types
        disruption_mapping = {
            "delivery_delay": DisruptionType.CUSTOMER_UNAVAILABLE,
            "traffic_issue": DisruptionType.TRAFFIC_JAM,
            "merchant_delay": DisruptionType.MERCHANT_DELAY,
            "customer_dispute": DisruptionType.DISPUTE,
            "customer_unavailable": DisruptionType.CUSTOMER_UNAVAILABLE,
            "package_damage": DisruptionType.DISPUTE
        }
        
        # Map cities to enum
        city_mapping = {
            "mumbai": IndianCity.MUMBAI,
            "delhi": IndianCity.DELHI,
            "bangalore": IndianCity.BANGALORE,
            "hyderabad": IndianCity.HYDERABAD,
            "chennai": IndianCity.CHENNAI,
            "kolkata": IndianCity.KOLKATA,
            "pune": IndianCity.PUNE
        }
        
        scenario_id = f"LIVE_{int(datetime.now().timestamp())}"
        
        # Determine customer tier based on severity and language
        customer_tier = "premium" if analysis.severity >= 7 else "standard"
        
        return DeliveryState(
            scenario_id=scenario_id,
            thread_id=f"thread_{scenario_id}",
            disruption_type=disruption_mapping.get(analysis.crisis_type, DisruptionType.CUSTOMER_UNAVAILABLE),
            severity_level=analysis.severity,
            description=query,  # Original natural language query
            location=LocationInfo(
                city=city_mapping.get(analysis.location, IndianCity.MUMBAI),
                origin_address=f"Restaurant Location, {analysis.location.title() if analysis.location != 'unknown' else 'Mumbai'}",
                destination_address=f"Customer Address, {analysis.location.title() if analysis.location != 'unknown' else 'Mumbai'}",
                pincode="400001" if analysis.location in ["mumbai", "unknown"] else "110001"
            ),
            stakeholders=StakeholderInfo(
                customer_id="LIVE_CUST",
                driver_id="LIVE_DRV",
                merchant_id="LIVE_MER",
                customer_phone="+91-9876543210",
                customer_language="english",
                customer_tier=customer_tier
            ),
            order=OrderDetails(
                order_id=f"LIVE_ORD_{int(datetime.now().timestamp())}",
                items=["Food Items"],  # Generic for live queries
                total_value=500.0,  # Default value
                order_type="food"
            )
        )


# Global processor instance
crisis_processor = DeliveryCrisisProcessor()
