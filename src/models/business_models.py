"""
Business Logic Models for Project Synapse
Indian market specific business rules and calculations
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from enum import Enum

class CustomerTier(str, Enum):
    STANDARD = "standard"
    PREMIUM = "premium"
    VIP = "vip"
    ENTERPRISE = "enterprise"

class CompensationType(str, Enum):
    VOUCHER = "voucher"
    REFUND = "refund"
    CREDIT = "credit"
    FREE_DELIVERY = "free_delivery"
    UPGRADE = "upgrade"

class IndianBusinessRules(BaseModel):
    """Business rules specific to Indian market"""
    
    @staticmethod
    def calculate_compensation(delay_minutes: int, order_value: float, customer_tier: CustomerTier) -> Dict[str, Any]:
        """Calculate compensation based on Indian market standards"""
        
        base_compensation = {
            CustomerTier.STANDARD: 30,
            CustomerTier.PREMIUM: 50,
            CustomerTier.VIP: 100,
            CustomerTier.ENTERPRISE: 150
        }
        
        compensation_amount = base_compensation[customer_tier]
        
        # Adjust for delay severity
        if delay_minutes > 60:
            compensation_amount *= 2
        elif delay_minutes > 30:
            compensation_amount *= 1.5
        
        # Cap at 20% of order value
        max_compensation = order_value * 0.2
        compensation_amount = min(compensation_amount, max_compensation)
        
        return {
            "type": CompensationType.VOUCHER,
            "amount": compensation_amount,
            "currency": "INR",
            "message": f"₹{compensation_amount} voucher for your inconvenience",
            "valid_days": 30
        }
    
    @staticmethod
    def get_peak_hours(city: str) -> List[str]:
        """Get peak delivery hours for Indian cities"""
        city_peak_hours = {
            "mumbai": ["12:00-14:00", "19:00-22:00"],
            "delhi": ["12:30-14:30", "19:30-22:30"],
            "bangalore": ["12:00-14:00", "19:00-21:30"],
            "hyderabad": ["12:30-14:00", "19:30-22:00"],
            "chennai": ["12:00-14:30", "19:00-21:30"],
            "kolkata": ["12:30-14:30", "19:00-21:30"],
            "pune": ["12:00-14:00", "19:00-22:00"],
        }
        return city_peak_hours.get(city.lower(), ["12:00-14:00", "19:00-22:00"])
    
    @staticmethod
    def get_festival_impact(current_date: str) -> Dict[str, Any]:
        """Assess festival period impact on deliveries"""
        # Simplified festival calendar
        festival_periods = {
            "diwali": {"dates": ["2024-11-01", "2024-11-05"], "impact": "high"},
            "holi": {"dates": ["2024-03-08", "2024-03-09"], "impact": "medium"},
            "eid": {"dates": ["2024-04-10", "2024-04-11"], "impact": "medium"},
        }
        
        return {
            "is_festival_period": False,
            "festival_name": None,
            "impact_level": "none",
            "delivery_adjustments": []
        }

class DeliveryMetrics(BaseModel):
    """Business metrics for delivery performance"""
    total_deliveries: int = Field(default=0)
    successful_deliveries: int = Field(default=0)
    average_resolution_time: float = Field(default=0.0)
    customer_satisfaction_score: float = Field(default=4.0)
    cost_savings: float = Field(default=0.0)
    efficiency_improvement: float = Field(default=0.0)
    
    @property
    def success_rate(self) -> float:
        if self.total_deliveries == 0:
            return 0.0
        return (self.successful_deliveries / self.total_deliveries) * 100
