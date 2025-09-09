"""
Live Driver Tracking Tool for Project Synapse
Provides real-time GPS tracking capabilities for agents
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List
from src.tools.base_tool import BaseTool
from src.services.driver_tracking import live_tracker, GPSCoordinate, VehicleType, DriverStatus


class TrackDriverTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "track_driver"
        self.description = "Get real-time location and status of a driver"
    
    async def _run(self, driver_id: str) -> Dict[str, Any]:
        """Get comprehensive driver tracking information"""
        
        result = await live_tracker.get_driver_status(driver_id)
        
        if "error" in result:
            # Create mock driver for demo if not found
            mock_location = GPSCoordinate(19.0760 + (hash(driver_id) % 100) * 0.001, 
                                        72.8777 + (hash(driver_id) % 100) * 0.001)
            
            await live_tracker.register_driver(
                driver_id=driver_id,
                driver_name=f"Driver {driver_id[-3:]}",
                phone_number=f"+91-98765{driver_id[-5:]}",
                initial_location=mock_location,
                vehicle_type=VehicleType.BIKE
            )
            
            result = await live_tracker.get_driver_status(driver_id)
        
        return result


class FindNearbyDriverTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "find_nearby_drivers"
        self.description = "Find available drivers near a specific location"
    
    async def _run(
        self, 
        latitude: float, 
        longitude: float, 
        radius_km: float = 5.0,
        vehicle_type: str = None
    ) -> Dict[str, Any]:
        """Find nearby available drivers"""
        
        location = GPSCoordinate(latitude, longitude)
        vehicle_filter = VehicleType(vehicle_type) if vehicle_type else None
        
        nearby_drivers = await live_tracker.get_nearby_drivers(
            location, radius_km, vehicle_filter
        )
        
        return {
            "search_location": {"lat": latitude, "lng": longitude},
            "radius_km": radius_km,
            "vehicle_type_filter": vehicle_type,
            "drivers_found": len(nearby_drivers),
            "nearby_drivers": nearby_drivers
        }


class AssignDriverTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "assign_driver"
        self.description = "Assign a delivery order to a driver and start tracking"
    
    async def _run(
        self,
        driver_id: str,
        order_id: str,
        pickup_lat: float,
        pickup_lng: float,
        delivery_lat: float,
        delivery_lng: float
    ) -> Dict[str, Any]:
        """Assign order and start GPS tracking"""
        
        pickup_location = GPSCoordinate(pickup_lat, pickup_lng)
        delivery_location = GPSCoordinate(delivery_lat, delivery_lng)
        
        try:
            result = await live_tracker.assign_order(
                driver_id, order_id, pickup_location, delivery_location
            )
            return result
        except ValueError as e:
            # Create driver if not exists
            mock_location = GPSCoordinate(pickup_lat + 0.001, pickup_lng + 0.001)
            await live_tracker.register_driver(
                driver_id=driver_id,
                driver_name=f"Driver {driver_id[-3:]}",
                phone_number=f"+91-98765{driver_id[-5:]}",
                initial_location=mock_location
            )
            
            result = await live_tracker.assign_order(
                driver_id, order_id, pickup_location, delivery_location
            )
            return result


class UpdateDriverLocationTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "update_driver_location"
        self.description = "Update driver's real-time GPS location"
    
    async def _run(
        self,
        driver_id: str,
        latitude: float,
        longitude: float,
        speed_kmh: float = 0.0,
        heading: float = 0.0,
        accuracy: float = 5.0
    ) -> Dict[str, Any]:
        """Update driver location with GPS data"""
        
        new_location = GPSCoordinate(
            latitude=latitude,
            longitude=longitude,
            accuracy=accuracy,
            timestamp=datetime.now()
        )
        
        try:
            result = await live_tracker.update_driver_location(
                driver_id, new_location, speed_kmh, heading
            )
            return result
        except ValueError:
            return {
                "error": f"Driver {driver_id} not registered",
                "suggestion": "Use register_driver or assign_driver first"
            }


class GetLiveTrackingURLTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "get_tracking_url"
        self.description = "Generate live tracking URL for customer"
    
    async def _run(self, order_id: str) -> Dict[str, Any]:
        """Generate customer tracking URL"""
        
        base_url = "https://synapse.in/track"
        tracking_url = f"{base_url}/{order_id}"
        
        return {
            "order_id": order_id,
            "tracking_url": tracking_url,
            "qr_code_url": f"{base_url}/qr/{order_id}",
            "sms_link": f"{base_url}/sms/{order_id}",
            "features": [
                "Real-time driver location",
                "Estimated arrival time",
                "Route visualization",
                "Driver contact info",
                "Delivery status updates"
            ]
        }
