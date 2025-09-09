"""
Enhanced Customer Notification System
Provides contextual, intelligent notifications based on delivery scenarios
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
from src.tools.notify_customer import NotifyCustomerTool
from src.models.delivery_state import DeliveryState, DisruptionType
from rich.console import Console

console = Console()


class SmartNotificationSystem:
    """Intelligent notification system that sends contextual messages"""
    
    def __init__(self):
        self.notify_tool = NotifyCustomerTool()
        self.notification_templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, Dict[str, str]]:
        """Load notification templates for different scenarios"""
        return {
            "traffic_jam": {
                "sms": "🚛 Your delivery is experiencing traffic delays. New ETA: {eta}. Track live: synapse.in/track/{order_id}",
                "whatsapp": "🚛 *Delivery Update*\n\nHi {customer_name}! Your order #{order_id} is stuck in traffic near {location}.\n\n📍 Current Status: {status}\n⏰ New ETA: {eta}\n🗺️ Live tracking: synapse.in/track/{order_id}\n\nWe'll keep you updated! 📱"
            },
            "merchant_delay": {
                "sms": "📦 Your order preparation is taking longer than expected. Updated ETA: {eta}. Merchant: {merchant_name}",
                "whatsapp": "📦 *Order Update*\n\nHi {customer_name}! Your order #{order_id} from {merchant_name} needs a bit more time.\n\n👨‍🍳 Status: Still preparing\n⏰ New ETA: {eta}\n💝 Good news: Extra care means better quality!\n\nThank you for your patience! 🙏"
            },
            "customer_unavailable": {
                "sms": "📞 Our delivery partner tried reaching you. Please call {driver_phone} or reschedule at synapse.in/reschedule/{order_id}",
                "whatsapp": "📞 *Delivery Attempt*\n\nHi {customer_name}! Our delivery partner arrived at {location} but couldn't reach you.\n\n🚪 What's next?\n• Call driver: {driver_phone}\n• Reschedule: synapse.in/reschedule/{order_id}\n• Track live: synapse.in/track/{order_id}\n\nWe're here to help! 📱"
            },
            "dispute": {
                "sms": "📦 We're investigating your order concern #{order_id}. Resolution ETA: 24 hours. Support: 1800-SYNAPSE",
                "whatsapp": "📦 *Order Investigation*\n\nHi {customer_name}! We're looking into your concern about order #{order_id}.\n\n✅ *Our process:*\n• Evidence collection in progress\n• 24-hour resolution commitment\n• Priority support assigned\n\n📞 Questions? Call 1800-SYNAPSE\n\nYour satisfaction is our priority! 💯"
            },
            "weather_impact": {
                "sms": "🌧️ Weather conditions affecting your delivery. New ETA: {eta}. Track: synapse.in/track/{order_id}",
                "whatsapp": "🌧️ *Weather Update*\n\nHi {customer_name}! Weather conditions in {location} are affecting your delivery.\n\n🔄 *Status Update:*\n• Safe route selected\n• New ETA: {eta}\n• Quality preserved\n\n📱 Track live: synapse.in/track/{order_id}\n\nSafety first! 🙏"
            },
            "address_issue": {
                "sms": "📍 Address verification needed for order #{order_id}. Please call {driver_phone} or update address",
                "whatsapp": "📍 *Address Verification*\n\nHi {customer_name}! We need to verify the delivery address for order #{order_id}.\n\n🚪 Quick actions:\n• Call driver: {driver_phone}\n• Update address: synapse.in/address/{order_id}\n• Live chat: synapse.in/chat\n\nWe're here to help! �"
            }
        }
    
    async def send_contextual_notification(
        self, 
        state: DeliveryState, 
        channel: str = "whatsapp",
        custom_message: str = None
    ) -> Dict[str, Any]:
        """Send intelligent notification based on delivery scenario"""
        
        # Extract scenario type
        scenario_key = state.disruption_type.value
        
        # Get template
        template = self.notification_templates.get(
            scenario_key, 
            self.notification_templates["traffic_jam"]  # fallback
        ).get(channel, "Your delivery status has been updated.")
        
        # Generate dynamic content
        eta = self._calculate_eta(state)
        message_params = {
            "customer_name": f"Customer {state.stakeholders.customer_id[-4:]}",  # Mock customer name
            "order_id": state.scenario_id,
            "location": state.location.city.value.title(),
            "status": self._get_friendly_status(state),
            "eta": eta,
            "merchant_name": f"Restaurant {state.stakeholders.merchant_id[-3:]}",  # Mock merchant name
            "driver_phone": "+91-9876543210"  # Mock driver phone
        }
        
        # Format message
        if custom_message:
            formatted_message = custom_message.format(**message_params)
        else:
            formatted_message = template.format(**message_params)
        
        # Send notification
        result = await self.notify_tool._run(
            customer_id=state.stakeholders.customer_id,
            message=formatted_message,
            channel=channel,
            phone_number=state.stakeholders.customer_phone
        )
        
        console.print(f"📱 Sent {channel.upper()} to Customer {state.stakeholders.customer_id[-4:]}: {result['status']}")
        
        return result
    
    async def send_proactive_updates(self, state: DeliveryState) -> List[Dict[str, Any]]:
        """Send proactive updates at key delivery milestones"""
        
        notifications = []
        
        # Send initial pickup notification
        customer_name = f"Customer {state.stakeholders.customer_id[-4:]}"
        merchant_name = f"Restaurant {state.stakeholders.merchant_id[-3:]}"
        pickup_msg = f"📦 Great news {customer_name}! Your order #{state.scenario_id} has been picked up from {merchant_name}. ETA: {self._calculate_eta(state)} 🚛"
        
        pickup_result = await self.notify_tool._run(
            customer_id=state.stakeholders.customer_id,
            message=pickup_msg,
            channel="whatsapp",
            phone_number=state.stakeholders.customer_phone
        )
        notifications.append(pickup_result)
        
        # Send halfway update (simulate)
        await asyncio.sleep(1)
        halfway_msg = f"🗺️ Halfway there! Your order #{state.scenario_id} is on route. Current location: Near {state.location.city.value.title()}. ETA: {self._calculate_eta(state)} ⏰"
        
        halfway_result = await self.notify_tool._run(
            customer_id=state.stakeholders.customer_id,
            message=halfway_msg,
            channel="sms",
            phone_number=state.stakeholders.customer_phone
        )
        notifications.append(halfway_result)
        
        return notifications
    
    def _calculate_eta(self, state: DeliveryState) -> str:
        """Calculate estimated delivery time"""
        base_time = datetime.now() + timedelta(minutes=30)
        
        # Adjust based on scenario
        if state.disruption_type == DisruptionType.TRAFFIC_JAM:
            base_time += timedelta(minutes=15)
        elif state.disruption_type == DisruptionType.MERCHANT_DELAY:
            base_time += timedelta(minutes=20)
        elif state.disruption_type == DisruptionType.WEATHER_IMPACT:
            base_time += timedelta(minutes=25)
        elif state.disruption_type == DisruptionType.ADDRESS_ISSUE:
            base_time += timedelta(minutes=10)
        
        return base_time.strftime("%I:%M %p")
    
    def _get_friendly_status(self, state: DeliveryState) -> str:
        """Convert technical status to customer-friendly status"""
        status_map = {
            DisruptionType.TRAFFIC_JAM: "Navigating traffic",
            DisruptionType.MERCHANT_DELAY: "Being prepared with extra care", 
            DisruptionType.CUSTOMER_UNAVAILABLE: "Waiting for your availability",
            DisruptionType.DISPUTE: "Under investigation",
            DisruptionType.WEATHER_IMPACT: "Weather delay - safe route selected",
            DisruptionType.ADDRESS_ISSUE: "Address verification needed"
        }
        return status_map.get(state.disruption_type, "In transit")


# Global notification system
smart_notifications = SmartNotificationSystem()
