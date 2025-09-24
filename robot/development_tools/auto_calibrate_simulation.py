#!/usr/bin/env python3
"""
Auto-Calibrate Simulation Constraints

Automatically adjusts simulation reality constraints based on real robot performance.
This creates a feedback loop to keep simulations realistic as market conditions change.
"""

from src.database import DatabaseManager, Simulation, SimulationCycle, TradingCycle
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import statistics

load_dotenv()

class SimulationAutoCalibrator:
    """Automatically calibrates simulation constraints using real robot data"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.calibration_history = []
        
    def auto_calibrate(self, simulation_id: int = 1, min_real_cycles: int = 7):
        """
        Automatically calibrate simulation constraints based on real robot performance
        
        Args:
            simulation_id: Simulation to calibrate
            min_real_cycles: Minimum real cycles needed for calibration
        """
        
        print("🤖 AUTO-CALIBRATING SIMULATION CONSTRAINTS")
        print("=" * 55)
        
        session = self.db_manager.get_session()
        
        try:
            # Get recent real robot data
            real_data = self._get_recent_robot_data(session, min_real_cycles)
            
            if not real_data['sufficient_data']:
                return self._handle_insufficient_data(real_data)
            
            # Analyze real robot performance patterns
            performance_analysis = self._analyze_real_performance(real_data)
            
            # Calculate optimal simulation constraints
            optimal_constraints = self._calculate_optimal_constraints(performance_analysis)
            
            # Apply constraints to simulation
            success = self._apply_constraints_to_simulation(
                session, simulation_id, optimal_constraints
            )
            
            if success:
                # Log calibration for future reference
                self._log_calibration(optimal_constraints, performance_analysis)
                
                print(f"\n🎉 AUTO-CALIBRATION COMPLETE!")
                print(f"   Simulation {simulation_id} updated with real-world constraints")
                
                return {
                    'success': True,
                    'constraints': optimal_constraints,
                    'performance_analysis': performance_analysis
                }
            else:
                print(f"\n❌ AUTO-CALIBRATION FAILED")
                return {'success': False}
                
        except Exception as e:
            print(f"❌ Error during auto-calibration: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
        finally:
            session.close()
    
    def _get_recent_robot_data(self, session, min_cycles: int):
        """Get recent robot trading data for analysis"""
        
        # Get last 30 days of robot data
        cutoff_date = datetime.now() - timedelta(days=30)
        
        real_cycles = session.query(TradingCycle).filter(
            TradingCycle.cycle_date >= cutoff_date
        ).order_by(TradingCycle.cycle_date).all()
        
        print(f"📊 REAL ROBOT DATA COLLECTION:")
        print(f"   Period: Last 30 days")
        print(f"   Cycles Found: {len(real_cycles)}")
        print(f"   Minimum Required: {min_cycles}")
        
        sufficient_data = len(real_cycles) >= min_cycles
        
        if sufficient_data:
            print(f"   ✅ Sufficient data for calibration")
        else:
            print(f"   ❌ Insufficient data - need {min_cycles - len(real_cycles)} more cycles")
        
        return {
            'cycles': real_cycles,
            'sufficient_data': sufficient_data,
            'count': len(real_cycles)
        }
    
    def _analyze_real_performance(self, real_data):
        """Analyze real robot performance to extract key metrics"""
        
        print(f"\n🔍 ANALYZING REAL ROBOT PERFORMANCE:")
        print("-" * 40)
        
        cycles = real_data['cycles']
        
        # Calculate daily returns
        daily_returns = []
        trading_costs = []
        execution_delays = []
        
        for i, cycle in enumerate(cycles[1:], 1):  # Skip first cycle
            prev_cycle = cycles[i-1]
            
            # Calculate daily return
            daily_return = (cycle.total_value - prev_cycle.total_value) / prev_cycle.total_value
            daily_returns.append(daily_return)
            
            # Estimate trading costs from actions
            actions = cycle.actions_taken or []
            estimated_cost = len(actions) * 0.001 * cycle.total_value  # 0.1% per trade
            trading_costs.append(estimated_cost)
        
        # Calculate statistics
        if daily_returns:
            avg_daily_return = statistics.mean(daily_returns)
            daily_return_std = statistics.stdev(daily_returns) if len(daily_returns) > 1 else 0
            max_daily_return = max(daily_returns)
            min_daily_return = min(daily_returns)
        else:
            avg_daily_return = daily_return_std = max_daily_return = min_daily_return = 0
        
        avg_trading_cost = statistics.mean(trading_costs) if trading_costs else 0
        
        # Estimate market timing efficiency
        # Compare actual returns to theoretical perfect timing
        timing_efficiency = self._estimate_timing_efficiency(daily_returns)
        
        # Estimate slippage from return volatility
        estimated_slippage = daily_return_std * 0.3  # Assume 30% of volatility is slippage
        
        analysis = {
            'avg_daily_return': avg_daily_return,
            'daily_return_std': daily_return_std,
            'max_daily_return': max_daily_return,
            'min_daily_return': min_daily_return,
            'avg_trading_cost': avg_trading_cost,
            'timing_efficiency': timing_efficiency,
            'estimated_slippage': estimated_slippage,
            'total_cycles': len(daily_returns)
        }
        
        print(f"   Average Daily Return: {avg_daily_return*100:+.2f}%")
        print(f"   Daily Return Std Dev: {daily_return_std*100:.2f}%")
        print(f"   Max Daily Return: {max_daily_return*100:+.2f}%")
        print(f"   Min Daily Return: {min_daily_return*100:+.2f}%")
        print(f"   Avg Trading Cost: ${avg_trading_cost:.2f}")
        print(f"   Estimated Timing Efficiency: {timing_efficiency*100:.0f}%")
        print(f"   Estimated Slippage: {estimated_slippage*100:.2f}%")
        
        return analysis
    
    def _estimate_timing_efficiency(self, daily_returns):
        """Estimate market timing efficiency from return patterns"""
        
        if not daily_returns:
            return 0.7  # Default assumption
        
        # Simple heuristic: if returns are consistently positive, timing is good
        positive_days = sum(1 for r in daily_returns if r > 0)
        total_days = len(daily_returns)
        
        if total_days == 0:
            return 0.7
        
        positive_ratio = positive_days / total_days
        
        # Convert to timing efficiency (50% positive = 60% efficiency, 80% positive = 80% efficiency)
        timing_efficiency = 0.4 + (positive_ratio * 0.5)
        
        # Bound between 40% and 90%
        return max(0.4, min(0.9, timing_efficiency))
    
    def _calculate_optimal_constraints(self, analysis):
        """Calculate optimal simulation constraints based on real performance"""
        
        print(f"\n⚙️  CALCULATING OPTIMAL CONSTRAINTS:")
        print("-" * 40)
        
        # Market timing efficiency (based on observed performance)
        timing_efficiency = analysis['timing_efficiency']
        
        # Slippage (based on return volatility)
        slippage_per_day = max(0.001, min(0.01, analysis['estimated_slippage']))
        
        # Trading costs (based on observed costs)
        trading_fee = float(os.getenv('TRADING_FEE', '0.001'))
        
        # Volatility drag (based on return standard deviation)
        volatility_drag = analysis['daily_return_std'] * 0.2  # 20% of observed volatility
        volatility_drag = max(0.001, min(0.005, volatility_drag))
        
        # Daily return cap (based on observed maximum)
        max_daily_return = analysis['max_daily_return'] * 1.2  # 20% above observed max
        max_daily_return = max(0.02, min(0.08, max_daily_return))  # Between 2% and 8%
        
        constraints = {
            'market_timing_efficiency': timing_efficiency,
            'slippage_per_day': slippage_per_day,
            'trading_fee': trading_fee,
            'volatility_drag': volatility_drag,
            'max_daily_return': max_daily_return,
            'calibration_date': datetime.now().isoformat(),
            'based_on_cycles': analysis['total_cycles']
        }
        
        print(f"   Market Timing Efficiency: {timing_efficiency*100:.0f}%")
        print(f"   Daily Slippage: {slippage_per_day*100:.2f}%")
        print(f"   Trading Fee: {trading_fee*100:.1f}%")
        print(f"   Volatility Drag: {volatility_drag*100:.2f}%")
        print(f"   Max Daily Return: {max_daily_return*100:.1f}%")
        print(f"   Based on {analysis['total_cycles']} real cycles")
        
        return constraints
    
    def _apply_constraints_to_simulation(self, session, simulation_id, constraints):
        """Apply the calculated constraints to the simulation"""
        
        print(f"\n🔄 APPLYING CONSTRAINTS TO SIMULATION {simulation_id}:")
        print("-" * 50)
        
        try:
            # Get simulation
            simulation = session.query(Simulation).filter(Simulation.id == simulation_id).first()
            if not simulation:
                print(f"❌ Simulation {simulation_id} not found")
                return False
            
            # Get simulation cycles
            cycles = session.query(SimulationCycle).filter(
                SimulationCycle.simulation_id == simulation_id
            ).order_by(SimulationCycle.cycle_number).all()
            
            if not cycles:
                print(f"❌ No cycles found for simulation {simulation_id}")
                return False
            
            # Recalculate simulation with new constraints
            current_capital = simulation.starting_reserve
            total_trading_costs = 0
            
            for i, cycle in enumerate(cycles):
                # Get original return
                if i == 0:
                    original_return = (cycle.total_value - simulation.starting_reserve) / simulation.starting_reserve
                else:
                    prev_value = cycles[i-1].total_value
                    original_return = (cycle.total_value - prev_value) / prev_value
                
                # Apply new constraints
                timing_adjusted = original_return * constraints['market_timing_efficiency']
                
                # Cap daily return
                capped_return = min(constraints['max_daily_return'], 
                                  max(-0.05, timing_adjusted))  # Floor at -5%
                
                # Subtract costs
                after_costs = (capped_return 
                             - constraints['slippage_per_day']
                             - constraints['volatility_drag']
                             - (constraints['trading_fee'] * 2))  # Buy + sell
                
                # Calculate new capital
                new_capital = current_capital * (1 + after_costs)
                
                # Track costs
                daily_cost = current_capital * constraints['trading_fee'] * 2
                total_trading_costs += daily_cost
                
                # Update cycle
                cycle.total_value = new_capital
                cycle.portfolio_value = new_capital * 0.95
                cycle.bnb_reserve = new_capital * 0.05
                cycle.trading_costs = daily_cost
                
                current_capital = new_capital
            
            # Update simulation record
            simulation.final_total_value = current_capital
            simulation.final_portfolio_value = current_capital * 0.95
            simulation.final_reserve_value = current_capital * 0.05
            simulation.fee_estimate = total_trading_costs
            simulation.total_trading_costs = total_trading_costs
            simulation.realized_pnl = current_capital - simulation.starting_reserve
            simulation.engine_version = f"auto_calibrated_v{datetime.now().strftime('%Y%m%d')}"
            
            # Store calibration info
            calibration_info = {
                'calibration_date': constraints['calibration_date'],
                'constraints_applied': constraints,
                'based_on_real_cycles': constraints['based_on_cycles']
            }
            
            # Update data source to reflect calibration
            simulation.data_source = f"historical + auto_calibrated ({constraints['based_on_cycles']} real cycles)"
            
            session.commit()
            
            # Calculate new performance
            new_return = ((current_capital - simulation.starting_reserve) / simulation.starting_reserve) * 100
            
            print(f"   ✅ Simulation updated successfully")
            print(f"   New Final Value: ${current_capital:.2f}")
            print(f"   New Return: {new_return:.1f}%")
            print(f"   Engine Version: {simulation.engine_version}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error applying constraints: {e}")
            session.rollback()
            return False
    
    def _log_calibration(self, constraints, analysis):
        """Log calibration for future reference"""
        
        calibration_log = {
            'timestamp': datetime.now().isoformat(),
            'constraints': constraints,
            'analysis': analysis
        }
        
        self.calibration_history.append(calibration_log)
        
        # Save to file for persistence
        log_file = 'calibration_history.json'
        try:
            with open(log_file, 'w') as f:
                json.dump(self.calibration_history, f, indent=2)
            print(f"   📝 Calibration logged to {log_file}")
        except Exception as e:
            print(f"   ⚠️  Could not save calibration log: {e}")
    
    def _handle_insufficient_data(self, real_data):
        """Handle case where there's insufficient real robot data"""
        
        print(f"\n⚠️  INSUFFICIENT DATA FOR AUTO-CALIBRATION")
        print("-" * 45)
        
        cycles_needed = 7 - real_data['count']
        
        print(f"   Current real cycles: {real_data['count']}")
        print(f"   Minimum required: 7")
        print(f"   Additional cycles needed: {cycles_needed}")
        print()
        
        print(f"📋 RECOMMENDATIONS:")
        print(f"   1. Continue running robot in LIVE TRADING mode (not dry-run)")
        print(f"   2. Wait {cycles_needed} more days for daily cycles")
        print(f"   3. Run auto-calibration again when sufficient REAL data available")
        print(f"\n⚠️  CRITICAL: Only LIVE trading data should be used for calibration!")
        print(f"   Dry-run data is already calibrated and creates circular logic.")
        print(f"   4. Current simulation constraints remain unchanged")
        
        return {
            'success': False,
            'reason': 'insufficient_data',
            'cycles_needed': cycles_needed,
            'current_cycles': real_data['count']
        }

def run_auto_calibration(simulation_id: int = 1):
    """Run auto-calibration for a simulation"""
    
    calibrator = SimulationAutoCalibrator()
    result = calibrator.auto_calibrate(simulation_id)
    
    return result

if __name__ == "__main__":
    run_auto_calibration()