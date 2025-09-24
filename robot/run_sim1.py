#!/usr/bin/env python3
"""
Run sim1 with enhanced USDC protection
"""
import sys
sys.path.append('src')
from daily_rebalance_simulation_engine import DailyRebalanceSimulationEngine
import pandas as pd

def run_sim2():
    # Load simulation template
    df = pd.read_csv('simulations_templates/simulations_template_custom.csv')
    sim2 = df[df['simulation_name'] == 'sim2'].iloc[0]

    print('🚀 Running sim2 with Enhanced USDC Protection')
    print(f'   Profile: {sim2["calibration_profile"]}')
    print(f'   Start: {sim2["start_date"]}')
    print(f'   Duration: {sim2["duration_days"]} days')
    print('   Enhanced USDC Protection: ENABLED')
    print('=' * 50)

    # Create and run simulation
    engine = DailyRebalanceSimulationEngine(
        realistic_mode=True,
        calibration_profile=sim2['calibration_profile'],
        enable_usdc_protection=True
    )

    from datetime import datetime
    start_date = datetime.strptime(sim2['start_date'], '%Y-%m-%d')
    
    result = engine.run_simulation(
        start_date=start_date,
        duration_days=int(sim2['duration_days']),
        cycle_length_minutes=int(sim2['cycle_duration_minutes']),
        starting_reserve=float(sim2['starting_capital'])
    )

    print('✅ Simulation completed!')
    print(f'Final result: {result}')
    return result

if __name__ == "__main__":
    run_sim2()