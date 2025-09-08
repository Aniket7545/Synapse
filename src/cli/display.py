"""
Rich display utilities for Project Synapse CLI
Beautiful terminal formatting and progress indicators
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from typing import Dict, Any

from config.settings import settings


class SynapseDisplay:
    """Rich display manager for Project Synapse"""
    
    def __init__(self):
        self.console = Console()
    
    def show_startup_banner(self):
        """Display Project Synapse startup banner"""
        
        banner = Text()
        banner.append("🚛 ", style="blue")
        banner.append("Project Synapse", style="bold blue")
        banner.append("\n")
        banner.append("India's AI-Powered Last-Mile Delivery Crisis Coordinator", style="cyan")
        banner.append(f"\n🌟 Version: {settings.app_version}", style="green")
        banner.append(f"\n🏙️ Default City: {settings.default_city.title()}", style="yellow")
        banner.append(f"\n🤖 LLM Provider: {settings.primary_model.upper()}", style="magenta")
        
        panel = Panel(
            banner,
            title="Welcome to Project Synapse",
            border_style="blue",
            padding=(1, 2)
        )
        
        self.console.print(panel)
    
    def show_scenario_start(self, state):
        """Display scenario start information"""
        
        scenario_info = f"""
🎯 Scenario: {state.scenario_id}
📍 Location: {state.location.city.title()} 
🚨 Disruption: {state.disruption_type.replace('_', ' ').title()}
⚠️ Severity: {state.severity_level}/10
👥 Stakeholders: Customer, Driver, Merchant
💰 Order Value: ₹{state.order.total_value}
        """
        
        panel = Panel(
            scenario_info.strip(),
            title="[bold green]Scenario Starting",
            border_style="green"
        )
        
        self.console.print(panel)
    
    def show_scenario_results(self, final_state: Dict[str, Any]):
        """Display final scenario results"""
        
        # Results summary table
        table = Table(title="Scenario Resolution Results")
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        table.add_column("Status", style="yellow")
        
        resolution = final_state.get("resolution_summary", {})
        
        table.add_row("Resolution Time", resolution.get("total_time", "N/A"), "✅ Fast")
        table.add_row("Agents Involved", str(resolution.get("agents_involved", 0)), "🤝 Multi-Agent")
        table.add_row("Tools Used", str(resolution.get("tools_used", 0)), "🛠️ Comprehensive") 
        table.add_row("Confidence Score", f"{resolution.get('confidence_score', 0):.2f}", "🎯 High")
        table.add_row("Customer Satisfaction", resolution.get("customer_satisfaction", "N/A"), "😊 Positive")
        
        self.console.print(table)
    
    def show_summary_table(self, final_state: Dict[str, Any]):
        """Show detailed summary table"""
        
        summary_table = Table(title="Detailed Resolution Summary")
        summary_table.add_column("Category", style="cyan")
        summary_table.add_column("Details", style="white")
        
        summary_table.add_row("Scenario ID", final_state.get("scenario_id", "N/A"))
        summary_table.add_row("Disruption Type", final_state.get("disruption_type", "N/A"))
        summary_table.add_row("Final Status", final_state.get("status", "N/A"))
        summary_table.add_row("Resolution Strategy", "Multi-agent coordination")
        
        self.console.print(summary_table)
