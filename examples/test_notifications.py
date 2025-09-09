"""
Real-time Notification Testing Example
Tests the Twilio integration for SMS and WhatsApp notifications
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.services.twilio_service import twilio_service
from src.tools.notify_customer import NotifyCustomerTool
from rich.console import Console
from rich.panel import Panel

console = Console()


async def test_notifications():
    """Test real-time notification system"""
    
    console.print(Panel.fit(
        "🔔 Testing Real-time Notification System",
        style="bold blue"
    ))
    
    # Initialize notification tool
    notify_tool = NotifyCustomerTool()
    
    # Test scenarios
    test_cases = [
        {
            "customer_id": "CUST_12345",
            "message": "🚛 Your delivery is delayed by 15 minutes due to traffic. New ETA: 3:30 PM",
            "channel": "sms",
            "phone_number": "9876543210"
        },
        {
            "customer_id": "CUST_67890", 
            "message": "📦 Great news! Your order has been picked up and is on its way. Track: synapse.in/track/ABC123",
            "channel": "whatsapp",
            "phone_number": "9123456789"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        console.print(f"\n📱 Test {i}: Sending {test_case['channel'].upper()} notification...")
        
        result = await notify_tool._run(
            customer_id=test_case['customer_id'],
            message=test_case['message'],
            channel=test_case['channel'],
            phone_number=test_case['phone_number']
        )
        
        # Display result
        status_color = "green" if result['status'] == 'sent' else "red"
        console.print(f"   ✅ Status: [{status_color}]{result['status'].upper()}[/{status_color}]")
        console.print(f"   📞 To: {result.get('to_number', 'N/A')}")
        console.print(f"   🆔 Message ID: {result['message_id']}")
        console.print(f"   💰 Cost: ₹{result['cost_inr']}")
        console.print(f"   🏷️ Provider: {result.get('provider', 'unknown')}")
        
        if result['status'] == 'failed':
            console.print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
    
    # Test delivery status check
    console.print(f"\n📊 Testing delivery status check...")
    status = await twilio_service.get_delivery_status(test_cases[0]['message_id'] if 'message_id' in locals() else 'test_id')
    console.print(f"   📈 Delivery Status: {status}")
    
    console.print(Panel.fit(
        "🎉 Notification system test completed!\n" +
        "Configure Twilio credentials in .env for real SMS/WhatsApp delivery.",
        style="bold green"
    ))


if __name__ == "__main__":
    asyncio.run(test_notifications())
