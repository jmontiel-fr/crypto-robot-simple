#!/usr/bin/env python3
"""
Test USDC protection functionality
"""
import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_usdc_protection():
    """Test with USDC protection enabled"""
    print("🛡️ TESTING USDC PROTECTION FUNCTIONALITY")
    print("=" * 60)
    
    try:
        from daily_rebalance_simulation_engine import DailyRebalanceSimulationEngine
        
        # Test with USDC protection ENABLED
        engine = DailyRebalanceSimulationEngine(
            realistic_mode=True,
            calibration_profile='live_robot_performance',
            enable_usdc_protection=True  # ENABLE USDC PROTECTION
        )
        
        print("\n🧪 Running test with USDC protection ENABLED...")
        print("   Duration: 14 days (longer test for volatility)")
        print("   Starting Capital: $100")
        print("   Profile: live_robot_performance")
        print("   USDC Protection: ENABLED")
        print("   Triggers: -15% decline OR 3 consecutive losses")
        
        # Run longer simulation to potentially trigger protection
        result = engine.run_simulation(
            start_date=datetime(2025, 1, 15),  # Different date range
            duration_days=14,
            cycle_length_minutes=1440,
            starting_reserve=100.0,
            verbose=True
        )
        
        if result and result.get('success'):
            cycles_data = result['cycles_data']
            final_summary = result['final_summary']
            
            # Check for USDC protection cycles
            usdc_cycles = 0
            protection_triggered = False
            
            for cycle in cycles_data:
                if cycle.get('usdc_protection', False):
                    usdc_cycles += 1
                    protection_triggered = True
                    print(f"🛡️ USDC Protection was active in cycle {cycle.get('cycle_number', '?')}")
            
            print(f"\n✅ USDC PROTECTION TEST RESULTS:")
            print(f"=" * 50)
            print(f"   Starting Capital: $100.00")
            print(f"   Final Capital: ${final_summary.get('final_capital', 0):.2f}")
            print(f"   Total Return: {final_summary.get('total_return', 0):.1f}%")
            print(f"   Total Cycles: {len(cycles_data)}")
            print(f"   USDC Protection Cycles: {usdc_cycles}")
            
            if protection_triggered:
                print(f"   Status: ✅ USDC Protection was ACTIVATED")
            else:
                print(f"   Status: ⚠️  USDC Protection was NOT triggered")
                print(f"   Reason: No -15% decline or 3 consecutive losses detected")
            
            # Show consecutive losses tracking
            consecutive_losses = 0
            max_consecutive = 0
            min_daily_return = 100.0
            
            for cycle in cycles_data:
                cycle_return = cycle.get('cycle_return', 0)
                if cycle_return < 0:
                    consecutive_losses += 1
                    max_consecutive = max(max_consecutive, consecutive_losses)
                else:
                    consecutive_losses = 0
                min_daily_return = min(min_daily_return, cycle_return)
            
            print(f"\n📊 PROTECTION TRIGGER ANALYSIS:")
            print(f"   Max Consecutive Losses: {max_consecutive} (threshold: 3)")
            print(f"   Worst Daily Return: {min_daily_return:.1f}% (threshold: -15%)")
            
            if max_consecutive >= 3:
                print(f"   ⚠️  Consecutive loss threshold WAS reached")
            if min_daily_return <= -15:
                print(f"   ⚠️  Daily decline threshold WAS reached")
                
        else:
            print("❌ Simulation failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_usdc_protection()