#!/usr/bin/env python3
"""
Test the engine with truly realistic calibration
"""
import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_truly_realistic():
    """Test with brutally honest calibration"""
    print("🔍 TESTING WITH TRULY REALISTIC CALIBRATION")
    print("=" * 60)
    
    try:
        from daily_rebalance_simulation_engine import DailyRebalanceSimulationEngine
        
        # Test with truly realistic baseline
        engine = DailyRebalanceSimulationEngine(
            realistic_mode=True,
            calibration_profile='truly_realistic_baseline'
        )
        
        print("\n🧪 Running test with HONEST calibration...")
        print("   Duration: 7 days")
        print("   Starting Capital: $100")
        print("   Profile: truly_realistic_baseline")
        print("   Expected: 2-8% monthly (HONEST)")
        
        # Run test simulation
        result = engine.run_simulation(
            start_date=datetime(2025, 2, 1),
            duration_days=7,
            cycle_length_minutes=1440,
            starting_reserve=100.0,
            verbose=True
        )
        
        if result and result.get('success'):
            final_summary = result['final_summary']
            
            print(f"\n✅ TRULY REALISTIC RESULTS:")
            print(f"=" * 50)
            print(f"   Starting Capital: $100.00")
            print(f"   Final Capital: ${final_summary.get('final_capital', 0):.2f}")
            print(f"   Total Return: {final_summary.get('total_return', 0):.1f}%")
            
            # Extrapolate to 30 days
            daily_return = final_summary.get('total_return', 0) / 7
            projected_30_day = daily_return * 30
            print(f"   Projected 30-day: {projected_30_day:.1f}%")
            
            print(f"\n🎯 HONEST COMPARISON:")
            print(f"   Realistic Expectation: 2-8% per 30 days")
            print(f"   AI-Enhanced Result: {projected_30_day:.1f}% per 30 days")
            
            if projected_30_day > 8:
                print(f"   Status: ⚠️  Still above realistic range!")
            elif projected_30_day >= 2:
                print(f"   Status: ✅ Within realistic expectations")
            else:
                print(f"   Status: ❌ Below realistic minimum")
                
        else:
            print("❌ Simulation failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_truly_realistic()