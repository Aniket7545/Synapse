"""
Project Synapse - Modular Agentic Coordinator
Main entry point for the crisis management system
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.core.coordinator import ProperCoordinator
from rich.console import Console
from rich.panel import Panel

console = Console()


async def main():
    """Main execution function"""
    
    if len(sys.argv) < 2:
        console.print(Panel.fit(
            "🤖 [bold blue]PROJECT SYNAPSE - MODULAR AGENTIC COORDINATOR[/bold blue]\n\n"
            "[bold yellow]Usage:[/bold yellow]\n"
            "python main.py \"Your crisis scenario\"\n\n"
            "[bold green]System Features:[/bold green]\n"
            "• 🧠 Coordinator: Analysis and routing only\n"
            "• 🤖 Agents: Full reasoning and tool execution\n"
            "• 🛠️ Dynamic tool creation when needed\n"
            "• 📊 Proper chain of thought tracking\n"
            "• 💰 Human approval for financial decisions\n\n"
            "[bold cyan]Example Scenarios:[/bold cyan]\n"
            "• \"Customer wants refund for damaged package\"\n"
            "• \"Delivery stuck in Mumbai traffic jam\"\n"
            "• \"Restaurant delay causing order issues\"\n\n"
            "[bold magenta]Modular Architecture:[/bold magenta]\n"
            "• src/core/ - Core system components\n"
            "• src/agents/ - Agent execution logic\n"
            "• src/tools/ - Dynamic tool management\n"
            "• src/utils/ - Display and utilities",
            title="🚀 Modular Crisis Management System",
            border_style="blue"
        ))
        return
    
    scenario = " ".join(sys.argv[1:])
    
    # Initialize and run coordinator
    coordinator = ProperCoordinator()
    await coordinator.handle_crisis(scenario)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        console.print(f"[red]System Error: {e}[/red]")
