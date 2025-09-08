"""
Indian Market Context Utilities
Cultural, linguistic, and market-specific helpers
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json

class IndianContextManager:
    """Manages Indian market context and cultural considerations"""
    
    def __init__(self):
        self.city_data = self._load_city_data()
        self.cultural_patterns = self._load_cultural_patterns()
    
    def _load_city_data(self) -> Dict[str, Any]:
        """Load Indian city-specific data"""
        return {
            "mumbai": {
                "timezone": "Asia/Kolkata",
                "peak_traffic_hours": ["9-11", "18-21"],
                "monsoon_months": [6, 7, 8, 9],
                "major_business_areas": ["BKC", "Nariman Point", "Andheri"],
                "delivery_challenges": ["traffic", "monsoon", "narrow_lanes"],
                "preferred_languages": ["hindi", "marathi", "english"],
                "cultural_notes": "Fast-paced, time-conscious customers"
            },
            "delhi": {
                "timezone": "Asia/Kolkata",
                "peak_traffic_hours": ["8-11", "17-21"], 
                "monsoon_months": [7, 8, 9],
                "major_business_areas": ["CP", "Gurgaon", "Noida"],
                "delivery_challenges": ["traffic", "pollution", "weather_extremes"],
                "preferred_languages": ["hindi", "english"],
                "cultural_notes": "Formal communication preferred"
            },
            "bangalore": {
                "timezone": "Asia/Kolkata",
                "peak_traffic_hours": ["8-10", "17-20"],
                "monsoon_months": [6, 7, 8, 9, 10],
                "major_business_areas": ["Koramangala", "Whitefield", "Electronic City"],
                "delivery_challenges": ["traffic", "road_construction", "tech_crowd"],
                "preferred_languages": ["english", "kannada", "hindi"],
                "cultural_notes": "Tech-savvy, app-native customers"
            }
        }
    
    def _load_cultural_patterns(self) -> Dict[str, Any]:
        """Load cultural patterns and preferences"""
        return {
            "communication_styles": {
                "north_india": {"tone": "formal", "language_mix": "hindi_english"},
                "south_india": {"tone": "polite", "language_mix": "english_local"},
                "west_india": {"tone": "direct", "language_mix": "english_hindi"},
                "east_india": {"tone": "respectful", "language_mix": "bengali_english"}
            },
            "festival_calendar": {
                "diwali": {"impact": "very_high", "typical_dates": "oct_nov"},
                "holi": {"impact": "high", "typical_dates": "mar"},
                "eid": {"impact": "high", "typical_dates": "variable"},
                "durga_puja": {"impact": "high", "regions": ["west_bengal"]},
                "ganesh_chaturthi": {"impact": "high", "regions": ["maharashtra"]}
            },
            "business_hours": {
                "standard": {"start": "10:00", "end": "19:00"},
                "lunch_break": {"start": "13:00", "end": "14:00"},
                "weekend_pattern": "saturday_half_sunday_off"
            }
        }
    
    def get_city_context(self, city: str) -> Dict[str, Any]:
        """Get comprehensive context for a specific city"""
        return self.city_data.get(city.lower(), self.city_data["mumbai"])
    
    def get_appropriate_language(self, city: str, customer_preference: str = None) -> str:
        """Determine appropriate language for communication"""
        city_context = self.get_city_context(city)
        preferred_languages = city_context["preferred_languages"]
        
        if customer_preference and customer_preference in preferred_languages:
            return customer_preference
        
        # Default to most common language for the city
        return preferred_languages[0] if preferred_languages else "english"
    
    def get_cultural_communication_style(self, city: str) -> Dict[str, str]:
        """Get appropriate communication style for region"""
        region_map = {
            "mumbai": "west_india", "pune": "west_india",
            "delhi": "north_india", "gurgaon": "north_india",
            "bangalore": "south_india", "chennai": "south_india", "hyderabad": "south_india",
            "kolkata": "east_india"
        }
        
        region = region_map.get(city.lower(), "north_india")
        return self.cultural_patterns["communication_styles"][region]
    
    def is_festival_period(self, date: datetime = None) -> Dict[str, Any]:
        """Check if current date falls in festival period"""
        if not date:
            date = datetime.now()
        
        # Simplified festival detection
        month = date.month
        
        festival_months = {
            3: "holi",
            10: "diwali", 
            11: "diwali"
        }
        
        current_festival = festival_months.get(month)
        
        return {
            "is_festival": current_festival is not None,
            "festival_name": current_festival,
            "impact_level": self.cultural_patterns["festival_calendar"].get(current_festival, {}).get("impact", "none"),
            "delivery_adjustments": self._get_festival_adjustments(current_festival) if current_festival else []
        }
    
    def _get_festival_adjustments(self, festival: str) -> List[str]:
        """Get delivery adjustments needed during festivals"""
        adjustments = {
            "diwali": [
                "Expect increased order volumes",
                "Plan for gift deliveries",
                "Extended delivery windows",
                "Higher customer satisfaction expectations"
            ],
            "holi": [
                "Weather-resistant packaging",
                "Avoid light-colored uniforms",
                "Extended delivery times due to celebrations"
            ],
            "eid": [
                "Halal food verification",
                "Respectful timing of deliveries",
                "Gift packaging options"
            ]
        }
        
        return adjustments.get(festival, [])
    
    def format_indian_currency(self, amount: float) -> str:
        """Format currency in Indian style"""
        return f"₹{amount:,.2f}"
    
    def get_peak_delivery_hours(self, city: str) -> List[str]:
        """Get peak delivery hours for specific city"""
        city_context = self.get_city_context(city)
        return city_context["peak_traffic_hours"]
    
    def assess_delivery_difficulty(self, city: str, area: str = None) -> Dict[str, Any]:
        """Assess delivery difficulty for city/area"""
        city_context = self.get_city_context(city)
        challenges = city_context["delivery_challenges"]
        
        difficulty_score = len(challenges) / 5  # Normalized score
        
        return {
            "difficulty_score": difficulty_score,
            "primary_challenges": challenges,
            "recommendations": self._get_delivery_recommendations(challenges),
            "estimated_time_multiplier": 1 + (difficulty_score * 0.5)
        }
    
    def _get_delivery_recommendations(self, challenges: List[str]) -> List[str]:
        """Get recommendations based on delivery challenges"""
        recommendations = []
        
        challenge_solutions = {
            "traffic": "Use traffic-optimized routing and real-time updates",
            "monsoon": "Waterproof packaging and weather tracking",
            "narrow_lanes": "Use smaller vehicles and local area knowledge", 
            "pollution": "Protective gear for delivery partners",
            "weather_extremes": "Temperature-controlled storage when needed"
        }
        
        for challenge in challenges:
            if challenge in challenge_solutions:
                recommendations.append(challenge_solutions[challenge])
        
        return recommendations
