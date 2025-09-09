"""
Smart Notification System Demo
Shows contextual, intelligent notifications for different delivery scenarios
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.services.notification_system import smart_notifications
from src.models.delivery_state import DeliveryState, DisruptionType, IndianCity, LocationInfo, StakeholderInfo, OrderDetails
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


async def demo_smart_notifications():
    """Demonstrate contextual notifications for various scenarios"""
    
    console.print(Panel.fit(
        "🧠 Smart Notification System Demo\n" +
        "Contextual, AI-powered customer communications",
        style="bold cyan"
    ))
    
    # Create test scenarios
    scenarios = [
        {
            "name": "Traffic Jam in Mumbai",
            "state": DeliveryState(
                scenario_id="ORD_001",
                thread_id="thread_001",
                disruption_type=DisruptionType.TRAFFIC_JAM,
                severity_level=7,
                description="Heavy traffic on Western Express Highway",
                location=LocationInfo(
                    city=IndianCity.MUMBAI,
                    origin_address="Burger Palace, Bandra West",
                    destination_address="Worli Sea Face, Mumbai",
                    pincode="400050"
                ),
                stakeholders=StakeholderInfo(
                    customer_id="CUST_12345",
                    driver_id="DRV_001",
                    merchant_id="MER_001",
                    customer_phone="9876543210",
                    customer_tier="premium"
                ),
                order=OrderDetails(
                    order_id="ORD_001",
                    items=["Burger Combo", "Fries"],
                    total_value=299.0
                )
            )
        },
        {
            "name": "Merchant Delay in Delhi", 
            "state": DeliveryState(
                scenario_id="ORD_002",
                thread_id="thread_002",
                disruption_type=DisruptionType.MERCHANT_DELAY,
                severity_level=6,
                description="Kitchen overwhelmed with orders",
                location=LocationInfo(
                    city=IndianCity.DELHI,
                    origin_address="Spice Route Restaurant, Connaught Place",
                    destination_address="Hauz Khas Village, Delhi",
                    pincode="110016"
                ),
                stakeholders=StakeholderInfo(
                    customer_id="CUST_67890",
                    driver_id="DRV_002",
                    merchant_id="MER_002", 
                    customer_phone="9123456789",
                    customer_tier="standard"
                ),
                order=OrderDetails(
                    order_id="ORD_002",
                    items=["Biryani", "Raita", "Dessert"],
                    total_value=450.0
                )
            )
        },
        {
            "name": "Customer Unavailable in Bangalore",
            "state": DeliveryState(
                scenario_id="ORD_003",
                thread_id="thread_003",
                disruption_type=DisruptionType.CUSTOMER_UNAVAILABLE,
                severity_level=8,
                description="Customer not responding to calls",
                location=LocationInfo(
                    city=IndianCity.BANGALORE,
                    origin_address="South Indian Delights, Koramangala",
                    destination_address="Electronic City, Bangalore",
                    pincode="560100"
                ),
                stakeholders=StakeholderInfo(
                    customer_id="CUST_54321",
                    driver_id="DRV_003",
                    merchant_id="MER_003",
                    customer_phone="9987654321",
                    customer_tier="gold"
                ),
                order=OrderDetails(
                    order_id="ORD_003",
                    items=["Dosa", "Sambar", "Chutney"],
                    total_value=180.0
                )
            )
        }
    ]
    
    # Test each scenario
    for i, scenario in enumerate(scenarios, 1):
        console.print(f"\n📱 **Scenario {i}: {scenario['name']}**")
        
        # Send WhatsApp notification
        console.print("   Sending WhatsApp notification...")
        whatsapp_result = await smart_notifications.send_contextual_notification(
            scenario['state'], 
            channel="whatsapp"
        )
        
        await asyncio.sleep(0.5)
        
        # Send SMS notification  
        console.print("   Sending SMS notification...")
        sms_result = await smart_notifications.send_contextual_notification(
            scenario['state'],
            channel="sms"
        )
        
        # Display summary
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Channel", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Message ID", style="yellow") 
        table.add_column("Cost", style="red")
        
        table.add_row(
            "WhatsApp", 
            whatsapp_result['status'], 
            whatsapp_result['message_id'][-12:] + "...",
            f"₹{whatsapp_result['cost_inr']}"
        )
        table.add_row(
            "SMS",
            sms_result['status'],
            sms_result['message_id'][-12:] + "...", 
            f"₹{sms_result['cost_inr']}"
        )
        
        console.print(table)
        console.print()
    
    # Demo proactive notifications
    console.print("🚀 **Testing Proactive Updates**")
    proactive_results = await smart_notifications.send_proactive_updates(scenarios[0]['state'])
    
    console.print(f"   ✅ Sent {len(proactive_results)} proactive notifications")
    for result in proactive_results:
        console.print(f"   📱 {result['channel'].upper()}: {result['status']} (₹{result['cost_inr']})")
    
    # Calculate total cost
    total_cost = sum([
        whatsapp_result['cost_inr'] + sms_result['cost_inr'] 
        for scenario in scenarios
    ]) + sum([r['cost_inr'] for r in proactive_results])
    
    console.print(Panel.fit(
        f"🎉 Demo completed successfully!\n" +
        f"💰 Total notification cost: ₹{total_cost:.2f}\n" +
        f"📊 {len(scenarios) * 2 + len(proactive_results)} notifications sent\n" +
        f"🔧 Configure Twilio for real delivery",
        style="bold green"
    ))


if __name__ == "__main__":
    asyncio.run(demo_smart_notifications())
