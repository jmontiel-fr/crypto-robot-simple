#!/usr/bin/env python3
"""
Test the calculation fixes for total_value and performance
"""
import sys
sys.path.append('src')
from daily_rebalance_simulation_engine import DailyRebalanceSimulationEngine
from datetime import datetime

def test_calculation_fix():
    print('🧪 Testing Calculation Fixes')
    print('=' * 50)
    
    # Create engine
    engine = DailyRebalanceSimulationEngine(
        realistic_mode=True,
        calibration_profile='realistic_baseline',
        enable_usdc_protection=True
    )
    
    # Run a short 3-day simulation
    start_date = datetime.strptime('2025-01-01', '%Y-%m-%d')
    
    result = engine.run_simulation(
        start_date=start_date,
        duration_days=3,
        cycle_length_minutes=1440,
        starting_reserve=100.0
    )
    
    print('\n✅ Testing Results:')
    print('=' * 50)
    
    # Debug: Print result structure
    print("Result keys:", list(result.keys()))
    
    # Check all cycles
    cycles = result.get('cycles', [])
    cycle_data = result.get('cycle_data', [])
    
    print(f"Cycles: {len(cycles)}")
    print(f"Cycle data: {len(cycle_data)}")
    
    # Use whichever has data
    data_to_check = cycles if cycles else cycle_data
    
    if data_to_check:
        for i, cycle in enumerate(data_to_check[-3:]):  # Check last 3 cycles
            portfolio_value = cycle.get('portfolio_value', 0)
            bnb_reserve = cycle.get('bnb_reserve', 0)
            total_value = cycle.get('total_value', 0)
            calculated_total = portfolio_value + bnb_reserve
            ending_capital = cycle.get('ending_capital', 0)
            
            print(f"\nCycle {i+1}:")
            print(f"  Portfolio Value: ${portfolio_value:.6f}")
            print(f"  BNB Reserve:     ${bnb_reserve:.6f}")
            print(f"  Total Value:     ${total_value:.6f}")
            print(f"  Calculated:      ${calculated_total:.6f}")
            print(f"  Ending Capital:  ${ending_capital:.6f}")
            print(f"  Total=Portfolio+Reserve: {'✅' if abs(total_value - calculated_total) < 0.000001 else '❌'}")
            print(f"  Total=EndingCapital: {'✅' if abs(total_value - ending_capital) < 0.000001 else '❌'}")
    else:
        print("No cycle data found in result")
    
    # Check final summary
    final_summary = result.get('final_summary', {})
    final_capital = final_summary.get('final_capital', 0)
    
    print(f"\nFinal Summary:")
    print(f"  Final Capital: ${final_capital:.6f}")
    
    return result

if __name__ == "__main__":
    test_calculation_fix()