"""
Integrated Demo: Live Tracking + Smart Notifications
Shows how driver tracking integrates with customer notifications
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.services.driver_tracking import live_tracker, GPSCoordinate, VehicleType
from src.services.notification_system import smart_notifications
from src.models.delivery_state import DeliveryState, DisruptionType, IndianCity, LocationInfo, StakeholderInfo, OrderDetails
from rich.console import Console
from rich.panel import Panel

console = Console()


async def integrated_demo():
    """Demo showing live tracking + notifications working together"""
    
    console.print(Panel.fit(
        "🔗 Integrated Demo: Live Tracking + Smart Notifications\n" +
        "Real-time driver tracking with automatic customer updates",
        style="bold cyan"
    ))
    
    # Step 1: Setup driver and order
    driver_id = "DRV_DEMO_001"
    order_id = "ORD_INTEGRATED_001"
    
    # Register driver
    driver_location = GPSCoordinate(19.0596, 72.8295)  # Bandra
    await live_tracker.register_driver(
        driver_id=driver_id,
        driver_name="Arjun Singh",
        phone_number="+91-9876543210",
        initial_location=driver_location,
        vehicle_type=VehicleType.BIKE
    )
    
    console.print("✅ Driver registered and tracking started")
    
    # Step 2: Create delivery state for notifications
    delivery_state = DeliveryState(
        scenario_id=order_id,
        thread_id="thread_demo_001",
        disruption_type=DisruptionType.TRAFFIC_JAM,
        severity_level=6,
        description="Heavy traffic on Western Express Highway",
        location=LocationInfo(
            city=IndianCity.MUMBAI,
            origin_address="McDonald's, Bandra West",
            destination_address="Phoenix Mills, Lower Parel",
            pincode="400013"
        ),
        stakeholders=StakeholderInfo(
            customer_id="CUST_DEMO_001",
            driver_id=driver_id,
            merchant_id="MER_DEMO_001",
            customer_phone="9123456789",
            customer_tier="premium"
        ),
        order=OrderDetails(
            order_id=order_id,
            items=["Big Mac Meal", "McFlurry"],
            total_value=350.0
        )
    )
    
    # Step 3: Assign order and start tracking
    pickup_location = GPSCoordinate(19.0596, 72.8295)  # Bandra
    delivery_location = GPSCoordinate(19.0176, 72.8118)  # Lower Parel
    
    assignment = await live_tracker.assign_order(
        driver_id, order_id, pickup_location, delivery_location
    )
    
    console.print(f"📦 Order assigned: {assignment['order_id']}")
    console.print(f"🚛 Driver: Arjun Singh")
    console.print(f"📍 Pickup ETA: {assignment['estimated_pickup_time']} minutes")
    
    # Step 4: Send initial pickup notification
    pickup_notification = await smart_notifications.send_contextual_notification(
        delivery_state, 
        channel="whatsapp"
    )
    
    console.print(f"📱 Initial notification sent: {pickup_notification['status']}")
    
    # Step 5: Simulate driver movement with notifications
    console.print("\n🚛 Simulating delivery journey with live updates...")
    
    # Simulate 3 key points in the journey
    journey_points = [
        {"status": "Picked up order", "delay": 0},
        {"status": "Halfway to destination", "delay": 5},
        {"status": "Traffic delay detected", "delay": 15}
    ]
    
    for i, point in enumerate(journey_points, 1):
        console.print(f"\n📍 Journey Point {i}: {point['status']}")
        
        # Update driver location (simulate movement)
        new_lat = driver_location.latitude + (i * 0.002)
        new_lng = driver_location.longitude - (i * 0.001)
        
        location_update = await live_tracker.update_driver_location(
            driver_id,
            GPSCoordinate(new_lat, new_lng),
            speed_kmh=25.0 - (point['delay'] * 0.5),  # Slower if delayed
            heading=180.0
        )
        
        console.print(f"   🗺️  Updated location: {new_lat:.4f}, {new_lng:.4f}")
        console.print(f"   🏃 Speed: {location_update['speed_kmh']:.1f} km/h")
        
        # Send notification if there's a delay
        if point['delay'] > 0:
            # Update delivery state with new delay info
            delivery_state.description = f"{point['status']} - {point['delay']} min delay"
            
            delay_notification = await smart_notifications.send_contextual_notification(
                delivery_state,
                channel="sms",
                custom_message=f"🚛 Update: Your delivery is delayed by {point['delay']} minutes due to traffic. New ETA: {{eta}}. Track live: synapse.in/track/{{order_id}}"
            )
            
            console.print(f"   📱 Delay notification sent: {delay_notification['status']}")
        
        await asyncio.sleep(1)  # Simulate time passing
    
    # Step 6: Final delivery notification
    console.print("\n🏁 Delivery completed!")
    
    completion_notification = await smart_notifications.send_contextual_notification(
        delivery_state,
        channel="whatsapp",
        custom_message="🎉 Delivered! Your order #{order_id} has been delivered successfully. Thanks for choosing Synapse! Rate your experience: synapse.in/rate/{order_id}"
    )
    
    console.print(f"📱 Completion notification sent: {completion_notification['status']}")
    
    # Step 7: Export tracking data
    tracking_data = await live_tracker.export_tracking_data(driver_id)
    
    console.print(f"\n📊 Journey Summary:")
    console.print(f"   📍 Total locations tracked: {tracking_data['total_locations']}")
    console.print(f"   ⏱️  Journey duration: {tracking_data['tracking_duration_hours']:.2f} hours")
    console.print(f"   🚛 Final status: {tracking_data['driver_info']['status']}")
    
    console.print(Panel.fit(
        "🎉 Integrated Demo Completed!\n\n" +
        "✅ Features Demonstrated:\n" +
        "• Driver registration & tracking\n" +
        "• Order assignment & GPS monitoring\n" +
        "• Real-time location updates\n" +
        "• Automatic customer notifications\n" +
        "• Context-aware messaging\n" +
        "• Journey analytics\n\n" +
        "🚀 Production-ready integration of live tracking + notifications!",
        style="bold green"
    ))


if __name__ == "__main__":
    asyncio.run(integrated_demo())
