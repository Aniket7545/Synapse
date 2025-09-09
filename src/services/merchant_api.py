"""
Real-time Merchant API Integration Service for Project Synapse
Connects with restaurant POS systems and kitchen management platforms
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, asdict
import random
import logging
from config.settings import settings

logger = logging.getLogger(__name__)


class OrderStatus(str, Enum):
    RECEIVED = "received"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    PICKED_UP = "picked_up"
    CANCELLED = "cancelled"
    DELAYED = "delayed"


class MerchantType(str, Enum):
    RESTAURANT = "restaurant"
    CLOUD_KITCHEN = "cloud_kitchen"
    CAFE = "cafe"
    BAKERY = "bakery"
    FAST_FOOD = "fast_food"


class KitchenStatus(str, Enum):
    NORMAL = "normal"
    BUSY = "busy"
    OVERWHELMED = "overwhelmed"
    OFFLINE = "offline"


@dataclass
class MenuItem:
    item_id: str
    name: str
    category: str
    preparation_time_minutes: int
    price: float
    available: bool = True
    special_instructions: str = ""


@dataclass
class OrderItem:
    menu_item: MenuItem
    quantity: int
    customizations: List[str] = None
    estimated_prep_time: int = 0
    
    def __post_init__(self):
        if self.customizations is None:
            self.customizations = []
        if self.estimated_prep_time == 0:
            self.estimated_prep_time = self.menu_item.preparation_time_minutes * self.quantity


@dataclass
class MerchantOrder:
    order_id: str
    merchant_id: str
    customer_id: str
    items: List[OrderItem]
    status: OrderStatus
    total_amount: float
    estimated_prep_time: int
    actual_prep_time: Optional[int] = None
    created_at: datetime = None
    updated_at: datetime = None
    special_notes: str = ""
    kitchen_priority: int = 1  # 1=normal, 2=high, 3=urgent
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


@dataclass
class MerchantProfile:
    merchant_id: str
    name: str
    merchant_type: MerchantType
    address: str
    phone: str
    email: str
    kitchen_capacity: int = 10  # Orders per hour
    current_load: int = 0
    kitchen_status: KitchenStatus = KitchenStatus.NORMAL
    average_prep_time: int = 15  # minutes
    rating: float = 4.5
    is_active: bool = True


class MerchantAPIService:
    """Real-time merchant integration service"""
    
    def __init__(self):
        self.active_merchants: Dict[str, MerchantProfile] = {}
        self.active_orders: Dict[str, MerchantOrder] = {}
        self.menu_cache: Dict[str, List[MenuItem]] = {}
        self.webhooks: Dict[str, List[str]] = {}  # merchant_id -> webhook URLs
        self.api_keys: Dict[str, str] = {}  # merchant_id -> API key
        
        # Popular Indian restaurant chains for demo
        self._initialize_demo_merchants()
    
    def _initialize_demo_merchants(self):
        """Initialize demo merchant profiles"""
        demo_merchants = [
            {
                "merchant_id": "MER_001",
                "name": "Burger Palace",
                "type": MerchantType.FAST_FOOD,
                "address": "Bandra West, Mumbai",
                "phone": "+91-9876543210"
            },
            {
                "merchant_id": "MER_002", 
                "name": "Spice Route Restaurant",
                "type": MerchantType.RESTAURANT,
                "address": "Connaught Place, Delhi",
                "phone": "+91-9876543211"
            },
            {
                "merchant_id": "MER_003",
                "name": "South Indian Delights",
                "type": MerchantType.RESTAURANT,
                "address": "Koramangala, Bangalore",
                "phone": "+91-9876543212"
            },
            {
                "merchant_id": "MER_004",
                "name": "Mumbai Street Food Co.",
                "type": MerchantType.CLOUD_KITCHEN,
                "address": "Andheri East, Mumbai",
                "phone": "+91-9876543213"
            },
            {
                "merchant_id": "MER_005",
                "name": "Cafe Mocha",
                "type": MerchantType.CAFE,
                "address": "Khan Market, Delhi",
                "phone": "+91-9876543214"
            }
        ]
        
        for merchant_data in demo_merchants:
            profile = MerchantProfile(
                merchant_id=merchant_data["merchant_id"],
                name=merchant_data["name"],
                merchant_type=merchant_data["type"],
                address=merchant_data["address"],
                phone=merchant_data["phone"],
                email=f"orders@{merchant_data['name'].lower().replace(' ', '')}.com"
            )
            self.active_merchants[merchant_data["merchant_id"]] = profile
            
            # Generate sample menu
            self._generate_sample_menu(merchant_data["merchant_id"], merchant_data["type"])
    
    def _generate_sample_menu(self, merchant_id: str, merchant_type: MerchantType):
        """Generate sample menu items for demo merchants"""
        
        menu_templates = {
            MerchantType.FAST_FOOD: [
                ("Burger Combo", "Mains", 8, 299.0),
                ("Chicken Wings", "Appetizers", 12, 199.0),
                ("French Fries", "Sides", 5, 99.0),
                ("Cola", "Beverages", 2, 49.0)
            ],
            MerchantType.RESTAURANT: [
                ("Butter Chicken", "Mains", 18, 350.0),
                ("Biryani", "Mains", 25, 450.0),
                ("Naan", "Sides", 8, 60.0),
                ("Lassi", "Beverages", 3, 80.0)
            ],
            MerchantType.CAFE: [
                ("Cappuccino", "Beverages", 5, 120.0),
                ("Sandwich", "Mains", 10, 180.0),
                ("Pastry", "Desserts", 3, 150.0),
                ("Green Tea", "Beverages", 3, 90.0)
            ],
            MerchantType.CLOUD_KITCHEN: [
                ("Vada Pav", "Street Food", 5, 30.0),
                ("Pani Puri", "Street Food", 8, 60.0),
                ("Pav Bhaji", "Mains", 12, 120.0),
                ("Cutting Chai", "Beverages", 2, 20.0)
            ]
        }
        
        template = menu_templates.get(merchant_type, menu_templates[MerchantType.RESTAURANT])
        menu_items = []
        
        for i, (name, category, prep_time, price) in enumerate(template):
            item = MenuItem(
                item_id=f"{merchant_id}_ITEM_{i+1:03d}",
                name=name,
                category=category,
                preparation_time_minutes=prep_time,
                price=price,
                available=True  # Make all items available for demo
            )
            menu_items.append(item)
        
        self.menu_cache[merchant_id] = menu_items
    
    async def register_merchant(
        self,
        merchant_profile: MerchantProfile,
        api_key: str,
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Register a new merchant for API integration"""
        
        self.active_merchants[merchant_profile.merchant_id] = merchant_profile
        self.api_keys[merchant_profile.merchant_id] = api_key
        
        if webhook_url:
            if merchant_profile.merchant_id not in self.webhooks:
                self.webhooks[merchant_profile.merchant_id] = []
            self.webhooks[merchant_profile.merchant_id].append(webhook_url)
        
        logger.info(f"Merchant {merchant_profile.name} registered with API integration")
        
        return {
            "merchant_id": merchant_profile.merchant_id,
            "status": "registered",
            "api_endpoint": f"https://api.synapse.in/merchant/{merchant_profile.merchant_id}",
            "webhook_configured": webhook_url is not None,
            "integration_active": True
        }
    
    async def create_order(
        self,
        merchant_id: str,
        customer_id: str,
        order_items: List[Dict[str, Any]],
        special_notes: str = ""
    ) -> Dict[str, Any]:
        """Create a new order with merchant"""
        
        if merchant_id not in self.active_merchants:
            raise ValueError(f"Merchant {merchant_id} not registered")
        
        merchant = self.active_merchants[merchant_id]
        menu = self.menu_cache.get(merchant_id, [])
        
        # Build order items
        processed_items = []
        total_amount = 0.0
        total_prep_time = 0
        
        for item_data in order_items:
            # Find menu item
            menu_item = next(
                (item for item in menu if item.item_id == item_data["item_id"]),
                None
            )
            
            if not menu_item:
                raise ValueError(f"Menu item {item_data['item_id']} not found")
            
            if not menu_item.available:
                raise ValueError(f"{menu_item.name} is currently unavailable")
            
            order_item = OrderItem(
                menu_item=menu_item,
                quantity=item_data["quantity"],
                customizations=item_data.get("customizations", [])
            )
            
            processed_items.append(order_item)
            total_amount += menu_item.price * item_data["quantity"]
            total_prep_time = max(total_prep_time, order_item.estimated_prep_time)
        
        # Adjust prep time based on kitchen load
        kitchen_multiplier = {
            KitchenStatus.NORMAL: 1.0,
            KitchenStatus.BUSY: 1.3,
            KitchenStatus.OVERWHELMED: 1.8,
            KitchenStatus.OFFLINE: 0  # Will reject order
        }.get(merchant.kitchen_status, 1.0)
        
        if kitchen_multiplier == 0:
            raise ValueError(f"Merchant {merchant.name} is currently offline")
        
        adjusted_prep_time = int(total_prep_time * kitchen_multiplier)
        
        # Create order
        order_id = f"ORD_{merchant_id}_{int(datetime.now().timestamp())}"
        
        order = MerchantOrder(
            order_id=order_id,
            merchant_id=merchant_id,
            customer_id=customer_id,
            items=processed_items,
            status=OrderStatus.RECEIVED,
            total_amount=total_amount,
            estimated_prep_time=adjusted_prep_time,
            special_notes=special_notes
        )
        
        self.active_orders[order_id] = order
        
        # Update merchant load
        merchant.current_load += len(processed_items)
        
        # Send webhook notification
        await self._send_webhook_notification(merchant_id, "order_created", order)
        
        return {
            "order_id": order_id,
            "status": "created",
            "estimated_prep_time": adjusted_prep_time,
            "total_amount": total_amount,
            "merchant_name": merchant.name,
            "kitchen_status": merchant.kitchen_status.value,
            "expected_ready_time": (datetime.now() + timedelta(minutes=adjusted_prep_time)).isoformat()
        }
    
    async def update_order_status(
        self,
        order_id: str,
        new_status: OrderStatus,
        estimated_time_remaining: Optional[int] = None,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Update order status (called by merchant POS system)"""
        
        if order_id not in self.active_orders:
            raise ValueError(f"Order {order_id} not found")
        
        order = self.active_orders[order_id]
        old_status = order.status
        
        order.status = new_status
        order.updated_at = datetime.now()
        
        if notes:
            order.special_notes += f"\n[{datetime.now().strftime('%H:%M')}] {notes}"
        
        # Calculate actual prep time if order is ready
        if new_status == OrderStatus.READY and order.actual_prep_time is None:
            order.actual_prep_time = int((datetime.now() - order.created_at).total_seconds() / 60)
        
        # Update estimated time if provided
        if estimated_time_remaining is not None:
            order.estimated_prep_time = estimated_time_remaining
        
        # Send webhook notification
        await self._send_webhook_notification(
            order.merchant_id, 
            "order_status_updated", 
            order,
            {"old_status": old_status.value, "new_status": new_status.value}
        )
        
        return {
            "order_id": order_id,
            "old_status": old_status.value,
            "new_status": new_status.value,
            "updated_at": order.updated_at.isoformat(),
            "estimated_time_remaining": estimated_time_remaining,
            "actual_prep_time": order.actual_prep_time
        }
    
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get current order status and details"""
        
        if order_id not in self.active_orders:
            # Try to find order by partial ID (for demo)
            matching_orders = [oid for oid in self.active_orders.keys() if order_id in oid]
            if not matching_orders:
                return {"error": "Order not found"}
            order_id = matching_orders[0]
        
        order = self.active_orders[order_id]
        merchant = self.active_merchants[order.merchant_id]
        
        # Calculate time estimates
        time_elapsed = int((datetime.now() - order.created_at).total_seconds() / 60)
        time_remaining = max(0, order.estimated_prep_time - time_elapsed)
        
        return {
            "order_id": order_id,
            "merchant_name": merchant.name,
            "merchant_phone": merchant.phone,
            "status": order.status.value,
            "total_amount": order.total_amount,
            "items_count": len(order.items),
            "items": [
                {
                    "name": item.menu_item.name,
                    "quantity": item.quantity,
                    "customizations": item.customizations
                }
                for item in order.items
            ],
            "estimated_prep_time": order.estimated_prep_time,
            "actual_prep_time": order.actual_prep_time,
            "time_elapsed_minutes": time_elapsed,
            "time_remaining_minutes": time_remaining,
            "created_at": order.created_at.isoformat(),
            "updated_at": order.updated_at.isoformat(),
            "kitchen_status": merchant.kitchen_status.value,
            "special_notes": order.special_notes
        }
    
    async def get_merchant_status(self, merchant_id: str) -> Dict[str, Any]:
        """Get comprehensive merchant status"""
        
        if merchant_id not in self.active_merchants:
            return {"error": "Merchant not found"}
        
        merchant = self.active_merchants[merchant_id]
        
        # Get active orders for this merchant
        merchant_orders = [
            order for order in self.active_orders.values()
            if order.merchant_id == merchant_id and order.status in [
                OrderStatus.RECEIVED, OrderStatus.CONFIRMED, OrderStatus.PREPARING
            ]
        ]
        
        # Calculate metrics
        avg_wait_time = sum(
            int((datetime.now() - order.created_at).total_seconds() / 60)
            for order in merchant_orders
        ) / len(merchant_orders) if merchant_orders else 0
        
        return {
            "merchant_id": merchant_id,
            "name": merchant.name,
            "type": merchant.merchant_type.value,
            "kitchen_status": merchant.kitchen_status.value,
            "current_load": len(merchant_orders),
            "capacity": merchant.kitchen_capacity,
            "utilization_percent": min(100, int((len(merchant_orders) / merchant.kitchen_capacity) * 100)),
            "average_prep_time": merchant.average_prep_time,
            "current_avg_wait": int(avg_wait_time),
            "active_orders": len(merchant_orders),
            "rating": merchant.rating,
            "is_active": merchant.is_active,
            "address": merchant.address,
            "phone": merchant.phone
        }
    
    async def simulate_kitchen_activity(
        self, 
        merchant_id: str, 
        duration_minutes: int = 30
    ) -> List[Dict[str, Any]]:
        """Simulate realistic kitchen activity for demo"""
        
        if merchant_id not in self.active_merchants:
            raise ValueError(f"Merchant {merchant_id} not found")
        
        updates = []
        merchant = self.active_merchants[merchant_id]
        
        # Get orders for this merchant
        merchant_orders = [
            order for order in self.active_orders.values()
            if order.merchant_id == merchant_id and order.status in [
                OrderStatus.RECEIVED, OrderStatus.CONFIRMED, OrderStatus.PREPARING
            ]
        ]
        
        # Simulate status updates every few minutes
        for minute in range(0, duration_minutes, 3):
            for order in merchant_orders:
                # Randomly update order status
                if order.status == OrderStatus.RECEIVED:
                    new_status = OrderStatus.CONFIRMED
                elif order.status == OrderStatus.CONFIRMED:
                    new_status = OrderStatus.PREPARING
                elif order.status == OrderStatus.PREPARING:
                    # 50% chance to mark as ready
                    new_status = OrderStatus.READY if random.random() > 0.5 else OrderStatus.PREPARING
                else:
                    continue
                
                if new_status != order.status:
                    update = await self.update_order_status(
                        order.order_id,
                        new_status,
                        estimated_time_remaining=random.randint(5, 20)
                    )
                    updates.append(update)
            
            # Randomly update kitchen status
            if random.random() > 0.8:  # 20% chance
                new_kitchen_status = random.choice([
                    KitchenStatus.NORMAL, KitchenStatus.BUSY, KitchenStatus.OVERWHELMED
                ])
                merchant.kitchen_status = new_kitchen_status
                updates.append({
                    "type": "kitchen_status_update",
                    "merchant_id": merchant_id,
                    "new_status": new_kitchen_status.value,
                    "timestamp": datetime.now().isoformat()
                })
            
            await asyncio.sleep(0.1)  # Small delay for simulation
        
        return updates
    
    async def _send_webhook_notification(
        self,
        merchant_id: str,
        event_type: str,
        order: MerchantOrder,
        extra_data: Dict[str, Any] = None
    ):
        """Send webhook notification to registered URLs"""
        
        webhook_urls = self.webhooks.get(merchant_id, [])
        if not webhook_urls:
            return
        
        payload = {
            "event": event_type,
            "timestamp": datetime.now().isoformat(),
            "merchant_id": merchant_id,
            "order": asdict(order),
            **(extra_data or {})
        }
        
        # In production, this would make HTTP POST requests
        logger.info(f"Webhook notification: {event_type} for order {order.order_id}")
        
        # Simulate webhook delivery
        await asyncio.sleep(0.1)
    
    async def get_menu(self, merchant_id: str) -> Dict[str, Any]:
        """Get merchant menu with availability"""
        
        if merchant_id not in self.active_merchants:
            return {"error": "Merchant not found"}
        
        merchant = self.active_merchants[merchant_id]
        menu_items = self.menu_cache.get(merchant_id, [])
        
        return {
            "merchant_id": merchant_id,
            "merchant_name": merchant.name,
            "menu_items": [asdict(item) for item in menu_items],
            "total_items": len(menu_items),
            "available_items": len([item for item in menu_items if item.available]),
            "last_updated": datetime.now().isoformat()
        }


# Global merchant service instance
merchant_api = MerchantAPIService()
