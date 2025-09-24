#!/usr/bin/env python3
import sqlite3
import os

def stop_running_simulations():
    """Stop all running simulations"""
    print("⏹️  STOPPING RUNNING SIMULATIONS")
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
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get running simulations
        cursor.execute("SELECT id, name FROM simulations WHERE status = 'running'")
        running_sims = cursor.fetchall()
        
        if not running_sims:
            print("ℹ️  No running simulations to stop")
            conn.close()
            return
        
        print(f"⏹️  Found {len(running_sims)} running simulations:")
        for sim_id, name in running_sims:
            print(f"   • {name} (ID: {sim_id})")
        
        # Mark as failed/stopped
        cursor.execute("UPDATE simulations SET status = 'stopped', error_message = 'Manually stopped' WHERE status = 'running'")
        stopped_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ Stopped {stopped_count} running simulations")
        
    except Exception as e:
        print(f"❌ Error stopping simulations: {e}")

if __name__ == "__main__":
    stop_running_simulations()