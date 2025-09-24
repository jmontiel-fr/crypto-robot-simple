#!/usr/bin/env python3
import sqlite3
import os

def check_simulations():
    # Check multiple possible database locations
    db_paths = ['trading_bot.db', 'data/cryptorobot.db', 'crypto_robot.db']
    db_path = None
    
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ Database file not found in any of these locations:")
        for path in db_paths:
            print(f"   - {path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if simulations table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='simulations'")
        if not cursor.fetchone():
            print("❌ Simulations table not found in database")
            conn.close()
            return
        
        # Get all simulations
        cursor.execute("SELECT name, status, created_at FROM simulations ORDER BY created_at DESC LIMIT 10")
        simulations = cursor.fetchall()
        
        if not simulations:
            print("ℹ️  No simulations found in database")
        else:
            print(f"📊 Found {len(simulations)} recent simulations:")
            for name, status, created_at in simulations:
                print(f"  • {name} - Status: {status} - Created: {created_at}")
        
        # Check pending specifically
        cursor.execute("SELECT COUNT(*) FROM simulations WHERE status = 'pending'")
        pending_count = cursor.fetchone()[0]
        print(f"\n🔄 Pending simulations: {pending_count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == "__main__":
    check_simulations()