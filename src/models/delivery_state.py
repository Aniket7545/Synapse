"""
Delivery State Model for Project Synapse
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class DisruptionType(str, Enum):
    TRAFFIC_JAM = "traffic_jam"
    MERCHANT_DELAY = "merchant_delay"
    DISPUTE = "dispute"
    CUSTOMER_UNAVAILABLE = "customer_unavailable"
    WEATHER_IMPACT = "weather_impact"
    ADDRESS_ISSUE = "address_issue"


class IndianCity(str, Enum):
    MUMBAI = "mumbai"
    DELHI = "delhi"
    BANGALORE = "bangalore"
    HYDERABAD = "hyderabad"
    CHENNAI = "chennai"
    KOLKATA = "kolkata"
    PUNE = "pune"


class LocationInfo(BaseModel):
    city: IndianCity
    origin_address: str
    destination_address: str
    pincode: str


class StakeholderInfo(BaseModel):
    customer_id: str
    driver_id: str
    merchant_id: str
    customer_phone: str
    customer_language: str = "english"
    customer_tier: str = "standard"


class OrderDetails(BaseModel):
    order_id: str
    items: List[str]
    total_value: float
    order_type: str = "food"


class DeliveryState(BaseModel):
    scenario_id: str
    thread_id: str
    disruption_type: DisruptionType
    severity_level: int = Field(ge=1, le=10)
    description: str
    location: LocationInfo
    stakeholders: StakeholderInfo
    order: OrderDetails
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
