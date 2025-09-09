"""
Enhanced Chain of Thought Viewer
Shows the detailed chain of thought with tools and actions
"""

import json
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.json import JSON

console = Console()

def view_latest_chain_of_thought():
    """View the latest chain of thought log"""
    
    logs_dir = Path("logs")
    if not logs_dir.exists():
        console.print("❌ No logs directory found")
        return
    
    # Find the latest chain of thought log
    chain_files = list(logs_dir.glob("chain_of_thought_*.json"))
    if not chain_files:
        console.print("❌ No chain of thought logs found")
        return
    
    latest_file = max(chain_files, key=lambda f: f.stat().st_mtime)
    
    console.print(f"📄 [bold]Latest Chain of Thought Log:[/bold] {latest_file.name}")
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Display overview
        console.print(Panel.fit(
            f"🎯 [bold]Scenario ID:[/bold] {data.get('scenario_id', 'N/A')}\\n"
            f"⏰ [bold]Timestamp:[/bold] {data.get('timestamp', 'N/A')}\\n"
            f"🧠 [bold]Total Thoughts:[/bold] {data.get('total_thoughts', 0)}\\n"
            f"🤖 [bold]Agents Involved:[/bold] {', '.join(data.get('agents_involved', []))}",
            title="📊 Chain of Thought Overview",
            border_style="blue"
        ))
        
        # Display detailed chain of thought
        if "chain_of_thought" in data and data["chain_of_thought"]:
            console.print("\\n🧠 [bold]Detailed Chain of Thought:[/bold]")
            
            for thought in data["chain_of_thought"]:
                console.print(f"\\n{'='*80}")
                console.print(f"🔢 [bold]Step {thought.get('step', 'N/A')}:[/bold] {thought.get('agent', 'Unknown Agent').replace('_', ' ').title()}")
                console.print('='*80)
                
                # Basic info
                details_table = Table(show_header=False, box=None, padding=(0, 1))
                details_table.add_row("🎯 Type:", thought.get('type', 'N/A').title())
                details_table.add_row("📝 Description:", thought.get('description', 'N/A'))
                details_table.add_row("⏱️ Duration:", f"{thought.get('duration_seconds', 0):.2f} seconds")
                details_table.add_row("📊 Confidence:", f"{thought.get('confidence', 0):.2f}")
                console.print(details_table)
                
                # Tools used
                tools_used = thought.get('tools_used', [])
                if tools_used:
                    console.print(f"\\n🛠️ [bold]Tools Executed ({len(tools_used)}):[/bold]")
                    for i, tool in enumerate(tools_used, 1):
                        console.print(f"   {i}. {tool}")
                        
                        # Show tool results if available
                        tool_results = thought.get('tool_results', {})
                        if tool in tool_results:
                            console.print(f"      ✅ Result: {tool_results[tool]}")
                else:
                    console.print("\\n🛠️ [dim]No tools executed[/dim]")
                
                # Actions taken
                actions_taken = thought.get('actions_taken', [])
                if actions_taken:
                    console.print(f"\\n🎯 [bold]Actions Taken ({len(actions_taken)}):[/bold]")
                    for i, action in enumerate(actions_taken, 1):
                        console.print(f"   {i}. {action}")
                else:
                    console.print("\\n🎯 [dim]No actions recorded[/dim]")
                
                # Reasoning
                reasoning = thought.get('reasoning', '')
                if reasoning:
                    console.print(f"\\n💭 [bold]Agent Reasoning:[/bold]")
                    # Truncate long reasoning for readability
                    if len(reasoning) > 200:
                        console.print(f"   {reasoning[:200]}...")
                    else:
                        console.print(f"   {reasoning}")
        
        # Display execution results summary
        if "execution_results" in data:
            console.print(f"\\n{'='*80}")
            console.print("📊 [bold]Execution Results Summary:[/bold]")
            console.print('='*80)
            
            for result in data["execution_results"]:
                agent_name = result.get("agent", "Unknown")
                tools_count = len(result.get("tools_used", []))
                actions_count = len(result.get("actions_taken", []))
                
                result_table = Table(title=f"{agent_name.replace('_', ' ').title()} Results")
                result_table.add_column("Metric", style="cyan")
                result_table.add_column("Value", style="green")
                
                result_table.add_row("Tools Executed", str(tools_count))
                result_table.add_row("Actions Taken", str(actions_count))
                result_table.add_row("Confidence", f"{result.get('confidence', 0):.2f}")
                result_table.add_row("Routing Decision", result.get('routing_decision', 'N/A'))
                
                console.print(result_table)
        
        console.print(f"\\n✅ [bold green]Chain of Thought Analysis Complete![/bold green]")
        
    except Exception as e:
        console.print(f"❌ Error reading log file: {e}")

if __name__ == "__main__":
    console.print("🔍 [bold blue]Enhanced Chain of Thought Viewer[/bold blue]\\n")
    view_latest_chain_of_thought()
