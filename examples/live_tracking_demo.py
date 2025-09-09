"""
Live Driver Tracking Demo for Project Synapse
Demonstrates real-time GPS tracking, route optimization, and driver management
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.services.driver_tracking import live_tracker, GPSCoordinate, VehicleType, DriverStatus
from src.tools.driver_tracking_tools import TrackDriverTool, FindNearbyDriverTool, AssignDriverTool
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
import random

console = Console()


async def setup_demo_drivers():
    """Register sample drivers in Mumbai for demo"""
    
    # Mumbai locations for drivers
    mumbai_locations = [
        {"name": "Bandra", "lat": 19.0596, "lng": 72.8295},
        {"name": "Andheri", "lat": 19.1136, "lng": 72.8697},
        {"name": "Worli", "lat": 19.0176, "lng": 72.8118},
        {"name": "Powai", "lat": 19.1197, "lng": 72.9081},
        {"name": "Malad", "lat": 19.1864, "lng": 72.8493}
    ]
    
    drivers = []
    
    for i, location in enumerate(mumbai_locations, 1):
        driver_id = f"DRV_{1000 + i}"
        gps_location = GPSCoordinate(
            latitude=location["lat"] + random.uniform(-0.002, 0.002),
            longitude=location["lng"] + random.uniform(-0.002, 0.002),
            accuracy=random.uniform(3.0, 8.0)
        )
        
        vehicle_types = [VehicleType.BIKE, VehicleType.SCOOTER, VehicleType.CAR]
        
        result = await live_tracker.register_driver(
            driver_id=driver_id,
            driver_name=f"Rajesh Kumar {i}",
            phone_number=f"+91-9876{54320 + i}",
            initial_location=gps_location,
            vehicle_type=random.choice(vehicle_types)
        )
        
        drivers.append({
            "driver_id": driver_id,
            "name": f"Rajesh Kumar {i}",
            "location": location["name"],
            "vehicle": result["status"]
        })
    
    return drivers


async def demo_live_tracking():
    """Comprehensive live driver tracking demonstration"""
    
    console.print(Panel.fit(
        "🚛 Live Driver Tracking System Demo\n" +
        "Real-time GPS tracking, route optimization & driver management",
        style="bold blue"
    ))
    
    # Setup demo drivers
    console.print("🔧 Setting up demo drivers...")
    drivers = await setup_demo_drivers()
    
    # Display registered drivers
    driver_table = Table(title="📍 Registered Drivers", show_header=True, header_style="bold magenta")
    driver_table.add_column("Driver ID", style="cyan")
    driver_table.add_column("Name", style="green")
    driver_table.add_column("Location", style="yellow")
    driver_table.add_column("Vehicle", style="red")
    driver_table.add_column("Status", style="blue")
    
    for driver in drivers:
        driver_table.add_row(
            driver["driver_id"],
            driver["name"],
            driver["location"],
            "🏍️" if "bike" in driver["vehicle"].lower() else "🛵",
            "✅ Active"
        )
    
    console.print(driver_table)
    
    # Demo 1: Find nearby drivers
    console.print("\n🔍 **Demo 1: Finding Nearby Drivers**")
    search_location = GPSCoordinate(19.0760, 72.8777)  # Mumbai center
    
    nearby_tool = FindNearbyDriverTool()
    nearby_result = await nearby_tool._run(
        latitude=search_location.latitude,
        longitude=search_location.longitude,
        radius_km=10.0
    )
    
    console.print(f"   📍 Search Location: Mumbai Center")
    console.print(f"   🔍 Radius: {nearby_result['radius_km']} km")
    console.print(f"   ✅ Found: {nearby_result['drivers_found']} drivers")
    
    # Demo 2: Assign order to closest driver
    if nearby_result['nearby_drivers']:
        console.print("\n📦 **Demo 2: Order Assignment & Tracking**")
        
        closest_driver = nearby_result['nearby_drivers'][0]
        order_id = "ORD_LIVE_001"
        
        assign_tool = AssignDriverTool()
        assignment_result = await assign_tool._run(
            driver_id=closest_driver['driver_id'],
            order_id=order_id,
            pickup_lat=19.0596,  # Bandra
            pickup_lng=72.8295,
            delivery_lat=19.0176,  # Worli
            delivery_lng=72.8118
        )
        
        console.print(f"   🎯 Assigned Order: {order_id}")
        console.print(f"   👨‍🚗 Driver: {closest_driver['driver_name']}")
        console.print(f"   📍 Distance to Pickup: {assignment_result['distance_to_pickup_m']:.0f}m")
        console.print(f"   ⏰ Estimated Pickup: {assignment_result['estimated_pickup_time']} minutes")
        console.print(f"   🔗 Tracking URL: {assignment_result['tracking_url']}")
        
        # Demo 3: Real-time location updates
        console.print("\n📡 **Demo 3: Real-time Location Simulation**")
        
        track_tool = TrackDriverTool()
        
        # Simulate 5 location updates
        for i in range(1, 6):
            console.print(f"   📍 Update {i}/5: Simulating GPS movement...")
            
            # Get current status
            status = await track_tool._run(closest_driver['driver_id'])
            
            # Simulate movement
            movement_updates = await live_tracker.simulate_driver_movement(
                closest_driver['driver_id'],
                duration_minutes=1,
                update_interval_seconds=10
            )
            
            latest_update = movement_updates[-1] if movement_updates else status
            
            console.print(f"      🗺️  Location: {latest_update['location']['lat']:.4f}, {latest_update['location']['lng']:.4f}")
            console.print(f"      🏃 Speed: {latest_update['speed_kmh']:.1f} km/h")
            console.print(f"      🧭 Heading: {latest_update['heading']:.0f}°")
            
            if latest_update.get('geofence_alerts'):
                for alert in latest_update['geofence_alerts']:
                    console.print(f"      🚨 Geofence Alert: {alert['type']} zone entered!")
        
        # Demo 4: Driver tracking analytics
        console.print("\n📊 **Demo 4: Tracking Analytics**")
        
        analytics = await live_tracker.export_tracking_data(closest_driver['driver_id'])
        
        analytics_table = Table(show_header=True, header_style="bold cyan")
        analytics_table.add_column("Metric", style="green")
        analytics_table.add_column("Value", style="yellow")
        
        analytics_table.add_row("Total Locations Tracked", str(analytics['total_locations']))
        analytics_table.add_row("Tracking Duration", f"{analytics['tracking_duration_hours']:.2f} hours")
        analytics_table.add_row("Current Status", analytics['driver_info']['status'])
        analytics_table.add_row("Vehicle Type", analytics['driver_info']['vehicle_type'])
        analytics_table.add_row("Battery Level", f"{analytics['driver_info']['battery_level']}%")
        
        console.print(analytics_table)
    
    # Demo 5: Multiple driver status overview
    console.print("\n🎛️ **Demo 5: Fleet Management Dashboard**")
    
    fleet_table = Table(title="🚛 Live Fleet Status", show_header=True, header_style="bold magenta")
    fleet_table.add_column("Driver", style="cyan", width=12)
    fleet_table.add_column("Status", style="green", width=12)
    fleet_table.add_column("Location", style="yellow", width=15)
    fleet_table.add_column("Speed", style="red", width=8)
    fleet_table.add_column("Battery", style="blue", width=8)
    fleet_table.add_column("Order", style="magenta", width=12)
    
    for driver in drivers:
        status = await live_tracker.get_driver_status(driver['driver_id'])
        
        fleet_table.add_row(
            status['driver_name'],
            status['status'].replace('_', ' ').title(),
            f"{status['current_location']['lat']:.3f}, {status['current_location']['lng']:.3f}",
            f"{status['speed_kmh']:.1f} km/h",
            f"{status['battery_level']}%",
            status['order_id'] or "None"
        )
    
    console.print(fleet_table)
    
    # Summary
    console.print(Panel.fit(
        "🎉 Live Driver Tracking Demo Completed!\n\n" +
        "✅ Features Demonstrated:\n" +
        "• Real-time GPS tracking\n" +
        "• Driver registration & management\n" +
        "• Order assignment & routing\n" +
        "• Geofence monitoring\n" +
        "• Movement simulation\n" +
        "• Fleet analytics\n" +
        "• Multi-vehicle support\n\n" +
        "🚀 Ready for production with real GPS devices!",
        style="bold green"
    ))


if __name__ == "__main__":
    asyncio.run(demo_live_tracking())
