#!/usr/bin/env python3
"""
Run Pending Simulations - Unicode Fixed Version
Executes all pending simulations in the database with proper Unicode handling
"""

import os
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def run_pending_simulations(max_simulations=None, list_only=False):
    """Run all pending simulations with Unicode support"""
    
    print("SIMULATION RUNNER - Unicode Fixed Version")
    print("=" * 55)
    
    try:
        from database import DatabaseManager, Simulation
        from daily_rebalance_simulation_engine import DailyRebalanceSimulationEngine
        
        # Initialize database
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        
        # Get pending simulations
        pending_query = session.query(Simulation).filter(Simulation.status == 'pending')
        
        if max_simulations:
            pending_query = pending_query.limit(max_simulations)
            
        pending_simulations = pending_query.all()
        
        if not pending_simulations:
            print("ℹ️  No pending simulations found")
            return True
        
        print(f"Found {len(pending_simulations)} pending simulation(s)")
        
        if list_only:
            print("\nPENDING SIMULATIONS:")
            print("-" * 60)
            for i, sim in enumerate(pending_simulations, 1):
                print(f"{i:2d}. {sim.name}")
                print(f"    Start: {sim.start_date} | Duration: {sim.duration_days} days")
                print(f"    Capital: ${sim.starting_reserve} | Profile: {sim.calibration_profile}")
                print(f"    Strategy: {sim.strategy} | Created: {sim.created_at}")
                print()
            return True
        
        # Execute simulations
        print(f"\nEXECUTING SIMULATIONS:")
        print("-" * 40)
        
        successful = 0
        failed = 0
        
        for i, simulation in enumerate(pending_simulations, 1):
            print(f"\n[{i}/{len(pending_simulations)}] Running: {simulation.name}")
            print(f"   Start Date: {simulation.start_date}")
            print(f"   Duration: {simulation.duration_days} days")
            print(f"   Capital: ${simulation.starting_reserve}")
            print(f"   Profile: {simulation.calibration_profile}")
            
            try:
                # Update status to running
                simulation.status = 'running'
                simulation.started_at = datetime.now(timezone.utc)
                session.commit()
                
                # Create simulation engine
                engine = DailyRebalanceSimulationEngine(
                    realistic_mode=simulation.realistic_mode,
                    calibration_profile=simulation.calibration_profile
                )
                
                # Run the simulation
                print(f"   Executing simulation...")
                result = engine.run_simulation(
                    start_date=simulation.start_date,
                    duration_days=simulation.duration_days,
                    cycle_length_minutes=simulation.cycle_length_minutes,
                    starting_reserve=simulation.starting_reserve,
                    verbose=True
                )
                
                if result and 'cycles_data' in result:
                    # Process and save simulation cycles
                    from database import SimulationCycle
                    
                    cycles_data = result['cycles_data']
                    print(f"   Processing {len(cycles_data)} cycles...")
                    
                    # Save cycles to database
                    for cycle_data in cycles_data:
                        # Convert cycle_date string to datetime object
                        from datetime import datetime as dt
                        cycle_date_str = cycle_data.get('date')
                        if isinstance(cycle_date_str, str):
                            try:
                                cycle_date = dt.fromisoformat(cycle_date_str.replace('Z', '+00:00'))
                            except:
                                # Fallback parsing
                                cycle_date = dt.strptime(cycle_date_str[:19], '%Y-%m-%dT%H:%M:%S')
                        else:
                            cycle_date = cycle_date_str
                        
                        cycle = SimulationCycle(
                            simulation_id=simulation.id,
                            cycle_number=cycle_data.get('cycle', cycle_data.get('cycle_number', 0)),
                            cycle_date=cycle_date,
                            total_value=cycle_data.get('total_value', 0),
                            portfolio_value=cycle_data.get('portfolio_value', 0),
                            bnb_reserve=cycle_data.get('bnb_reserve', 0),
                            portfolio_breakdown=cycle_data.get('portfolio_breakdown', {}),
                            actions_taken=cycle_data.get('actions_taken', {}),
                            trading_costs=cycle_data.get('trading_costs', 0),
                            execution_delay=cycle_data.get('execution_delay', 0),
                            failed_orders=cycle_data.get('failed_orders', 0),
                            market_conditions=cycle_data.get('market_conditions', '')
                        )
                        session.add(cycle)
                    
                    # Update simulation status and final values
                    simulation.status = 'completed'
                    simulation.completed_at = datetime.now(timezone.utc)
                    
                    # Get final cycle data
                    if cycles_data:
                        final_cycle = cycles_data[-1]
                        simulation.final_total_value = final_cycle.get('total_value', simulation.starting_reserve)
                        simulation.final_portfolio_value = final_cycle.get('portfolio_value', 0)
                        simulation.final_reserve_value = final_cycle.get('bnb_reserve', 0)
                        simulation.realized_pnl = simulation.final_total_value - simulation.starting_reserve
                    
                    session.commit()
                    
                    print(f"   Completed successfully!")
                    print(f"      Final Value: ${simulation.final_total_value:.2f}")
                    return_pct = (simulation.realized_pnl / simulation.starting_reserve) * 100
                    print(f"      Return: {return_pct:.1f}%")
                    print(f"      Cycles: {len(cycles_data)}")
                    
                    successful += 1
                    
                else:
                    # Mark as failed
                    simulation.status = 'failed'
                    simulation.completed_at = datetime.now(timezone.utc)
                    error_msg = result.get('error', 'Unknown error') if result else 'No result returned'
                    simulation.error_message = error_msg
                    session.commit()
                    
                    print(f"   Simulation failed: {error_msg}")
                    failed += 1
                    
            except Exception as e:
                # Handle Unicode and other errors gracefully
                error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8')
                print(f"   Error: {error_msg}")
                
                # Mark as failed
                simulation.status = 'failed'
                simulation.completed_at = datetime.now(timezone.utc)
                simulation.error_message = error_msg
                session.commit()
                
                failed += 1
        
        # Final summary
        print(f"\nEXECUTION SUMMARY:")
        print("=" * 30)
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Total: {len(pending_simulations)}")
        
        if successful > 0:
            print(f"\n{successful} simulation(s) completed successfully!")
            print(f"   View results at: http://localhost:5000/simulator-list")
        
        return successful > 0
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure you're running from the project root directory")
        return False
    except Exception as e:
        error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8')
        print(f"Execution error: {error_msg}")
        return False
    finally:
        if 'session' in locals():
            session.close()

def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(description='Run pending simulations with Unicode support')
    parser.add_argument('--max', type=int, help='Maximum number of simulations to run')
    parser.add_argument('--list', action='store_true', help='List pending simulations without running them')
    
    args = parser.parse_args()
    
    success = run_pending_simulations(
        max_simulations=args.max,
        list_only=args.list
    )
    
    if not success and not args.list:
        sys.exit(1)

if __name__ == '__main__':
    main()