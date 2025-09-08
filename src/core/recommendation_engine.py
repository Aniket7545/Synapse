"""
Contextual Recommendation Engine - Shows Only Relevant Information
"""

from typing import Dict, Any, List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

class ContextualRecommendation:
    """Shows only relevant recommendations based on crisis type"""
    
    def __init__(self):
        self.simple_crisis_types = ["delivery_delay", "customer_issue"]
        
    async def generate_recommendations(self, 
                                    query_analysis: Dict,
                                    agent_results: List[Dict],
                                    execution_metrics: Dict) -> Dict[str, Any]:
        """Generate contextual recommendations"""
        
        crisis_type = query_analysis.get('crisis_type', 'delivery_delay')
        severity = query_analysis.get('severity', 5)
        
        # For simple delays, show simple recommendations
        if crisis_type in self.simple_crisis_types and severity <= 6:
            return await self._generate_simple_recommendations(query_analysis, agent_results)
        else:
            return await self._generate_comprehensive_recommendations(query_analysis, agent_results, execution_metrics)
    
    async def _generate_simple_recommendations(self, query_analysis: Dict, agent_results: List) -> Dict[str, Any]:
        """Simple recommendations for basic issues"""
        
        crisis_type = query_analysis.get('crisis_type', 'delivery_delay')
        
        if crisis_type == "delivery_delay":
            recommendations = {
                "immediate_actions": [
                    {"action": "Contact customer with status update", "timeline": "Immediate"},
                    {"action": "Check delivery partner location", "timeline": "1-2 minutes"},
                    {"action": "Provide estimated delivery time", "timeline": "2-3 minutes"}
                ],
                "resolution_steps": [
                    "Track current delivery status",
                    "Communicate proactively with customer", 
                    "Ensure delivery completion with apology if needed"
                ]
            }
        else:
            recommendations = {
                "immediate_actions": [
                    {"action": "Acknowledge customer concern", "timeline": "Immediate"},
                    {"action": "Investigate the issue", "timeline": "2-5 minutes"},
                    {"action": "Provide resolution or compensation", "timeline": "5-10 minutes"}
                ]
            }
        
        # Simple display for basic issues
        self._display_simple_recommendations(recommendations, query_analysis)
        
        return {
            "type": "simple",
            "recommendations": recommendations,
            "confidence": sum(r.get('confidence', 0.7) for r in agent_results) / len(agent_results) if agent_results else 0.7
        }
    
    async def _generate_comprehensive_recommendations(self, 
                                                   query_analysis: Dict, 
                                                   agent_results: List, 
                                                   execution_metrics: Dict) -> Dict[str, Any]:
        """Comprehensive analysis for complex issues"""
        
        # Only show detailed business metrics for complex cases
        avg_confidence = sum(r.get('confidence', 0.5) for r in agent_results) / len(agent_results) if agent_results else 0.5
        severity = query_analysis.get('severity', 5)
        
        # Calculate business impact only for complex scenarios
        business_impact = {
            "estimated_cost": severity * 50,
            "potential_savings": max(0, severity * 30 - 50),
            "customer_impact": "High" if severity > 7 else "Medium"
        }
        
        recommendations = {
            "immediate_actions": [
                {"action": "Execute crisis protocol", "timeline": "0-5 minutes"},
                {"action": "Coordinate multi-team response", "timeline": "5-15 minutes"},
                {"action": "Monitor and adjust strategy", "timeline": "15-30 minutes"}
            ],
            "business_impact": business_impact
        }
        
        self._display_comprehensive_results(recommendations, query_analysis)
        
        return {
            "type": "comprehensive", 
            "recommendations": recommendations,
            "confidence": avg_confidence
        }
    
    def _display_simple_recommendations(self, recommendations: Dict, query_analysis: Dict):
        """Display simple, clean recommendations"""
        
        console.print(f"\n📋 [bold blue]Recommended Actions[/bold blue]")
        
        for i, action in enumerate(recommendations["immediate_actions"], 1):
            console.print(f"   {i}. {action['action']} - [dim]{action['timeline']}[/dim]")
        
        if "resolution_steps" in recommendations:
            console.print(f"\n🎯 [bold]Resolution Steps:[/bold]")
            for step in recommendations["resolution_steps"]:
                console.print(f"   • {step}")
    
    def _display_comprehensive_results(self, recommendations: Dict, query_analysis: Dict):
        """Display comprehensive analysis for complex issues"""
        
        # Action Plan Table
        actions_table = Table(title="🚀 Crisis Response Plan")
        actions_table.add_column("Action", style="cyan", width=40)
        actions_table.add_column("Timeline", style="yellow", width=15)
        
        for action in recommendations["immediate_actions"]:
            actions_table.add_row(action["action"], action["timeline"])
        
        console.print(actions_table)
        
        # Business Impact (only for severe cases)
        if query_analysis.get('severity', 0) > 7:
            impact = recommendations["business_impact"]
            impact_panel = Panel.fit(
                f"💰 [bold]Estimated Cost:[/bold] ₹{impact['estimated_cost']}\n"
                f"💡 [bold]Potential Savings:[/bold] ₹{impact['potential_savings']}\n"
                f"👥 [bold]Customer Impact:[/bold] {impact['customer_impact']}",
                title="📊 Business Impact",
                border_style="yellow"
            )
            console.print(f"\n{impact_panel}")

# Global recommendation engine
recommendation_engine = ContextualRecommendation()
