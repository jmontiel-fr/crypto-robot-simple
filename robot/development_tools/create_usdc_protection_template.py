#!/usr/bin/env python3
"""
Create USDC Protection Simulation Template

Creates simulation templates specifically designed to test USDC protection
during different market conditions.
"""

import csv
from datetime import datetime, timedelta

def create_usdc_protection_templates():
    """Create simulation templates for USDC protection testing"""
    
    print("🛡️ CREATING USDC PROTECTION SIMULATION TEMPLATES")
    print("=" * 60)
    
    # Template 1: USDC Protection Enabled
    usdc_enabled_template = [
        {
            'simulation_name': 'USDC Protection Demo - Enabled',
            'start_date': '2025-02-01',
            'duration_days': 7,
            'cycle_duration_minutes': 1440,
            'starting_capital': 100,
            'strategy': 'daily_rebalance_with_usdc_protection',
            'calibration_profile': 'none',  # No calibration to see raw results
            'data_source': 'binance_historical'
        },
        {
            'simulation_name': 'USDC Protection Demo - Disabled',
            'start_date': '2025-02-01',
            'duration_days': 7,
            'cycle_duration_minutes': 1440,
            'starting_capital': 100,
            'strategy': 'daily_rebalance',
            'calibration_profile': 'none',  # No calibration to see raw results
            'data_source': 'binance_historical'
        },
        {
            'simulation_name': 'USDC Protection Bear Market Test',
            'start_date': '2024-12-01',  # Try a different period
            'duration_days': 14,
            'cycle_duration_minutes': 1440,
            'starting_capital': 100,
            'strategy': 'daily_rebalance_with_usdc_protection',
            'calibration_profile': 'none',
            'data_source': 'binance_historical'
        },
        {
            'simulation_name': 'USDC Protection Stress Test',
            'start_date': '2024-11-01',  # Another period to test
            'duration_days': 21,
            'cycle_duration_minutes': 1440,
            'starting_capital': 100,
            'strategy': 'daily_rebalance_with_usdc_protection',
            'calibration_profile': 'none',
            'data_source': 'binance_historical'
        }
    ]
    
    # Write USDC protection template
    fieldnames = ['simulation_name', 'start_date', 'duration_days', 'cycle_duration_minutes', 
                 'starting_capital', 'strategy', 'calibration_profile', 'data_source']
    
    filename = 'simulations_template_usdc_protection.csv'
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(usdc_enabled_template)
        
        print(f"✅ Created USDC protection template: {filename}")
        print(f"📊 Contains {len(usdc_enabled_template)} USDC protection test simulations")
        
        # Show template contents
        print(f"\n📋 TEMPLATE CONTENTS:")
        print("-" * 80)
        print(f"{'Name':<35} {'Date':<12} {'Days':<5} {'Strategy':<25}")
        print("-" * 80)
        
        for sim in usdc_enabled_template:
            strategy_display = sim['strategy'].replace('daily_rebalance_with_usdc_protection', 'WITH USDC Protection')
            strategy_display = strategy_display.replace('daily_rebalance', 'NO Protection')
            
            print(f"{sim['simulation_name'][:34]:<35} {sim['start_date']:<12} "
                  f"{sim['duration_days']:<5} {strategy_display:<25}")
        
        print("-" * 80)
        
        return filename
        
    except Exception as e:
        print(f"❌ Error creating template: {e}")
        return None

