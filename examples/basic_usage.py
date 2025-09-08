#!/usr/bin/env python3
"""
Basic Usage Example for Project Synapse
Demonstrates simple scenario execution
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.chain_of_thought import chain_of_thought
from src.cli.commands import CommandHandler

async def basic_usage_example():
    """Run a basic Project Synapse example"""
    
    print("🚛 Project Synapse - Basic Usage Example")
    print("=" * 50)
    
    # Run a traffic jam scenario
    result = await CommandHandler.handle_scenario_run(
        scenario_type="traffic_jam",
        city="mumbai", 
        severity=7
    )
    
    print("\n📊 Scenario Results:")
    print(f"Status: {result['status']}")
    print(f"Confidence: {result['confidence_score']}")
    print(f"Agents Involved: {', '.join(result['agents_involved'])}")
    
    # Show chain of thought summary
    if chain_of_thought.thoughts:
        summary = chain_of_thought.get_chain_summary()
        print(f"\n🧠 Chain of Thought Summary:")
        print(f"Total Steps: {summary['total_steps']}")
        print(f"Average Confidence: {summary['average_confidence']:.2f}")
        print(f"Tools Used: {', '.join(summary['tools_used'])}")

if __name__ == "__main__":
    asyncio.run(basic_usage_example())
