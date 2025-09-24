#!/usr/bin/env python3
import sqlite3
import os
import sys

def diagnose_failed_simulations():
    """Diagnose why simulations failed"""
    print("🔍 DIAGNOSING FAILED SIMULATIONS")
    print("=" * 50)
    
    # Check multiple possible database locations
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
        
        # Get failed simulations with details
        cursor.execute("""
            SELECT id, name, status, error_message, created_at, 
                   start_date, duration_days, starting_reserve, calibration_profile
            FROM simulations 
            WHERE status = 'failed' 
            ORDER BY created_at DESC
        """)
        
        failed_sims = cursor.fetchall()
        
        if not failed_sims:
            print("ℹ️  No failed simulations found")
            conn.close()
            return
        
        print(f"❌ Found {len(failed_sims)} failed simulations:")
        print()
        
        for sim in failed_sims:
            sim_id, name, status, error_msg, created_at, start_date, duration, capital, profile = sim
            
            print(f"📊 Simulation: {name}")
            print(f"   ID: {sim_id}")
            print(f"   Status: {status}")
            print(f"   Created: {created_at}")
            print(f"   Start Date: {start_date}")
            print(f"   Duration: {duration} days")
            print(f"   Capital: ${capital}")
            print(f"   Profile: {profile}")
            
            if error_msg:
                print(f"   ❌ Error: {error_msg}")
            else:
                print(f"   ❌ Error: No error message recorded")
            
            # Check if any cycles were created
            cursor.execute("SELECT COUNT(*) FROM simulation_cycles WHERE simulation_id = ?", (sim_id,))
            cycle_count = cursor.fetchone()[0]
            print(f"   📈 Cycles Created: {cycle_count}")
            
            if cycle_count > 0:
                # Get cycle details
                cursor.execute("""
                    SELECT cycle_number, total_value, portfolio_value, cycle_date 
                    FROM simulation_cycles 
                    WHERE simulation_id = ? 
                    ORDER BY cycle_number DESC 
                    LIMIT 3
                """, (sim_id,))
                
                cycles = cursor.fetchall()
                print(f"   📊 Last cycles:")
                for cycle_num, total_val, portfolio_val, cycle_date in cycles:
                    print(f"      Cycle {cycle_num}: ${total_val:.2f} on {cycle_date}")
            
            print()
        
        # Check calibration profile issues
        print("🔧 CALIBRATION PROFILE CHECK:")
        cursor.execute("SELECT DISTINCT calibration_profile FROM simulations WHERE status = 'failed'")
        profiles = cursor.fetchall()
        
        for (profile,) in profiles:
            print(f"   Profile used: {profile}")
            
            # Check if profile file exists
            profile_path = f"calibration_profiles/{profile}.json"
            if os.path.exists(profile_path):
                print(f"   ✅ Profile file exists: {profile_path}")
            else:
                print(f"   ❌ Profile file missing: {profile_path}")
                
                # List available profiles
                if os.path.exists("calibration_profiles"):
                    available = os.listdir("calibration_profiles")
                    json_files = [f for f in available if f.endswith('.json')]
                    if json_files:
                        print(f"   📁 Available profiles: {', '.join(json_files)}")
                    else:
                        print(f"   📁 No profile files found in calibration_profiles/")
                else:
                    print(f"   📁 calibration_profiles/ directory not found")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error diagnosing simulations: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose_failed_simulations()