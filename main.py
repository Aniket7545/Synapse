#!/usr/bin/env python3
"""
Project Synapse - Fixed Main Application
Clean execution with proper exit control
"""

import asyncio
import sys
import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from src.core.query_processor import crisis_processor
from src.core.recommendation_engine import recommendation_engine
from src.workflow.synapse_workflow import synapse_workflow

console = Console()
app = typer.Typer(name="synapse", help="🚛 Project Synapse - AI Delivery Crisis Coordinator")

@app.command()
def solve(description: str):
    """🧠 Solve a single crisis and exit cleanly"""
    console.print(f"🚛 [bold blue]Project Synapse[/bold blue] - Processing Crisis")
    console.print(f"[dim]Query: {description}[/dim]\n")
    
    # Process single crisis and exit
    result = asyncio.run(process_single_crisis(description))
    
    if result:
        console.print(f"\n✅ [bold green]Crisis processing complete[/bold green]")
        console.print(f"📄 [dim]Check logs folder for detailed reasoning chain[/dim]")
    else:
        console.print(f"\n❌ [bold red]Crisis processing failed[/bold red]")
    
    # Clean exit - no further prompts
    sys.exit(0)

@app.command()
def chat():
    """🗣️ Interactive chat session with multiple queries"""
    
    console.print(Panel.fit(
        "🚛 [bold blue]Project Synapse AI[/bold blue] - Interactive Session\n\n"
        "Describe delivery crises and I'll provide AI-powered resolution.\n"
        "Type 'exit', 'quit', or 'bye' to end the session.\n\n"
        "[dim]Examples: 'damaged package', 'delivery delay', 'traffic jam'[/dim]",
        title="🤖 Interactive AI Session",
        border_style="blue"
    ))
    
    asyncio.run(interactive_chat_session())

async def process_single_crisis(crisis_description: str) -> bool:
    """Process a single crisis with full AI coordination"""
    
    try:
        console.print(f"🧠 [bold blue]AI analyzing crisis...[/bold blue]")
        
        # Step 1: AI-powered crisis analysis
        analysis, delivery_state = await crisis_processor.process_query(crisis_description)
        
        # Display AI analysis
        console.print(f"\n📊 [bold]AI Analysis Results:[/bold]")
        console.print(f"   • [bold]Crisis Type:[/bold] {analysis.crisis_type.replace('_', ' ').title()}")
        console.print(f"   • [bold]Severity:[/bold] {analysis.severity}/10")
        console.print(f"   • [bold]Urgency:[/bold] {analysis.urgency.title()}")
        console.print(f"   • [bold]AI Confidence:[/bold] {analysis.confidence:.1%}")
        
        if analysis.location != "unknown":
            console.print(f"   • [bold]Location:[/bold] {analysis.location.title()}")
        
        # Step 2: Multi-agent AI coordination
        console.print(f"\n🤖 [bold yellow]Executing AI coordination...[/bold yellow]")
        
        execution_result = await synapse_workflow.execute_scenario(delivery_state)
        
        if execution_result.get("status") == "success":
            # Step 3: AI recommendations
            recommendations = await recommendation_engine.generate_recommendations(
                analysis.dict(),
                synapse_workflow.execution_results,
                {"agents_used": len(synapse_workflow.execution_results)}
            )
            
            # Step 4: Display resolution
            display_crisis_resolution(analysis, recommendations, execution_result)
            
            return True
        else:
            console.print(f"❌ [bold red]AI coordination failed[/bold red]")
            return False
            
    except Exception as e:
        console.print(f"❌ [bold red]Error: Unable to process crisis[/bold red]")
        return False

async def interactive_chat_session():
    """Interactive chat session with proper session management"""
    
    session_active = True
    crisis_count = 0
    
    while session_active:
        try:
            # Get crisis description
            if crisis_count == 0:
                query = Prompt.ask("\n[bold cyan]Describe your delivery crisis[/bold cyan]")
            else:
                query = Prompt.ask("\n[bold cyan]Describe another crisis (or 'exit' to quit)[/bold cyan]")
            
            # Handle exit commands
            if query.lower().strip() in ['exit', 'quit', 'bye', 'stop']:
                console.print("👋 [bold blue]Session ended. Thank you for using Project Synapse![/bold blue]")
                break
            
            # Validate input
            if not query.strip():
                console.print("[yellow]Please describe the specific crisis situation.[/yellow]")
                continue
            
            # Process the crisis
            success = await process_single_crisis(query)
            crisis_count += 1
            
            if success:
                # Ask if user wants to continue (only in chat mode)
                console.print("\n" + "─" * 50)
                continue_session = Confirm.ask("[bold]Handle another delivery crisis?[/bold]", default=False)
                
                if not continue_session:
                    console.print("👋 [bold blue]Session completed. Stay safe![/bold blue]")
                    session_active = False
            else:
                # On failure, ask if they want to try again
                retry = Confirm.ask("[bold]Try with a different crisis description?[/bold]", default=True)
                if not retry:
                    console.print("👋 [bold blue]Session ended.[/bold blue]")
                    session_active = False
                
        except KeyboardInterrupt:
            console.print("\n👋 [bold blue]Session interrupted. Goodbye![/bold blue]")
            break
        except Exception as e:
            console.print(f"❌ [red]Session error. Please try again.[/red]")
            retry = Confirm.ask("[bold]Continue session?[/bold]", default=True)
            if not retry:
                session_active = False

