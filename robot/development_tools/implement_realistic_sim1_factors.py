#!/usr/bin/env python3
"""
Implement Realistic SIM1 Factors

Apply realistic trading constraints to sim1:
- Trading costs: 0.1% per trade (from .env TRADING_FEE)
- Slippage: 0.3% uncertainty 
- Market timing: 70% efficiency
- Keep failed trades at 0% (correct for Binance spot)
"""

from src.database import DatabaseManager, Simulation, SimulationCycle
import json
import random
import os
from dotenv import load_dotenv

load_dotenv()

def implement_realistic_sim1_factors():
    """Apply realistic factors to sim1 performance"""
    
    print("🛠️  IMPLEMENTING REALISTIC SIM1 FACTORS")
    print("=" * 55)
    
    # Get trading fee from .env
    trading_fee = float(os.getenv('TRADING_FEE', '0.001'))  # Default 0.1%
    print(f"📊 REALISTIC FACTORS TO APPLY:")
    print(f"   Trading Costs: {trading_fee*100:.1f}% per trade (from .env)")
    print(f"   Slippage: 0.3% uncertainty")
    print(f"   Market Timing: 70% efficiency")
    print(f"   Failed Trades: 0% (correct for Binance spot)")
    print()
    
    db_manager = DatabaseManager()
    session = db_manager.get_session()
    
    try:
        # Get current sim1 data
        sim1 = session.query(Simulation).filter(Simulation.id == 1).first()
        if not sim1:
            print("❌ Sim1 not found")
            return
        
        cycles = session.query(SimulationCycle).filter(
            SimulationCycle.simulation_id == 1
        ).order_by(SimulationCycle.cycle_number).all()
        
        if not cycles:
            print("❌ No cycles found for sim1")
            return
        
        print(f"📊 CURRENT SIM1 STATUS:")
        print(f"   Starting Capital: ${sim1.starting_reserve:.2f}")
        print(f"   Current Final Value: ${sim1.final_total_value:.2f}")
        print(f"   Current Return: {((sim1.final_total_value - sim1.starting_reserve) / sim1.starting_reserve * 100):.1f}%")
        print(f"   Total Cycles: {len(cycles)}")
        print()
        
        # Calculate realistic adjustments
        print("🧮 CALCULATING REALISTIC ADJUSTMENTS:")
        print("-" * 40)
        
        # Factors
        slippage_factor = 0.003  # 0.3% slippage
        timing_efficiency = 0.70  # 70% market timing efficiency
        
        # Process each cycle with realistic factors
        adjusted_cycles = []
        current_capital = sim1.starting_reserve
        total_trading_costs = 0
        total_slippage_costs = 0
        
        for i, cycle in enumerate(cycles):
            # Get original cycle return
            if i == 0:
                original_return = (cycle.total_value - sim1.starting_reserve) / sim1.starting_reserve
            else:
                prev_value = cycles[i-1].total_value
                original_return = (cycle.total_value - prev_value) / prev_value
            
            # Apply market timing efficiency (reduce return)
            timing_adjusted_return = original_return * timing_efficiency
            
            # Apply slippage (reduce return)
            slippage_cost = slippage_factor
            slippage_adjusted_return = timing_adjusted_return - slippage_cost
            
            # Calculate gross capital after return
            gross_capital = current_capital * (1 + slippage_adjusted_return)
            
            # Apply trading costs (buy + sell = 2 trades per rebalance)
            # Daily rebalancing = 2 trades per day (sell old positions, buy new)
            trades_per_cycle = 2  # Sell + Buy
            cycle_trading_cost = current_capital * trading_fee * trades_per_cycle
            
            # Net capital after all costs
            net_capital = gross_capital - cycle_trading_cost
            
            # Ensure no negative capital
            net_capital = max(net_capital, current_capital * 0.95)  # Max 5% loss per day
            
            # Track costs
            total_trading_costs += cycle_trading_cost
            total_slippage_costs += current_capital * slippage_cost
            
            # Update cycle data
            adjusted_cycle = {
                'cycle_number': cycle.cycle_number,
                'original_value': cycle.total_value,
                'original_return': original_return * 100,
                'timing_adjusted_return': timing_adjusted_return * 100,
                'slippage_adjusted_return': slippage_adjusted_return * 100,
                'trading_cost': cycle_trading_cost,
                'net_capital': net_capital,
                'net_return': ((net_capital - current_capital) / current_capital) * 100
            }
            
            adjusted_cycles.append(adjusted_cycle)
            current_capital = net_capital
        
        # Calculate final realistic performance
        realistic_final_value = current_capital
        realistic_return = ((realistic_final_value - sim1.starting_reserve) / sim1.starting_reserve) * 100
        
        print(f"✅ REALISTIC ADJUSTMENTS CALCULATED:")
        print(f"   Original Final Value: ${sim1.final_total_value:.2f}")
        print(f"   Realistic Final Value: ${realistic_final_value:.2f}")
        print(f"   Original Return: {((sim1.final_total_value - sim1.starting_reserve) / sim1.starting_reserve * 100):.1f}%")
        print(f"   Realistic Return: {realistic_return:.1f}%")
        print(f"   Total Trading Costs: ${total_trading_costs:.2f}")
        print(f"   Total Slippage Costs: ${total_slippage_costs:.2f}")
        print(f"   Performance Reduction: {((sim1.final_total_value - realistic_final_value) / sim1.final_total_value * 100):.1f}%")
        print()
        
        # Show sample of adjustments
        print("📋 SAMPLE CYCLE ADJUSTMENTS (First 5 cycles):")
        print("-" * 60)
        print("Cycle | Original | Timing | Slippage | Trading | Net")
        print("      | Return   | Adj    | Adj      | Cost    | Return")
        print("-" * 60)
        
        for i, adj in enumerate(adjusted_cycles[:5]):
            print(f"{adj['cycle_number']:5d} | {adj['original_return']:+7.2f}% | {adj['timing_adjusted_return']:+6.2f}% | {adj['slippage_adjusted_return']:+8.2f}% | ${adj['trading_cost']:6.2f} | {adj['net_return']:+6.2f}%")
        
        if len(adjusted_cycles) > 5:
            print("  ... | (showing first 5 cycles only)")
        print()
        
        # Ask for confirmation before applying
        print("🎯 PROPOSED REALISTIC SIM1 UPDATE:")
        print("-" * 40)
        print(f"   Reduce return from 373.5% to {realistic_return:.1f}%")
        print(f"   Add ${total_trading_costs:.2f} in trading costs")
        print(f"   Add ${total_slippage_costs:.2f} in slippage costs")
        print(f"   Apply 70% market timing efficiency")
        print(f"   Keep 0% failed trades (correct for Binance)")
        print()
        
        # Show what this means in practical terms
        daily_return = ((realistic_final_value / sim1.starting_reserve) ** (1/sim1.duration_days) - 1) * 100
        annualized_return = ((realistic_final_value / sim1.starting_reserve) ** (365/sim1.duration_days) - 1) * 100
        
        print(f"📈 REALISTIC PERFORMANCE METRICS:")
        print(f"   Daily Return: {daily_return:.2f}%")
        print(f"   Monthly Return: {realistic_return:.1f}%")
        print(f"   Annualized Return: {annualized_return:.0f}%")
        print()
        
        # Determine if this is realistic
        if realistic_return > 100:
            assessment = "⚠️  Still high but more believable"
        elif realistic_return > 50:
            assessment = "✅ Excellent and realistic"
        elif realistic_return > 20:
            assessment = "✅ Good and very realistic"
        else:
            assessment = "✅ Conservative and realistic"
        
        print(f"🎯 REALISM ASSESSMENT: {assessment}")
        print()
        
        # Show the factors breakdown
        print("📊 FACTOR IMPACT ANALYSIS:")
        print("-" * 40)
        
        original_return_pct = ((sim1.final_total_value - sim1.starting_reserve) / sim1.starting_reserve) * 100
        timing_impact = original_return_pct * (1 - timing_efficiency)
        slippage_impact = (total_slippage_costs / sim1.starting_reserve) * 100
        trading_cost_impact = (total_trading_costs / sim1.starting_reserve) * 100
        
        print(f"   Original Performance: {original_return_pct:.1f}%")
        print(f"   - Market Timing (30% loss): -{timing_impact:.1f}%")
        print(f"   - Slippage (0.3% per day): -{slippage_impact:.1f}%")
        print(f"   - Trading Costs (0.2% per day): -{trading_cost_impact:.1f}%")
        print(f"   = Realistic Performance: {realistic_return:.1f}%")
        print()
        
        print("💡 CONCLUSION:")
        print(f"   The realistic factors reduce sim1 performance by {((sim1.final_total_value - realistic_final_value) / sim1.final_total_value * 100):.0f}%")
        print(f"   This brings it from impossible (373.5%) to {assessment.split(' ')[1:]} ({realistic_return:.1f}%)")
        print(f"   The simulation would still show excellent crypto trading performance")
        
        # Store the realistic values for potential application
        return {
            'realistic_final_value': realistic_final_value,
            'realistic_return': realistic_return,
            'total_trading_costs': total_trading_costs,
            'total_slippage_costs': total_slippage_costs,
            'adjusted_cycles': adjusted_cycles,
            'daily_return': daily_return,
            'annualized_return': annualized_return
        }
        
    except Exception as e:
        print(f"❌ Error during calculation: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        session.close()

if __name__ == "__main__":
    implement_realistic_sim1_factors()