def create_enhanced_generator_with_usdc():
    """Create an enhanced generator that supports USDC protection flag"""
    
    enhanced_generator_code = '''#!/usr/bin/env python3
"""
Enhanced Simulation Generator with USDC Protection Support

Generates simulations with optional USDC protection enabled.
"""

import os
import sys
import csv
import argparse
from datetime import datetime
from typing import List, Dict, Optional

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import get_db_manager, Simulation, SimulationCycle
from daily_rebalance_simulation_engine import DailyRebalanceSimulationEngine

def run_usdc_protection_simulation(sim_data: Dict, enable_usdc: bool = False) -> Dict:
    """Run a single simulation with optional USDC protection"""
    
    print(f"🚀 RUNNING: {sim_data['simulation_name']}")
    print(f"   USDC Protection: {'ENABLED' if enable_usdc else 'DISABLED'}")
    print(f"   Period: {sim_data['start_date']} ({sim_data['duration_days']} days)")
    
    # Create engine with USDC protection setting
    engine = DailyRebalanceSimulationEngine(
        realistic_mode=True, 
        enable_usdc_protection=enable_usdc
    )
    
    # Run simulation
    result = engine.run_simulation(
        start_date=datetime.strptime(sim_data['start_date'], '%Y-%m-%d'),
        duration_days=sim_data['duration_days'],
        cycle_length_minutes=sim_data['cycle_duration_minutes'],
        starting_reserve=sim_data['starting_capital'],
        verbose=False
    )
    
    if result['success']:
        cycles_data = result['cycles_data']
        final_summary = result['final_summary']
        
        # Count USDC protection days
        protection_days = sum(1 for cycle in cycles_data if cycle.get('usdc_protection', False))
        final_performance = ((final_summary['final_capital'] - sim_data['starting_capital']) / sim_data['starting_capital']) * 100
        
        print(f"   ✅ COMPLETED: {final_performance:.1f}% return")
        print(f"   🛡️ Protection Days: {protection_days}/{len(cycles_data)}")
        
        return {
            'success': True,
            'final_performance': final_performance,
            'protection_days': protection_days,
            'total_days': len(cycles_data),
            'final_capital': final_summary['final_capital']
        }
    else:
        print(f"   ❌ FAILED: {result.get('error', 'Unknown error')}")
        return {'success': False, 'error': result.get('error', 'Unknown error')}

def main():
    parser = argparse.ArgumentParser(description='Run USDC protection simulations')
    parser.add_argument('--csv', default='simulations_template_usdc_protection.csv', 
                       help='CSV template file')
    parser.add_argument('--enable-usdc', action='store_true',
                       help='Enable USDC protection in simulations')
    
    args = parser.parse_args()
    
    print("🛡️ USDC PROTECTION SIMULATION RUNNER")
    print("=" * 50)
    print(f"Template: {args.csv}")
    print(f"USDC Protection: {'ENABLED' if args.enable_usdc else 'DISABLED'}")
    print()
    
    # Load simulations from CSV
    simulations = []
    
    try:
        with open(args.csv, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                simulations.append({
                    'simulation_name': row['simulation_name'],
                    'start_date': row['start_date'],
                    'duration_days': int(row['duration_days']),
                    'cycle_duration_minutes': int(row['cycle_duration_minutes']),
                    'starting_capital': float(row['starting_capital']),
                    'strategy': row['strategy'],
                    'calibration_profile': row['calibration_profile'],
                    'data_source': row['data_source']
                })
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return
    
    # Run simulations
    results = []
    
    for sim_data in simulations:
        # Determine if USDC should be enabled based on strategy or command line
        enable_usdc = args.enable_usdc or 'usdc_protection' in sim_data['strategy']
        
        result = run_usdc_protection_simulation(sim_data, enable_usdc)
        results.append(result)
        print()
    
    # Summary
    successful = [r for r in results if r['success']]
    
    print("📊 EXECUTION SUMMARY:")
    print(f"   Total Simulations: {len(results)}")
    print(f"   ✅ Successful: {len(successful)}")
    print(f"   ❌ Failed: {len(results) - len(successful)}")
    
    if successful:
        avg_performance = sum(r['final_performance'] for r in successful) / len(successful)
        total_protection_days = sum(r['protection_days'] for r in successful)
        total_days = sum(r['total_days'] for r in successful)
        
        print(f"   📈 Average Performance: {avg_performance:.1f}%")
        print(f"   🛡️ Total Protection Days: {total_protection_days}/{total_days}")

if __name__ == '__main__':
    main()
'''
    
    filename = 'run_usdc_protection_simulations.py'
    
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(enhanced_generator_code)
        
        print(f"✅ Created enhanced generator: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Error creating generator: {e}")
        return None

if __name__ == "__main__":
    # Create USDC protection template
    template_file = create_usdc_protection_templates()
    
    print()
def main():
    # Create USDC protection template
    template_file = create_usdc_protection_templates()
    
    # Create enhanced generator
    generator_file = create_enhanced_generator_with_usdc()
    
    if template_file and generator_file:
        print(f"\n🎯 READY TO TEST USDC PROTECTION:")
        print(f"   1. Run without protection: python {generator_file}")
        print(f"   2. Run with protection: python {generator_file} --enable-usdc")
        print(f"   3. Compare results to see protection in action!")

if __name__ == "__main__":
    main()