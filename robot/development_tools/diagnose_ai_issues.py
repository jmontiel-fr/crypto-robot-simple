#!/usr/bin/env python3
"""
Diagnose AI enhancement issues causing performance degradation
"""
import sqlite3
import os

def diagnose_ai_issues():
    """Analyze what's causing the AI performance issues"""
    print("🔍 DIAGNOSING AI ENHANCEMENT ISSUES")
    print("=" * 60)
    
    # Find database
    db_paths = ['trading_bot.db', 'data/cryptorobot.db', 'crypto_robot.db']
    db_path = None
    
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ No database found")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get recent AI-enhanced simulations
        cursor.execute("""
            SELECT id, name, starting_reserve, duration_days, created_at
            FROM simulations 
            WHERE status = 'completed' 
            AND duration_days = 30
            ORDER BY created_at DESC
            LIMIT 8
        """)
        
        simulations = cursor.fetchall()
        
        print(f"📊 Analyzing {len(simulations)} recent simulations:")
        print()
        
        issues_found = []
        
        for sim_id, name, starting_capital, duration, created_at in simulations:
            # Get cycle data
            cursor.execute("""
                SELECT cycle_number, total_value, portfolio_value, bnb_reserve
                FROM simulation_cycles 
                WHERE simulation_id = ? 
                ORDER BY cycle_number
            """, (sim_id,))
            
            cycles = cursor.fetchall()
            
            if cycles:
                final_value = cycles[-1][1]
                total_return = ((final_value - starting_capital) / starting_capital) * 100
                
                print(f"🔍 {name}: ${starting_capital:.0f} → ${final_value:.2f} ({total_return:+.1f}%)")
                
                # Calculate cycle returns
                cycle_returns = []
                for i in range(1, len(cycles)):
                    prev_value = cycles[i-1][1]
                    curr_value = cycles[i][1]
                    cycle_return = (curr_value - prev_value) / prev_value
                    cycle_returns.append(cycle_return)
                
                negative_cycles = sum(1 for ret in cycle_returns if ret < 0)
                avg_cycle_return = sum(cycle_returns) / len(cycle_returns) if cycle_returns else 0
                
                print(f"   • Negative cycles: {negative_cycles}/{len(cycle_returns)}")
                print(f"   • Average cycle return: {avg_cycle_return:+.3f}")
                print(f"   • Total cycles: {len(cycles)}")
                
                # Identify specific issues
                if total_return < 10:
                    issues_found.append(f"{name}: Catastrophic performance ({total_return:.1f}%)")
                if negative_cycles > len(cycles) * 0.4:
                    issues_found.append(f"{name}: Too many negative cycles ({negative_cycles}/{len(cycles)})")
                if avg_cycle_return < 0.001:  # Less than 0.1% per cycle
                    issues_found.append(f"{name}: Very low cycle returns ({avg_cycle_return:+.3f})")
                
                print()
        
        print(f"🚨 ISSUES IDENTIFIED:")
        print("=" * 30)
        if issues_found:
            for issue in issues_found:
                print(f"   ❌ {issue}")
        else:
            print("   ℹ️  No specific issues identified in data")
        
        print(f"\n💡 LIKELY ROOT CAUSES:")
        print("=" * 30)
        print("   1. 🎯 AI Signal Noise: Hybrid signals may be creating conflicting trades")
        print("   2. 🔄 Over-optimization: Too frequent regime switching hurting performance")
        print("   3. 📊 Position Sizing Issues: AI adjustments may be too aggressive")
        print("   4. 🧠 Insufficient Data: AI needs more historical data to work properly")
        print("   5. ⚖️  Risk Penalties: Volatility penalties may be too harsh")
        
        print(f"\n🔧 RECOMMENDED FIXES:")
        print("=" * 30)
        print("   1. Reduce AI signal sensitivity")
        print("   2. Limit regime switching frequency")
        print("   3. Cap position adjustments to ±25% instead of ±50%")
        print("   4. Increase minimum data requirements")
        print("   5. Reduce volatility penalties")
        print("   6. Add AI confidence thresholds")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error diagnosing issues: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose_ai_issues()