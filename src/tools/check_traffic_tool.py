"""
Check Traffic Tool - Real-time traffic data retrieval
Integrates with Indian traffic APIs (Mappls, TomTom, OSM)
"""

import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, Any, Optional
from src.tools.base_tool import BaseTool
from config.settings import settings


class CheckTrafficTool(BaseTool):
    """
    Tool for checking real-time traffic conditions
    Integrates with multiple Indian traffic data providers
    """
    
    name = "check_traffic"
    description = "Get real-time traffic conditions and congestion data for Indian routes"
    
    def __init__(self):
        super().__init__()
        self.api_timeout = 10
        self.retry_attempts = 3
        
    async def _run(self, origin: str, destination: str, city: str, **kwargs) -> Dict[str, Any]:
        """
        Execute traffic check with multiple API fallbacks
        """
        
        traffic_data = {
            "origin": origin,
            "destination": destination,
            "city": city,
            "timestamp": datetime.now().isoformat(),
            "data_sources": [],
            "traffic_level": "unknown",
            "estimated_delay_minutes": 0,
            "alternative_routes": [],
            "confidence": 0.5
        }
        
        # Try multiple APIs in order of preference
        apis_to_try = [
            ("mappls", self._get_mappls_traffic),
            ("tomtom", self._get_tomtom_traffic),
            ("osm", self._get_osm_traffic)
        ]
        
        for api_name, api_function in apis_to_try:
            try:
                api_data = await api_function(origin, destination, city)
                if api_data:
                    traffic_data.update(api_data)
                    traffic_data["data_sources"].append(api_name)
                    traffic_data["confidence"] = 0.9
                    break
            except Exception as e:
                self.logger.warning(f"Traffic API {api_name} failed: {str(e)}")
                continue
        
        # If no real API worked, use intelligent simulation
        if not traffic_data["data_sources"]:
            traffic_data.update(self._simulate_traffic_data(city))
            traffic_data["data_sources"].append("simulation")
            traffic_data["confidence"] = 0.6
        
        return traffic_data
    
    async def _get_mappls_traffic(self, origin: str, destination: str, city: str) -> Optional[Dict]:
        """
        Get traffic data from Mappls (MapMyIndia) API
        """
        
        if not settings.mappls_api_key:
            return None
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(self.api_timeout)) as session:
            url = "https://apis.mappls.com/advancedmaps/v1/directions"
            
            headers = {
                "Authorization": f"Bearer {settings.mappls_api_key}",
                "Content-Type": "application/json"
            }
            
            params = {
                "start": origin,
                "destination": destination,
                "traffic": "true",
                "geometries": "geojson"
            }
            
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._process_mappls_response(data)
                else:
                    self.logger.error(f"Mappls API error: {response.status}")
                    return None
    
    async def _get_tomtom_traffic(self, origin: str, destination: str, city: str) -> Optional[Dict]:
        """
        Get traffic data from TomTom API
        """
        
        if not settings.tomtom_api_key:
            return None
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(self.api_timeout)) as session:
            # Convert addresses to coordinates (simplified)
            origin_coords = await self._geocode_address(origin, session)
            dest_coords = await self._geocode_address(destination, session)
            
            if not origin_coords or not dest_coords:
                return None
            
            url = f"https://api.tomtom.com/routing/1/calculateRoute/{origin_coords}:{dest_coords}/json"
            
            params = {
                "key": settings.tomtom_api_key,
                "traffic": "true",
                "routeType": "fastest"
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._process_tomtom_response(data)
                else:
                    self.logger.error(f"TomTom API error: {response.status}")
                    return None
    
    async def _get_osm_traffic(self, origin: str, destination: str, city: str) -> Optional[Dict]:
        """
        Get routing data from OpenStreetMap (free alternative)
        """
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(self.api_timeout)) as session:
            # Convert addresses to coordinates using Nominatim
            origin_coords = await self._geocode_osm(origin, city, session)
            dest_coords = await self._geocode_osm(destination, city, session)
            
            if not origin_coords or not dest_coords:
                return None
            
            # Use OSRM for routing
            url = f"http://router.project-osrm.org/route/v1/driving/{origin_coords};{dest_coords}"
            
            params = {
                "overview": "false",
                "alternatives": "true"
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._process_osm_response(data)
                else:
                    self.logger.error(f"OSM API error: {response.status}")
                    return None
    
    def _process_mappls_response(self, data: Dict) -> Dict:
        """Process response from Mappls API"""
        
        routes = data.get("routes", [])
        if not routes:
            return {}
        
        primary_route = routes[0]
        duration_seconds = primary_route.get("duration", 0)
        distance_meters = primary_route.get("distance", 0)
        
        # Calculate traffic level based on speed
        if duration_seconds > 0:
            speed_kmh = (distance_meters / 1000) / (duration_seconds / 3600)
            traffic_level = self._determine_traffic_level(speed_kmh)
        else:
            traffic_level = "unknown"
        
        return {
            "traffic_level": traffic_level,
            "estimated_delay_minutes": max(0, (duration_seconds / 60) - 20),  # Assume 20 min base time
            "distance_km": distance_meters / 1000,
            "duration_minutes": duration_seconds / 60,
            "alternative_routes": self._extract_alternative_routes(routes)
        }
    
    def _process_tomtom_response(self, data: Dict) -> Dict:
        """Process response from TomTom API"""
        
        routes = data.get("routes", [])
        if not routes:
            return {}
        
        route = routes[0]
        summary = route.get("summary", {})
        
        travel_time = summary.get("travelTimeInSeconds", 0)
        traffic_delay = summary.get("trafficDelayInSeconds", 0)
        
        return {
            "traffic_level": self._determine_traffic_level_from_delay(traffic_delay),
            "estimated_delay_minutes": traffic_delay / 60,
            "distance_km": summary.get("lengthInMeters", 0) / 1000,
            "duration_minutes": travel_time / 60
        }
    
    def _process_osm_response(self, data: Dict) -> Dict:
        """Process response from OpenStreetMap/OSRM"""
        
        routes = data.get("routes", [])
        if not routes:
            return {}
        
        route = routes[0]
        duration_seconds = route.get("duration", 0)
        distance_meters = route.get("distance", 0)
        
        return {
            "traffic_level": "light",  # OSM doesn't provide real-time traffic
            "estimated_delay_minutes": 0,
            "distance_km": distance_meters / 1000,
            "duration_minutes": duration_seconds / 60,
            "note": "Based on static routing data"
        }
    
    def _simulate_traffic_data(self, city: str) -> Dict:
        """
        Intelligent traffic simulation based on city and time
        """
        
        current_hour = datetime.now().hour
        
        # City-specific traffic patterns
        city_patterns = {
            "mumbai": {
                "peak_hours": [(8, 11), (18, 21)],
                "base_delay": 15,
                "peak_multiplier": 2.5
            },
            "delhi": {
                "peak_hours": [(9, 12), (17, 20)],
                "base_delay": 12,
                "peak_multiplier": 2.0
            },
            "bangalore": {
                "peak_hours": [(8, 10), (18, 20)],
                "base_delay": 18,
                "peak_multiplier": 2.2
            }
        }
        
        pattern = city_patterns.get(city.lower(), city_patterns["delhi"])
        
        # Determine if current time is peak
        is_peak = any(start <= current_hour <= end for start, end in pattern["peak_hours"])
        
        if is_peak:
            delay = pattern["base_delay"] * pattern["peak_multiplier"]
            traffic_level = "heavy"
        else:
            delay = pattern["base_delay"]
            traffic_level = "moderate"
        
        return {
            "traffic_level": traffic_level,
            "estimated_delay_minutes": delay,
            "simulation_note": f"Simulated based on {city} traffic patterns"
        }
    
    def _determine_traffic_level(self, speed_kmh: float) -> str:
        """Determine traffic level based on average speed"""
        
        if speed_kmh < 10:
            return "severe"
        elif speed_kmh < 20:
            return "heavy"
        elif speed_kmh < 30:
            return "moderate"
        else:
            return "light"
    
    def _determine_traffic_level_from_delay(self, delay_seconds: int) -> str:
        """Determine traffic level based on delay"""
        
        delay_minutes = delay_seconds / 60
        
        if delay_minutes > 20:
            return "severe"
        elif delay_minutes > 10:
            return "heavy"
        elif delay_minutes > 5:
            return "moderate"
        else:
            return "light"
    
    async def _geocode_address(self, address: str, session: aiohttp.ClientSession) -> Optional[str]:
        """Geocode address to coordinates"""
        # Simplified - would use actual geocoding API
        return "19.0760,72.8777"  # Mumbai coordinates as fallback
    
    async def _geocode_osm(self, address: str, city: str, session: aiohttp.ClientSession) -> Optional[str]:
        """Geocode using OpenStreetMap Nominatim"""
        
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": f"{address}, {city}, India",
            "format": "json",
            "limit": 1
        }
        
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data:
                        return f"{data[0]['lon']},{data[0]['lat']}"
        except Exception:
            pass
        
        return None
    
    def _extract_alternative_routes(self, routes: List[Dict]) -> List[Dict]:
        """Extract alternative routes from API response"""
        
        alternatives = []
        
        for i, route in enumerate(routes[1:4]):  # Max 3 alternatives
            alternatives.append({
                "route_id": f"alt_{i+1}",
                "duration_minutes": route.get("duration", 0) / 60,
                "distance_km": route.get("distance", 0) / 1000,
                "description": f"Alternative route {i+1}"
            })
        
        return alternatives
