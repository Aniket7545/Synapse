"""
Real-time Twilio Integration Service for Project Synapse
Handles SMS and WhatsApp notifications for customers
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class TwilioService:
    """Real-time notification service using Twilio API"""
    
    def __init__(self):
        self.client = None
        self.phone_number = None
        self.whatsapp_number = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Twilio client with credentials"""
        try:
            if settings.twilio_account_sid and settings.twilio_auth_token:
                self.client = Client(
                    settings.twilio_account_sid,
                    settings.twilio_auth_token.get_secret_value() if settings.twilio_auth_token else None
                )
                self.phone_number = settings.twilio_phone_number
                self.whatsapp_number = settings.twilio_whatsapp_number
                logger.info("Twilio client initialized successfully")
            else:
                logger.warning("Twilio credentials not found. Using mock mode.")
        except Exception as e:
            logger.error(f"Failed to initialize Twilio client: {e}")
            self.client = None
    
    async def send_sms(self, to_number: str, message: str, customer_id: str) -> Dict[str, Any]:
        """Send SMS notification to customer"""
        if not self.client or not self.phone_number:
            return await self._mock_notification(customer_id, message, "sms", to_number)
        
        try:
            # Format phone number for India
            if not to_number.startswith('+'):
                to_number = f"+91{to_number}"
            
            message_obj = self.client.messages.create(
                body=message,
                from_=self.phone_number,
                to=to_number
            )
            
            return {
                "customer_id": customer_id,
                "message": message,
                "channel": "sms",
                "status": "sent",
                "timestamp": datetime.now().isoformat(),
                "message_id": message_obj.sid,
                "delivery_status": message_obj.status,
                "cost_inr": 0.05,  # Approximate cost in INR
                "to_number": to_number,
                "provider": "twilio_real"
            }
            
        except TwilioException as e:
            logger.error(f"Twilio SMS error: {e}")
            return {
                "customer_id": customer_id,
                "message": message,
                "channel": "sms",
                "status": "failed",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "provider": "twilio_real"
            }
    
    async def send_whatsapp(self, to_number: str, message: str, customer_id: str) -> Dict[str, Any]:
        """Send WhatsApp notification to customer"""
        if not self.client or not self.whatsapp_number:
            return await self._mock_notification(customer_id, message, "whatsapp", to_number)
        
        try:
            # Format phone number for WhatsApp
            if not to_number.startswith('whatsapp:+'):
                to_number = f"whatsapp:+91{to_number.replace('+91', '')}"
            
            from_number = f"whatsapp:{self.whatsapp_number}"
            
            message_obj = self.client.messages.create(
                body=message,
                from_=from_number,
                to=to_number
            )
            
            return {
                "customer_id": customer_id,
                "message": message,
                "channel": "whatsapp",
                "status": "sent",
                "timestamp": datetime.now().isoformat(),
                "message_id": message_obj.sid,
                "delivery_status": message_obj.status,
                "cost_inr": 0.02,  # Approximate cost in INR
                "to_number": to_number,
                "provider": "twilio_real"
            }
            
        except TwilioException as e:
            logger.error(f"Twilio WhatsApp error: {e}")
            return {
                "customer_id": customer_id,
                "message": message,
                "channel": "whatsapp",
                "status": "failed",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "provider": "twilio_real"
            }
    
    async def _mock_notification(self, customer_id: str, message: str, channel: str, to_number: str = None) -> Dict[str, Any]:
        """Fallback mock notification when Twilio is not configured"""
        await asyncio.sleep(0.1)  # Simulate network delay
        
        cost_map = {"sms": 0.05, "whatsapp": 0.02, "app_notification": 0.001}
        
        return {
            "customer_id": customer_id,
            "message": message,
            "channel": channel,
            "status": "sent",
            "timestamp": datetime.now().isoformat(),
            "message_id": f"mock_{channel}_{customer_id}_{int(datetime.now().timestamp())}",
            "delivery_status": "delivered",
            "cost_inr": cost_map.get(channel, 0.05),
            "to_number": to_number,
            "provider": "mock_fallback",
            "note": "Using mock mode - Add Twilio credentials for real notifications"
        }
    
    async def get_delivery_status(self, message_id: str) -> Dict[str, Any]:
        """Check delivery status of a sent message"""
        if not self.client or message_id.startswith('mock_'):
            return {
                "message_id": message_id,
                "status": "delivered",
                "provider": "mock_fallback"
            }
        
        try:
            message = self.client.messages(message_id).fetch()
            return {
                "message_id": message_id,
                "status": message.status,
                "error_code": message.error_code,
                "error_message": message.error_message,
                "provider": "twilio_real"
            }
        except TwilioException as e:
            logger.error(f"Error fetching message status: {e}")
            return {
                "message_id": message_id,
                "status": "unknown",
                "error": str(e),
                "provider": "twilio_real"
            }


# Global service instance
twilio_service = TwilioService()
