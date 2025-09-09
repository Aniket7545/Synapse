"""
Real-time Merchant API Integration Demo
Demonstrates live order tracking, kitchen management, and merchant communication
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.services.merchant_api import merchant_api, OrderStatus, KitchenStatus
from src.tools.merchant_api_tools import (
    GetMerchantStatusTool, CheckOrderStatusTool, CreateMerchantOrderTool,
    EstimatePreparationTimeTool, MonitorKitchenPerformanceTool, GetMerchantMenuTool
)
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, TaskID
import random

console = Console()


async def demo_merchant_api_integration():
    """Comprehensive merchant API integration demonstration"""
    
    console.print(Panel.fit(
        "🏪 Real-time Merchant API Integration Demo\n" +
        "Live order tracking, kitchen management & restaurant communication",
        style="bold magenta"
    ))
    
    # Demo 1: Merchant Status Overview
    console.print("\n🏪 **Demo 1: Merchant Fleet Status**")
    
    status_table = Table(title="📊 Live Merchant Status", show_header=True, header_style="bold cyan")
    status_table.add_column("Merchant", style="green", width=20)
    status_table.add_column("Type", style="blue", width=12)
    status_table.add_column("Kitchen Status", style="yellow", width=12)
    status_table.add_column("Load", style="red", width=8)
    status_table.add_column("Utilization", style="magenta", width=12)
    status_table.add_column("Avg Wait", style="cyan", width=10)
    
    status_tool = GetMerchantStatusTool()
    
    # Check status of all demo merchants
    merchant_ids = ["MER_001", "MER_002", "MER_003", "MER_004", "MER_005"]
    merchant_statuses = []
    
    for merchant_id in merchant_ids:
        status = await status_tool._run(merchant_id)
        merchant_statuses.append(status)
        
        # Add some random activity for demo
        utilization = random.randint(30, 95)
        avg_wait = random.randint(10, 35)
        
        kitchen_emoji = {
            "normal": "🟢",
            "busy": "🟡", 
            "overwhelmed": "🔴",
            "offline": "⚫"
        }
        
        status_table.add_row(
            status["name"],
            status["type"].title(),
            f"{kitchen_emoji.get(status['kitchen_status'], '🟢')} {status['kitchen_status'].title()}",
            f"{status['current_load']}/{status['capacity']}",
            f"{utilization}%",
            f"{avg_wait}m"
        )
    
    console.print(status_table)
    
    # Demo 2: Menu and Availability Check
    console.print("\n🍽️ **Demo 2: Live Menu & Availability**")
    
    menu_tool = GetMerchantMenuTool()
    sample_merchant = merchant_statuses[0]
    
    menu_result = await menu_tool._run(sample_merchant["merchant_id"])
    
    console.print(f"📋 Menu for: {menu_result['merchant_name']}")
    console.print(f"📊 Total Items: {menu_result['total_items']} | Available: {menu_result['available_items']}")
    
    menu_table = Table(show_header=True, header_style="bold green")
    menu_table.add_column("Item", style="cyan", width=20)
    menu_table.add_column("Category", style="blue", width=12)
    menu_table.add_column("Prep Time", style="yellow", width=10)
    menu_table.add_column("Price", style="red", width=8) 
    menu_table.add_column("Available", style="green", width=10)
    
    for item in menu_result['menu_items'][:5]:  # Show first 5 items
        availability = "✅ Yes" if item['available'] else "❌ No"
        menu_table.add_row(
            item['name'],
            item['category'],
            f"{item['preparation_time_minutes']}m",
            f"₹{item['price']}",
            availability
        )
    
    console.print(menu_table)
    
    # Demo 3: Create Live Order
    console.print("\n📦 **Demo 3: Live Order Creation & Tracking**")
    
    create_tool = CreateMerchantOrderTool()
    
    # Create sample order
    sample_items = [
        {"item_id": f"{sample_merchant['merchant_id']}_ITEM_001", "quantity": 2},
        {"item_id": f"{sample_merchant['merchant_id']}_ITEM_002", "quantity": 1, "customizations": ["Extra spicy"]}
    ]
    
    order_result = await create_tool._run(
        merchant_id=sample_merchant["merchant_id"],
        customer_id="CUST_DEMO_001",
        items=sample_items,
        special_notes="Please pack carefully"
    )
    
    if "error" not in order_result:
        console.print(f"✅ Order Created: {order_result['order_id']}")
        console.print(f"🏪 Merchant: {order_result['merchant_name']}")
        console.print(f"💰 Total: ₹{order_result['total_amount']}")
        console.print(f"⏰ Estimated Prep: {order_result['estimated_prep_time']} minutes")
        console.print(f"🕐 Ready By: {order_result['expected_ready_time'][:16]}")
        
        order_id = order_result['order_id']
        
        # Demo 4: Real-time Order Status Tracking
        console.print("\n📡 **Demo 4: Real-time Order Status Updates**")
        
        check_tool = CheckOrderStatusTool()
        
        # Simulate order progression
        status_progression = [
            ("confirmed", "Order confirmed by restaurant"),
            ("preparing", "Chef started preparation"), 
            ("ready", "Order ready for pickup")
        ]
        
        for new_status, description in status_progression:
            console.print(f"   🔄 {description}...")
            
            # Update order status (simulate merchant POS update)
            from src.tools.merchant_api_tools import UpdateOrderStatusTool
            update_tool = UpdateOrderStatusTool()
            
            update_result = await update_tool._run(
                order_id=order_id,
                new_status=new_status,
                notes=description
            )
            
            # Check updated status
            status_result = await check_tool._run(order_id)
            
            console.print(f"      📍 Status: {status_result['status'].upper()}")
            console.print(f"      ⏱️  Time Elapsed: {status_result['time_elapsed_minutes']}m")
            console.print(f"      🕐 Time Remaining: {status_result['time_remaining_minutes']}m")
            
            await asyncio.sleep(1)  # Simulate time passing
    
    # Demo 5: Kitchen Performance Analysis
    console.print("\n📊 **Demo 5: Kitchen Performance Monitoring**")
    
    performance_tool = MonitorKitchenPerformanceTool()
    
    perf_table = Table(title="🔥 Kitchen Performance Analysis", show_header=True, header_style="bold red")
    perf_table.add_column("Merchant", style="cyan", width=20)
    perf_table.add_column("Performance", style="green", width=12)
    perf_table.add_column("Utilization", style="yellow", width=12)
    perf_table.add_column("Avg Wait", style="red", width=10)
    perf_table.add_column("Recommendation", style="blue", width=30)
    
    for merchant_status in merchant_statuses[:3]:  # Analyze top 3 merchants
        perf_result = await performance_tool._run(merchant_status["merchant_id"])
        
        performance_emoji = {
            "optimal": "🟢",
            "busy": "🟡",
            "stressed": "🟠", 
            "critical": "🔴"
        }
        
        perf_table.add_row(
            perf_result["merchant_name"],
            f"{performance_emoji.get(perf_result['performance_level'], '🟢')} {perf_result['performance_level'].title()}",
            f"{perf_result['utilization_percent']}%",
            f"{perf_result['current_avg_wait_minutes']}m",
            perf_result["recommendation"][:30] + "..."
        )
    
    console.print(perf_table)
    
    # Demo 6: Preparation Time Estimation
    console.print("\n⏰ **Demo 6: Dynamic Preparation Time Estimation**")
    
    estimate_tool = EstimatePreparationTimeTool()
    
    test_orders = [
        {"name": "Burger Combo", "quantity": 2},
        {"name": "Biryani", "quantity": 1},
        {"name": "Pizza Margherita", "quantity": 1}
    ]
    
    estimate_table = Table(show_header=True, header_style="bold yellow")
    estimate_table.add_column("Items", style="cyan", width=25)
    estimate_table.add_column("Base Time", style="green", width=10)
    estimate_table.add_column("Kitchen Load", style="red", width=12)
    estimate_table.add_column("Final ETA", style="blue", width=10)
    estimate_table.add_column("Ready By", style="magenta", width=12)
    
    for merchant_status in merchant_statuses[:2]:  # Test with 2 merchants
        estimate_result = await estimate_tool._run(
            merchant_id=merchant_status["merchant_id"],
            items=test_orders
        )
        
        estimate_table.add_row(
            f"{len(test_orders)} items",
            f"{estimate_result['base_preparation_time']}m",
            f"{estimate_result['kitchen_multiplier']:.1f}x",
            f"{estimate_result['estimated_preparation_time']}m",
            estimate_result['ready_by'][11:16]  # Extract time only
        )
    
    console.print(estimate_table)
    
    # Demo 7: Simulate Kitchen Activity
    console.print("\n🔥 **Demo 7: Live Kitchen Activity Simulation**")
    
    console.print("🧑‍🍳 Simulating 15 minutes of kitchen activity...")
    
    with Progress() as progress:
        task = progress.add_task("[cyan]Kitchen simulation...", total=15)
        
        updates = await merchant_api.simulate_kitchen_activity(
            merchant_id=sample_merchant["merchant_id"],
            duration_minutes=15
        )
        
        progress.update(task, completed=15)
    
    console.print(f"📊 Generated {len(updates)} kitchen updates")
    
    # Show sample updates
    if updates:
        console.print("📋 Sample Updates:")
        for update in updates[:3]:
            if 'order_id' in update:
                console.print(f"   🔄 Order {update['order_id'][-6:]}: {update['old_status']} → {update['new_status']}")
            else:
                console.print(f"   🏪 Kitchen status: {update.get('new_status', 'Updated')}")
    
    # Final Summary
    console.print(Panel.fit(
        "🎉 Merchant API Integration Demo Completed!\n\n" +
        "✅ Features Demonstrated:\n" +
        "• Real-time merchant status monitoring\n" +
        "• Live menu & availability tracking\n" +
        "• Order creation & status updates\n" +
        "• Kitchen performance analytics\n" +
        "• Dynamic preparation time estimation\n" +
        "• Live kitchen activity simulation\n" +
        "• Restaurant communication APIs\n\n" +
        "🚀 Production-ready merchant integration system!",
        style="bold green"
    ))


if __name__ == "__main__":
    asyncio.run(demo_merchant_api_integration())
