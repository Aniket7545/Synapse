"""
Live Driver Tracking Service for Project Synapse
Real-time GPS tracking, route optimization, and location updates
"""

import asyncio
import json
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import random
import logging

logger = logging.getLogger(__name__)


class DriverStatus(str, Enum):
    IDLE = "idle"
    ASSIGNED = "assigned"
    PICKING_UP = "picking_up"
    IN_TRANSIT = "in_transit"
    DELIVERING = "delivering"
    COMPLETED = "completed"
    OFFLINE = "offline"


class VehicleType(str, Enum):
    BIKE = "bike"
    SCOOTER = "scooter"
    CAR = "car"
    BICYCLE = "bicycle"


@dataclass
class GPSCoordinate:
    latitude: float
    longitude: float
    accuracy: float = 5.0  # meters
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def distance_to(self, other: 'GPSCoordinate') -> float:
        """Calculate distance to another coordinate in meters using Haversine formula"""
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(self.latitude)
        lat2_rad = math.radians(other.latitude)
        delta_lat = math.radians(other.latitude - self.latitude)
        delta_lon = math.radians(other.longitude - self.longitude)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c


@dataclass
class DriverLocation:
    driver_id: str
    driver_name: str
    phone_number: str
    current_position: GPSCoordinate
    destination: Optional[GPSCoordinate] = None
    status: DriverStatus = DriverStatus.IDLE
    vehicle_type: VehicleType = VehicleType.BIKE
    battery_level: int = 100  # For electric vehicles
    speed_kmh: float = 0.0
    heading: float = 0.0  # degrees, 0 = North
    last_update: datetime = None
    order_id: Optional[str] = None
    
    def __post_init__(self):
        if self.last_update is None:
            self.last_update = datetime.now()


