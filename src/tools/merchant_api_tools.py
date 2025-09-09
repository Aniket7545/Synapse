"""
Merchant API Tools for Project Synapse
Provides real-time merchant integration capabilities for agents
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
from src.tools.base_tool import BaseTool
from src.services.merchant_api import merchant_api, OrderStatus, KitchenStatus


class GetMerchantStatusTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "get_merchant_status"
        self.description = "Get real-time merchant kitchen status, load, and capacity"
    
    async def _run(self, merchant_id: str) -> Dict[str, Any]:
        """Get comprehensive merchant status information"""
        
        result = await merchant_api.get_merchant_status(merchant_id)
        return result


class CheckOrderStatusTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "check_order_status"
        self.description = "Check real-time order status and preparation progress"
    
    async def _run(self, order_id: str) -> Dict[str, Any]:
        """Get detailed order status from merchant"""
        
        result = await merchant_api.get_order_status(order_id)
        return result


class CreateMerchantOrderTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "create_merchant_order"
        self.description = "Create a new order with merchant and get preparation timeline"
    
    async def _run(
        self,
        merchant_id: str,
        customer_id: str,
        items: List[Dict[str, Any]],
        special_notes: str = ""
    ) -> Dict[str, Any]:
        """Create order with merchant"""
        
        try:
            result = await merchant_api.create_order(
                merchant_id, customer_id, items, special_notes
            )
            return result
        except ValueError as e:
            return {"error": str(e)}


class UpdateOrderStatusTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "update_order_status"
        self.description = "Update order status (for merchant-side updates)"
    
    async def _run(
        self,
        order_id: str,
        new_status: str,
        estimated_time_remaining: int = None,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Update order status from merchant side"""
        
        try:
            status_enum = OrderStatus(new_status)
            result = await merchant_api.update_order_status(
                order_id, status_enum, estimated_time_remaining, notes
            )
            return result
        except (ValueError, KeyError) as e:
            return {"error": str(e)}


class GetMerchantMenuTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "get_merchant_menu"
        self.description = "Get merchant menu with item availability and pricing"
    
    async def _run(self, merchant_id: str) -> Dict[str, Any]:
        """Get merchant menu and availability"""
        
        result = await merchant_api.get_menu(merchant_id)
        return result


class EstimatePreparationTimeTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "estimate_preparation_time"
        self.description = "Get accurate preparation time estimate based on kitchen load"
    
    async def _run(
        self,
        merchant_id: str,
        items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Estimate preparation time for given items"""
        
        merchant_status = await merchant_api.get_merchant_status(merchant_id)
        
        if "error" in merchant_status:
            return merchant_status
        
        # Base preparation time calculation
        base_time = 0
        for item in items:
            # Estimate based on item complexity (mock calculation)
            item_time = 10  # Base 10 minutes per item
            if "biryani" in item.get("name", "").lower():
                item_time = 25
            elif "burger" in item.get("name", "").lower():
                item_time = 8
            elif "pizza" in item.get("name", "").lower():
                item_time = 15
            
            base_time = max(base_time, item_time * item.get("quantity", 1))
        
        # Apply kitchen load multiplier
        utilization = merchant_status["utilization_percent"]
        if utilization > 80:
            multiplier = 1.8
        elif utilization > 60:
            multiplier = 1.4
        elif utilization > 40:
            multiplier = 1.2
        else:
            multiplier = 1.0
        
        estimated_time = int(base_time * multiplier)
        
        return {
            "merchant_id": merchant_id,
            "merchant_name": merchant_status["name"],
            "base_preparation_time": base_time,
            "kitchen_multiplier": multiplier,
            "estimated_preparation_time": estimated_time,
            "kitchen_status": merchant_status["kitchen_status"],
            "current_load": merchant_status["current_load"],
            "utilization_percent": utilization,
            "ready_by": (datetime.now().replace(second=0, microsecond=0) + 
                        timedelta(minutes=estimated_time)).isoformat()
        }


class MonitorKitchenPerformanceTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "monitor_kitchen_performance"
        self.description = "Monitor merchant kitchen performance and identify bottlenecks"
    
    async def _run(self, merchant_id: str) -> Dict[str, Any]:
        """Analyze merchant kitchen performance"""
        
        merchant_status = await merchant_api.get_merchant_status(merchant_id)
        
        if "error" in merchant_status:
            return merchant_status
        
        # Performance analysis
        utilization = merchant_status["utilization_percent"]
        avg_wait = merchant_status["current_avg_wait"]
        
        # Determine performance level
        if utilization > 90:
            performance_level = "critical"
            recommendation = "Kitchen overwhelmed - consider rejecting new orders"
        elif utilization > 70:
            performance_level = "stressed"
            recommendation = "High load - expect delays, inform customers"
        elif utilization > 50:
            performance_level = "busy"
            recommendation = "Moderate load - monitor closely"
        else:
            performance_level = "optimal"
            recommendation = "Normal operations"
        
        return {
            "merchant_id": merchant_id,
            "merchant_name": merchant_status["name"],
            "performance_level": performance_level,
            "utilization_percent": utilization,
            "current_avg_wait_minutes": avg_wait,
            "active_orders": merchant_status["active_orders"],
            "kitchen_status": merchant_status["kitchen_status"],
            "recommendation": recommendation,
            "should_accept_orders": utilization < 90,
            "expected_delay_minutes": max(0, avg_wait - merchant_status["average_prep_time"]),
            "analysis_timestamp": datetime.now().isoformat()
        }
