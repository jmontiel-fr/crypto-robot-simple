#!/usr/bin/env python3
import sqlite3
import os

def fix_simulation_status():
    """Fix simulation status for completed simulations"""
    print("🔧 FIXING SIMULATION STATUS")
    print("=" * 40)
    
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
    
    print(f"📁 Using database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Find simulations that failed due to Unicode error but have cycles
        cursor.execute("""
            SELECT s.id, s.name, s.duration_days, COUNT(sc.id) as cycle_count,
                   s.starting_reserve, MAX(sc.total_value) as final_value
            FROM simulations s
            LEFT JOIN simulation_cycles sc ON s.id = sc.simulation_id
            WHERE s.status = 'failed' 
            AND s.error_message LIKE '%charmap%codec%'
            GROUP BY s.id
            HAVING cycle_count > 0
        """)
        
        failed_sims = cursor.fetchall()
        
        if not failed_sims:
            print("ℹ️  No simulations to fix")
            conn.close()
            return
        
        print(f"🔧 Found {len(failed_sims)} simulations to fix:")
        
        for sim_id, name, duration, cycle_count, starting, final_value in failed_sims:
            if cycle_count >= duration:  # Has all expected cycles
                # Calculate return
                return_pct = ((final_value - starting) / starting) * 100
                
                print(f"   ✅ {name}: {cycle_count}/{duration} cycles, +{return_pct:.1f}%")
                
                # Update status to completed
                cursor.execute("""
                    UPDATE simulations 
                    SET status = 'completed', 
                        error_message = NULL
                    WHERE id = ?
                """, (sim_id,))
            else:
                print(f"   ⚠️  {name}: Only {cycle_count}/{duration} cycles - keeping as failed")
        
        conn.commit()
        conn.close()
        
        print("\n✅ Simulation status fixed!")
        print("   All completed simulations now show as 'completed'")
        
    except Exception as e:
        print(f"❌ Error fixing simulations: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_simulation_status()