class LiveDriverTracker:
    """Real-time driver tracking system with GPS integration"""
    
    def __init__(self):
        self.active_drivers: Dict[str, DriverLocation] = {}
        self.location_history: Dict[str, List[GPSCoordinate]] = {}
        self.geofences: Dict[str, Dict] = {}
        self.tracking_active = False
        
        # Mumbai coordinates for simulation
        self.city_bounds = {
            "mumbai": {
                "center": GPSCoordinate(19.0760, 72.8777),
                "radius_km": 50
            },
            "delhi": {
                "center": GPSCoordinate(28.6139, 77.2090),
                "radius_km": 60
            },
            "bangalore": {
                "center": GPSCoordinate(12.9716, 77.5946),
                "radius_km": 40
            }
        }
    
    async def register_driver(
        self, 
        driver_id: str, 
        driver_name: str, 
        phone_number: str,
        initial_location: GPSCoordinate,
        vehicle_type: VehicleType = VehicleType.BIKE
    ) -> Dict[str, Any]:
        """Register a new driver for tracking"""
        
        driver_location = DriverLocation(
            driver_id=driver_id,
            driver_name=driver_name,
            phone_number=phone_number,
            current_position=initial_location,
            vehicle_type=vehicle_type,
            status=DriverStatus.IDLE
        )
        
        self.active_drivers[driver_id] = driver_location
        self.location_history[driver_id] = [initial_location]
        
        logger.info(f"Driver {driver_name} registered for tracking")
        
        return {
            "driver_id": driver_id,
            "status": "registered",
            "current_location": {
                "lat": initial_location.latitude,
                "lng": initial_location.longitude,
                "accuracy": initial_location.accuracy
            },
            "tracking_enabled": True
        }
    
    async def update_driver_location(
        self, 
        driver_id: str, 
        new_location: GPSCoordinate,
        speed_kmh: float = 0.0,
        heading: float = 0.0
    ) -> Dict[str, Any]:
        """Update driver's real-time location"""
        
        if driver_id not in self.active_drivers:
            raise ValueError(f"Driver {driver_id} not registered")
        
        driver = self.active_drivers[driver_id]
        old_location = driver.current_position
        
        # Calculate speed if not provided
        if speed_kmh == 0.0 and len(self.location_history[driver_id]) > 0:
            time_diff = (new_location.timestamp - old_location.timestamp).total_seconds()
            if time_diff > 0:
                distance_m = old_location.distance_to(new_location)
                speed_kmh = (distance_m / time_diff) * 3.6  # Convert m/s to km/h
        
        # Update driver location
        driver.current_position = new_location
        driver.speed_kmh = speed_kmh
        driver.heading = heading
        driver.last_update = datetime.now()
        
        # Add to history
        self.location_history[driver_id].append(new_location)
        
        # Keep only last 100 locations to prevent memory issues
        if len(self.location_history[driver_id]) > 100:
            self.location_history[driver_id] = self.location_history[driver_id][-100:]
        
        # Check geofences
        geofence_alerts = await self._check_geofences(driver_id, new_location)
        
        return {
            "driver_id": driver_id,
            "location": {
                "lat": new_location.latitude,
                "lng": new_location.longitude,
                "accuracy": new_location.accuracy
            },
            "speed_kmh": speed_kmh,
            "heading": heading,
            "status": driver.status.value,
            "timestamp": new_location.timestamp.isoformat(),
            "geofence_alerts": geofence_alerts
        }
    
    async def assign_order(
        self, 
        driver_id: str, 
        order_id: str, 
        pickup_location: GPSCoordinate,
        delivery_location: GPSCoordinate
    ) -> Dict[str, Any]:
        """Assign an order to a driver and start tracking"""
        
        if driver_id not in self.active_drivers:
            raise ValueError(f"Driver {driver_id} not registered")
        
        driver = self.active_drivers[driver_id]
        driver.order_id = order_id
        driver.destination = pickup_location
        driver.status = DriverStatus.ASSIGNED
        
        # Create geofences for pickup and delivery
        await self._create_delivery_geofences(order_id, pickup_location, delivery_location)
        
        # Calculate initial ETA
        distance_to_pickup = driver.current_position.distance_to(pickup_location)
        estimated_time = self._estimate_travel_time(distance_to_pickup, driver.vehicle_type)
        
        return {
            "driver_id": driver_id,
            "order_id": order_id,
            "status": "assigned",
            "distance_to_pickup_m": distance_to_pickup,
            "estimated_pickup_time": estimated_time,
            "tracking_url": f"https://synapse.in/track/{order_id}",
            "driver_location": {
                "lat": driver.current_position.latitude,
                "lng": driver.current_position.longitude
            }
        }
    
    async def get_driver_status(self, driver_id: str) -> Dict[str, Any]:
        """Get comprehensive driver status and location"""
        
        if driver_id not in self.active_drivers:
            return {"error": "Driver not found"}
        
        driver = self.active_drivers[driver_id]
        
        # Calculate additional metrics
        eta_to_destination = None
        distance_to_destination = None
        
        if driver.destination:
            distance_to_destination = driver.current_position.distance_to(driver.destination)
            eta_to_destination = self._estimate_travel_time(distance_to_destination, driver.vehicle_type)
        
        return {
            "driver_id": driver_id,
            "driver_name": driver.driver_name,
            "phone_number": driver.phone_number,
            "current_location": {
                "lat": driver.current_position.latitude,
                "lng": driver.current_position.longitude,
                "accuracy": driver.current_position.accuracy
            },
            "status": driver.status.value,
            "vehicle_type": driver.vehicle_type.value,
            "speed_kmh": driver.speed_kmh,
            "heading": driver.heading,
            "battery_level": driver.battery_level,
            "order_id": driver.order_id,
            "distance_to_destination_m": distance_to_destination,
            "eta_minutes": eta_to_destination,
            "last_update": driver.last_update.isoformat(),
            "tracking_active": True
        }
    
    async def get_nearby_drivers(
        self, 
        location: GPSCoordinate, 
        radius_km: float = 5.0,
        vehicle_type: Optional[VehicleType] = None
    ) -> List[Dict[str, Any]]:
        """Find nearby available drivers"""
        
        nearby_drivers = []
        
        for driver_id, driver in self.active_drivers.items():
            if driver.status not in [DriverStatus.IDLE, DriverStatus.COMPLETED]:
                continue
            
            if vehicle_type and driver.vehicle_type != vehicle_type:
                continue
            
            distance_m = location.distance_to(driver.current_position)
            distance_km = distance_m / 1000
            
            if distance_km <= radius_km:
                nearby_drivers.append({
                    "driver_id": driver_id,
                    "driver_name": driver.driver_name,
                    "distance_km": round(distance_km, 2),
                    "vehicle_type": driver.vehicle_type.value,
                    "battery_level": driver.battery_level,
                    "location": {
                        "lat": driver.current_position.latitude,
                        "lng": driver.current_position.longitude
                    }
                })
        
        # Sort by distance
        nearby_drivers.sort(key=lambda x: x["distance_km"])
        
        return nearby_drivers
    
    async def simulate_driver_movement(
        self, 
        driver_id: str, 
        duration_minutes: int = 10,
        update_interval_seconds: int = 30
    ) -> List[Dict[str, Any]]:
        """Simulate realistic driver movement for testing"""
        
        if driver_id not in self.active_drivers:
            raise ValueError(f"Driver {driver_id} not registered")
        
        driver = self.active_drivers[driver_id]
        updates = []
        
        total_updates = (duration_minutes * 60) // update_interval_seconds
        
        for i in range(total_updates):
            # Simulate realistic GPS drift and movement
            lat_drift = random.uniform(-0.0001, 0.0001)  # ~10m drift
            lng_drift = random.uniform(-0.0001, 0.0001)
            
            # Simulate movement towards destination if assigned
            if driver.destination and driver.status == DriverStatus.IN_TRANSIT:
                # Move slightly towards destination
                lat_move = (driver.destination.latitude - driver.current_position.latitude) * 0.1
                lng_move = (driver.destination.longitude - driver.current_position.longitude) * 0.1
                lat_drift += lat_move
                lng_drift += lng_move
            
            new_location = GPSCoordinate(
                latitude=driver.current_position.latitude + lat_drift,
                longitude=driver.current_position.longitude + lng_drift,
                accuracy=random.uniform(3.0, 8.0),
                timestamp=datetime.now()
            )
            
            speed = random.uniform(15.0, 40.0)  # 15-40 km/h
            heading = random.uniform(0.0, 360.0)
            
            update = await self.update_driver_location(
                driver_id, new_location, speed, heading
            )
            updates.append(update)
            
            await asyncio.sleep(1)  # Small delay for simulation
        
        return updates
    
    async def _create_delivery_geofences(
        self, 
        order_id: str, 
        pickup_location: GPSCoordinate,
        delivery_location: GPSCoordinate
    ):
        """Create geofences for pickup and delivery locations"""
        
        self.geofences[f"{order_id}_pickup"] = {
            "center": pickup_location,
            "radius_m": 100,
            "type": "pickup",
            "order_id": order_id
        }
        
        self.geofences[f"{order_id}_delivery"] = {
            "center": delivery_location,
            "radius_m": 100,
            "type": "delivery",
            "order_id": order_id
        }
    
    async def _check_geofences(
        self, 
        driver_id: str, 
        location: GPSCoordinate
    ) -> List[Dict[str, Any]]:
        """Check if driver has entered any geofences"""
        
        alerts = []
        
        for geofence_id, geofence in self.geofences.items():
            distance = location.distance_to(geofence["center"])
            
            if distance <= geofence["radius_m"]:
                alerts.append({
                    "geofence_id": geofence_id,
                    "type": geofence["type"],
                    "order_id": geofence["order_id"],
                    "entered_at": datetime.now().isoformat(),
                    "distance_m": round(distance, 1)
                })
        
        return alerts
    
    def _estimate_travel_time(
        self, 
        distance_m: float, 
        vehicle_type: VehicleType
    ) -> int:
        """Estimate travel time in minutes based on distance and vehicle type"""
        
        # Average speeds by vehicle type in urban areas
        avg_speeds = {
            VehicleType.BIKE: 25,      # km/h
            VehicleType.SCOOTER: 20,   # km/h  
            VehicleType.CAR: 18,       # km/h (slower due to traffic)
            VehicleType.BICYCLE: 12    # km/h
        }
        
        speed_kmh = avg_speeds.get(vehicle_type, 20)
        distance_km = distance_m / 1000
        time_hours = distance_km / speed_kmh
        
        return max(1, int(time_hours * 60))  # At least 1 minute
    
    async def export_tracking_data(self, driver_id: str) -> Dict[str, Any]:
        """Export tracking data for analytics"""
        
        if driver_id not in self.active_drivers:
            return {"error": "Driver not found"}
        
        driver = self.active_drivers[driver_id]
        history = self.location_history.get(driver_id, [])
        
        return {
            "driver_info": asdict(driver),
            "location_history": [
                {
                    "lat": loc.latitude,
                    "lng": loc.longitude,
                    "accuracy": loc.accuracy,
                    "timestamp": loc.timestamp.isoformat()
                }
                for loc in history
            ],
            "total_locations": len(history),
            "tracking_duration_hours": (
                (history[-1].timestamp - history[0].timestamp).total_seconds() / 3600
                if len(history) >= 2 else 0
            )
        }


# Global tracker instance
live_tracker = LiveDriverTracker()
