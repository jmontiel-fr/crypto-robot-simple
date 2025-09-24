#!/usr/bin/env python3
import sqlite3
import os

def clear_pending_simulations():
    """Clear all pending simulations from database"""
    print("🧹 CLEARING PENDING SIMULATIONS")
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
        
        # Get pending simulations
        cursor.execute("SELECT id, name FROM simulations WHERE status = 'pending'")
        pending_sims = cursor.fetchall()
        
        if not pending_sims:
            print("ℹ️  No pending simulations to clear")
            conn.close()
            return
        
        print(f"🗑️  Found {len(pending_sims)} pending simulations:")
        for sim_id, name in pending_sims:
            print(f"   • {name} (ID: {sim_id})")
        
        # Delete pending simulations
        cursor.execute("DELETE FROM simulations WHERE status = 'pending'")
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ Cleared {deleted_count} pending simulations")
        print("   Ready for fresh simulation generation!")
        
    except Exception as e:
        print(f"❌ Error clearing simulations: {e}")

if __name__ == "__main__":
    clear_pending_simulations()