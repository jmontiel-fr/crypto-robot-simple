#!/usr/bin/env python3
"""
Migrate database schema to support Enhanced Realistic Mode v5.0
"""

import os
import sys
import sqlite3

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def migrate_database_schema():
    """Add enhanced realistic mode columns to existing database"""
    
    print("🔧 MIGRATING DATABASE SCHEMA FOR ENHANCED REALISTIC MODE v5.0")
    print("=" * 70)
    
    # Find database file
    db_paths = [
        'crypto_robot.db',
        'data/cryptorobot.db',
        'src/crypto_robot.db',
        'robot.db'
    ]
    
    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("📁 No existing database found. Creating new database...")
        # Create database using the models
        try:
            from src.database import DatabaseManager
            db_manager = DatabaseManager()
            print("✅ New database created with enhanced schema!")
            return True
        except Exception as e:
            print(f"❌ Error creating database: {e}")
            return False
    
    print(f"📁 Found database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n📊 ADDING ENHANCED COLUMNS TO SIMULATIONS TABLE:")
        
        # Add columns to simulations table
        enhanced_sim_columns = [
            ('realistic_mode', 'BOOLEAN DEFAULT FALSE'),
            ('total_trading_costs', 'FLOAT DEFAULT 0.0'),
            ('failed_trades', 'INTEGER DEFAULT 0'),
            ('average_execution_delay', 'FLOAT DEFAULT 0.0'),
            ('success_rate', 'FLOAT DEFAULT 100.0')
        ]
        
        for col_name, col_type in enhanced_sim_columns:
            try:
                cursor.execute(f"ALTER TABLE simulations ADD COLUMN {col_name} {col_type}")
                print(f"   ✅ Added {col_name} column")
            except sqlite3.OperationalError as e:
                if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                    print(f"   ℹ️  {col_name} column already exists")
                else:
                    print(f"   ❌ Error adding {col_name}: {e}")
        
        print("\n📈 ADDING ENHANCED COLUMNS TO SIMULATION_CYCLES TABLE:")
        
        # Add columns to simulation_cycles table
        enhanced_cycle_columns = [
            ('trading_costs', 'FLOAT DEFAULT 0.0'),
            ('execution_delay', 'FLOAT DEFAULT 0.0'),
            ('failed_orders', 'INTEGER DEFAULT 0'),
            ('market_conditions', 'TEXT')
        ]
        
        for col_name, col_type in enhanced_cycle_columns:
            try:
                cursor.execute(f"ALTER TABLE simulation_cycles ADD COLUMN {col_name} {col_type}")
                print(f"   ✅ Added {col_name} column")
            except sqlite3.OperationalError as e:
                if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                    print(f"   ℹ️  {col_name} column already exists")
                else:
                    print(f"   ❌ Error adding {col_name}: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ DATABASE MIGRATION COMPLETED!")
        print(f"   Database: {db_path}")
        print(f"   Enhanced columns added for realistic mode")
        
        return True
        
    except Exception as e:
        print(f"❌ Error migrating database: {e}")
        return False

def verify_migration():
    """Verify that the migration was successful"""
    
    print(f"\n🔍 VERIFYING MIGRATION...")
    
    try:
        from src.database import DatabaseManager, Simulation, SimulationCycle
        
        db_manager = DatabaseManager()
        
        # Test creating a simulation with enhanced columns
        with db_manager.get_session() as session:
            test_sim = Simulation(
                name="Migration Test",
                start_date=datetime.now(),
                duration_days=1,
                cycle_length_minutes=360,
                starting_reserve=1000.0,
                realistic_mode=True,
                total_trading_costs=10.0,
                failed_trades=1,
                average_execution_delay=5.0,
                success_rate=98.0,
                status='completed'
            )
            session.add(test_sim)
            session.flush()
            
            test_cycle = SimulationCycle(
                simulation_id=test_sim.id,
                cycle_number=1,
                portfolio_value=900.0,
                bnb_reserve=100.0,
                total_value=1000.0,
                cycle_date=datetime.now(),
                trading_costs=2.5,
                execution_delay=3.2,
                failed_orders=0,
                market_conditions='{"test": true}'
            )
            session.add(test_cycle)
            session.commit()
            
            print("   ✅ Successfully created test records with enhanced columns")
            
            # Clean up
            session.delete(test_cycle)
            session.delete(test_sim)
            session.commit()
            
        return True
        
    except Exception as e:
        print(f"   ❌ Migration verification failed: {e}")
        return False

if __name__ == "__main__":
    from datetime import datetime
    
    success = migrate_database_schema()
    
    if success:
        verify_success = verify_migration()
        if verify_success:
            print(f"\n🎉 MIGRATION SUCCESSFUL!")
            print(f"   Enhanced Realistic Mode v5.0 is ready to use!")
            print(f"\n💡 NEXT STEPS:")
            print(f"   1. Start web server: python src/web_app.py")
            print(f"   2. Create new simulation with realistic mode")
            print(f"   3. Enjoy realistic trading constraints!")
        else:
            print(f"\n⚠️  MIGRATION COMPLETED BUT VERIFICATION FAILED")
            print(f"   Check the error messages above")
    else:
        print(f"\n❌ MIGRATION FAILED")
        print(f"   Check the error messages above")
    
    sys.exit(0 if success else 1)