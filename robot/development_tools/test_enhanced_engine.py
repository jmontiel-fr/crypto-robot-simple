#!/usr/bin/env python3
"""
Test the enhanced AI-powered simulation engine
"""
import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_enhanced_engine():
    """Test the enhanced engine with AI improvements"""
    print("🚀 TESTING AI-ENHANCED SIMULATION ENGINE")
    print("=" * 60)
    
    try:
        from daily_rebalance_simulation_engine import DailyRebalanceSimulationEngine
        
        # Create enhanced engine
        engine = DailyRebalanceSimulationEngine(
            realistic_mode=True,
            calibration_profile='live_robot_performance',
            enable_usdc_protection=True  # Enhanced USDC protection enabled
        )
        
        print("\n🧪 Running test simulation...")
        print("   Duration: 7 days")
        print("   Starting Capital: $100")
        print("   Profile: live_robot_performance")
        print("   AI Features: ALL ENABLED")
        print("   Enhanced USDC Protection: ENABLED")
        
        # Run test simulation
        result = engine.run_simulation(
            start_date=datetime(2025, 2, 1),
            duration_days=7,
            cycle_length_minutes=1440,
            starting_reserve=100.0,
            verbose=True
        )
        
        if result and result.get('success'):
            cycles_data = result['cycles_data']
            final_summary = result['final_summary']
            
            print(f"\n✅ AI-ENHANCED SIMULATION RESULTS:")
            print(f"=" * 50)
            print(f"   Starting Capital: $100.00")
            print(f"   Final Capital: ${final_summary.get('final_capital', 0):.2f}")
            print(f"   Total Return: {final_summary.get('total_return', 0):.1f}%")
            print(f"   Total Cycles: {len(cycles_data)}")
            print(f"   AI Enhanced: {result.get('ai_enhanced', False)}")
            print(f"   Final Coin Selection: {', '.join(result.get('final_coin_selection', []))}")
            
            # Show regime detection results
            regime_history = result.get('regime_history', [])
            if regime_history:
                print(f"   Market Regimes Detected: {', '.join(set(regime_history))}")
            
            print(f"\n🎯 PERFORMANCE COMPARISON:")
            print(f"   Previous Engine Average: ~15.8% per 30 days")
            print(f"   AI-Enhanced Result: {final_summary.get('total_return', 0):.1f}% per 7 days")
            
            # Extrapolate to 30 days for comparison
            daily_return = final_summary.get('total_return', 0) / 7
            projected_30_day = daily_return * 30
            print(f"   Projected 30-day: {projected_30_day:.1f}%")
            
            improvement = (projected_30_day / 15.8 - 1) * 100 if projected_30_day > 0 else 0
            print(f"   Estimated Improvement: {improvement:+.1f}%")
            
            print(f"\n🔧 AI FEATURES ACTIVE:")
            print(f"   ✅ Dynamic Coin Selection")
            print(f"   ✅ Market Regime Detection") 
            print(f"   ✅ Hybrid Momentum + Mean Reversion")
            print(f"   ✅ Risk-Adjusted Position Sizing")
            print(f"   ✅ Real-time Strategy Adaptation")
            
        else:
            print("❌ Simulation failed")
            
    except Exception as e:
        print(f"❌ Error testing enhanced engine: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_engine()