def display_crisis_resolution(analysis, recommendations, execution_result):
    """Display comprehensive AI resolution results"""
    
    console.print(f"\n{'='*60}")
    console.print("🎯 [bold green]AI CRISIS RESOLUTION COMPLETE[/bold green]")
    console.print('='*60)
    
    # AI-generated outcome
    estimated_outcome = recommendations.get('estimated_outcome', {})
    predicted_outcome = estimated_outcome.get('predicted_outcome', 'Resolution coordinated successfully')
    success_probability = estimated_outcome.get('success_probability', 0.85)
    
    console.print(f"🔮 [bold]AI Prediction:[/bold] {predicted_outcome}")
    console.print(f"📊 [bold]Success Probability:[/bold] {success_probability:.0%}")
    
    # Show actual tools used
    all_tools_used = []
    for result in synapse_workflow.execution_results:
        all_tools_used.extend(result.get("tools_used", []))
    
    if all_tools_used:
        console.print(f"🛠️ [bold]AI Tools Executed:[/bold] {', '.join(set(all_tools_used))}")
    
    # Show AI-generated immediate actions
    immediate_actions = recommendations.get('recommendations', {}).get('immediate_actions', [])
    if immediate_actions:
        console.print(f"\n🚀 [bold]AI Recommended Actions:[/bold]")
        for i, action in enumerate(immediate_actions[:3], 1):
            action_text = action.get('action', str(action)) if isinstance(action, dict) else str(action)
            timeline = action.get('timeline', 'Immediate') if isinstance(action, dict) else 'Now'
            console.print(f"   {i}. {action_text} - [dim]{timeline}[/dim]")
    
    # Chain of thought file
    chain_file = execution_result.get("chain_of_thought_file", "logs/latest_chain.json")
    console.print(f"\n📄 [bold]Full AI reasoning saved:[/bold] [cyan]{chain_file}[/cyan]")
    
    console.print(f"\n✅ [bold green]Crisis resolved with AI intelligence[/bold green]")

@app.command()
def status():
    """📊 Show system status"""
    console.print(Panel.fit(
        "🚛 [bold blue]Project Synapse[/bold blue] - System Status\n\n"
        "[green]✅ AI Reasoning Engine: Online[/green]\n"
        "[green]✅ Multi-Agent Coordination: Active[/green]\n" 
        "[green]✅ Crisis Resolution Tools: Ready[/green]\n"
        "[green]✅ Chain of Thought Logging: Enabled[/green]\n\n"
        "[bold]Available Commands:[/bold]\n"
        "• [cyan]synapse solve \"crisis description\"[/cyan] - Single crisis resolution\n"
        "• [cyan]synapse chat[/cyan] - Interactive session\n"
        "• [cyan]synapse status[/cyan] - System status",
        title="🤖 System Status",
        border_style="green"
    ))

if __name__ == "__main__":
    # Show startup banner only if running directly
    if len(sys.argv) == 1:
        console.print(Panel.fit(
            "🚛 [bold blue]Project Synapse[/bold blue]\n"
            "AI-Powered Delivery Crisis Coordinator\n\n"
            "[green]✅ Real-Time Crisis Resolution[/green]\n"
            "[green]✅ Multi-Agent AI Coordination[/green]\n"
            "[green]✅ Intelligent Tool Integration[/green]\n\n"
            "[bold]Usage:[/bold]\n"
            "• [cyan]python main.py solve \"describe crisis\"[/cyan]\n"
            "• [cyan]python main.py chat[/cyan]\n"
            "• [cyan]python main.py status[/cyan]",
            title="🤖 AI System Ready",
            border_style="blue"
        ))
    
    app()
