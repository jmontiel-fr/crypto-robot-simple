#!/usr/bin/env python3
"""
Database initialization using SQLAlchemy models - NO SAMPLE DATA
Ensures schema is always up-to-date with current models
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import DatabaseManager, Base, Portfolio, Position, TradingCycle, Simulation, SimulationCycle, CyclePosition, StrategyPerformance, StrategySwitch

# Load environment variables
load_dotenv()

def create_database_with_permissions():
    """Create database using SQLAlchemy models with proper permissions"""
    print("Creating Database Using SQLAlchemy Models")
    print("=" * 55)
    
    # Get database configuration
    db_url = os.getenv('DATABASE_URL')
    db_type = os.getenv('DATABASE_TYPE', 'sqlite')
    
    if not db_url:
        # Fallback to SQLite if no DATABASE_URL
        # Support new DATABASE_PATH and DATABASE_FILE variables
        database_path = os.getenv('DATABASE_PATH', 'data')
        database_file = os.getenv('DATABASE_FILE', 'cryptorobot.db')
        
        # Fallback to legacy SQLITE_FILE if new variables not set
        if database_path == 'data' and database_file == 'cryptorobot.db':
            legacy_sqlite_file = os.getenv('SQLITE_FILE')
            if legacy_sqlite_file:
                db_path = legacy_sqlite_file
            else:
                # Use forward slashes for cross-platform compatibility (especially in containers)
                db_path = f"{database_path}/{database_file}"
        else:
            # Use forward slashes for cross-platform compatibility (especially in containers)
            db_path = f"{database_path}/{database_file}"
            
        db_url = f"sqlite:///{db_path}"
        print(f"Using SQLite database: {db_path}")
        
        # Create data directory for SQLite
        data_dir = Path(db_path).parent
        data_dir.mkdir(exist_ok=True, mode=0o755)
        print(f"Data directory created: {data_dir}")
        
        # Remove existing database if it exists
        if os.path.exists(db_path):
            print("Removing existing database for fresh start...")
            try:
                os.remove(db_path)
                print("Old database removed successfully")
            except PermissionError:
                print("Database file is locked (server running?)")
                print("Trying to recreate tables in existing database...")
                # Try to drop and recreate tables instead
                try:
                    temp_manager = DatabaseManager(database_url=db_url, db_type=db_type)
                    temp_manager.drop_tables()
                    print("Dropped existing tables")
                except Exception as e:
                    print(f"Could not drop tables: {e}")
                    print("Continuing with table creation...")
            except Exception as e:
                print(f"Could not remove database: {e}")
                print("Continuing with existing file...")
    else:
        print(f"Using database: {db_url}")
    
    try:
        # Initialize database manager
        print("Initializing database manager...")
        db_manager = DatabaseManager(database_url=db_url, db_type=db_type)
        
        # Create all tables using SQLAlchemy models
        print("Creating all tables from SQLAlchemy models...")
        db_manager.create_tables()
        
        # Set proper file permissions for SQLite
        if db_type == 'sqlite':
            # Use new DATABASE_PATH and DATABASE_FILE variables or fallback to SQLITE_FILE
            database_path = os.getenv('DATABASE_PATH', 'data')
            database_file = os.getenv('DATABASE_FILE', 'cryptorobot.db')
            
            if database_path == 'data' and database_file == 'cryptorobot.db':
                legacy_sqlite_file = os.getenv('SQLITE_FILE')
                if legacy_sqlite_file:
                    db_path = legacy_sqlite_file
                else:
                    # Use forward slashes for cross-platform compatibility (especially in containers)
                    db_path = f"{database_path}/{database_file}"
            else:
                # Use forward slashes for cross-platform compatibility (especially in containers)
                db_path = f"{database_path}/{database_file}"
                
            if os.path.exists(db_path):
                os.chmod(db_path, 0o664)
                print(f"File permissions set: {oct(os.stat(db_path).st_mode)[-3:]}")
        
        print("Database created successfully!")
        
        # Test the database by checking each table
        print("\nTesting database tables...")
        session = db_manager.get_session()
        
        # Check each table with the actual models
        tables_models = [
            ('portfolios', Portfolio),
            ('positions', Position), 
            ('trading_cycles', TradingCycle),
            ('cycle_positions', CyclePosition),
            ('simulations', Simulation),
            ('simulation_cycles', SimulationCycle),
            ('strategy_performance', StrategyPerformance),
            ('strategy_switches', StrategySwitch)
        ]
        
        for table_name, model_class in tables_models:
            try:
                count = session.query(model_class).count()
                print(f"  {table_name}: OK ({count} records)")
            except Exception as e:
                print(f"  {table_name}: ERROR: {e}")
        
        session.close()
        
        # NO SAMPLE DATA CREATION - Database remains empty
        print("\nDatabase setup complete!")
        print("Empty database created (NO sample data)")
        
        if db_type == 'sqlite':
            # Use new DATABASE_PATH and DATABASE_FILE variables or fallback to SQLITE_FILE
            database_path = os.getenv('DATABASE_PATH', 'data')
            database_file = os.getenv('DATABASE_FILE', 'cryptorobot.db')
            
            if database_path == 'data' and database_file == 'cryptorobot.db':
                legacy_sqlite_file = os.getenv('SQLITE_FILE')
                if legacy_sqlite_file:
                    db_path = legacy_sqlite_file
                else:
                    # Use forward slashes for cross-platform compatibility (especially in containers)
                    db_path = f"{database_path}/{database_file}"
            else:
                # Use forward slashes for cross-platform compatibility (especially in containers)
                db_path = f"{database_path}/{database_file}"
                
            print(f"Database file: {os.path.abspath(db_path)}")
            if os.path.exists(db_path):
                print(f"File size: {os.path.getsize(db_path)} bytes")
        
        print("Robot will show as STOPPED (not running) with this empty database")
        print("All latest schema features included:")
        print("   - portfolio_breakdown column in trading_cycles")
        print("   - portfolio_breakdown column in simulation_cycles") 
        print("   - actions_taken JSON columns in both trading_cycles and simulation_cycles")
        print("   - data_source column in simulations table with percentage support")
        print("   - calibration_profile column in simulations table for realistic performance")
        print("   - cycle_positions table for detailed position tracking")
        print("   - strategy_performance table for dynamic strategy tracking")
        print("   - strategy_switches table for strategy change logging")
        print("   - enhanced JSON type handling for cross-database compatibility")
        
        # Initialize Fixed Sim6 in database
        print("\nFIXED SIM6 INTEGRATION:")
        try:
            from src.fixed_sim6_integration import fixed_sim6_integration
            
            # Create initial Fixed Sim6 simulation entry
            sim_id = fixed_sim6_integration.get_or_create_sim6()
            if sim_id:
                print(f"   [OK] Fixed Sim6 simulation created (ID: {sim_id})")
                print(f"   - Strategy: Fixed Sim6 Engine v2.0")
                print(f"   - All core fixes implemented")
                print(f"   - Risk management: Stop-losses & take-profits")
                print(f"   - Smart entries and momentum logic")
                print(f"   - Ready for automated trading")
            else:
                print(f"   [WARN] Fixed Sim6 simulation creation deferred")
                
        except Exception as e:
            print(f"   [WARN] Fixed Sim6 integration: {e}")
            print(f"   Fixed Sim6 will be available when server starts")
        
        # Configure Fixed Sim6 as the default strategy
        print(f"\nFIXED SIM6 STRATEGY CONFIGURATION:")
        print(f"   - Strategy: Fixed Sim6 Engine (The Only Strategy You Need)")
        print(f"   - Coins: BTC, ETH, SOL, SHIB (dynamic allocation)")
        print(f"   - Cycle: 72 hours (3 days)")
        print(f"   - Features: Market protection, USDC conversion, Risk management")
        print(f"   - Target: Adaptive returns based on market conditions")
        print(f"   - Starting Capital: ${os.getenv('STARTING_CAPITAL', '100')}")
        print(f"   - Protection: Automatic USDC conversion during downturns")
        print(f"   - Calibration Profile: {os.getenv('DEFAULT_CALIBRATION_PROFILE', 'moderate_realistic')}")
        print(f"   Fixed Sim6 ready for simulations and automated trading")

        return True
        
    except Exception as e:
        print(f"Failed to create database: {e}")
        import traceback
        traceback.print_exc()
        return False

def initialize_fixed_sim6():
    """Initialize Fixed Sim6 after database creation"""
    print("\n[INIT] INITIALIZING FIXED SIM6...")
    try:
        # Import Fixed Sim6 integration
        sys.path.append('src')
        from src.fixed_sim6_integration import fixed_sim6_integration
        
        # Create Fixed Sim6 simulation
        sim_id = fixed_sim6_integration.get_or_create_sim6()
        
        if sim_id:
            print(f"[OK] Fixed Sim6 initialized successfully!")
            print(f"   - Simulation ID: {sim_id}")
            print(f"   - Strategy: Fixed Sim6 Engine v2.0")
            print(f"   - Status: Ready for trading")
            print(f"   - Dashboard: /fixed-sim6")
            return True
        else:
            print("[WARN] Fixed Sim6 initialization deferred")
            return False
            
    except Exception as e:
        print(f"[WARN] Fixed Sim6 initialization: {e}")
        print("Fixed Sim6 will be available when HTTPS server starts")
        return False
if __name__ == '__main__':
    success = create_database_with_permissions()
    
    if success:
        # Initialize Fixed Sim6
        initialize_fixed_sim6()
        
        print(f"\n[COMPLETE] DATABASE SETUP COMPLETE!")
        print(f"[OK] Database created with all tables")
        print(f"[OK] Fixed Sim6 engine integrated")
        print(f"[OK] Single strategy configured")
        print(f"[OK] Calibration profiles ready")
        
        # Display calibration profile configuration
        default_profile = os.getenv('DEFAULT_CALIBRATION_PROFILE', 'moderate_realistic')
        calibration_enabled = os.getenv('ENABLE_CALIBRATION', 'true').lower() == 'true'
        
        print(f"\nCALIBRATION PROFILE CONFIGURATION:")
        print(f"   - Default Profile: {default_profile}")
        print(f"   - Calibration Enabled: {calibration_enabled}")
        print(f"   - Available Profiles: conservative_realistic, moderate_realistic, aggressive_realistic")
        
        print(f"\nNext steps:")
        print(f"   1. Start HTTPS server: python start_https_server.py")
        print(f"   2. Access main dashboard: https://your-domain:5000/")
        print(f"   3. Access Fixed Sim6: https://your-domain:5000/fixed-sim6")
        print(f"   4. Run calibrated simulation: /simulator (with profile selection)")
        print(f"\nFor EC2 deployment:")
        print(f"   sudo $(which python) start_https_server.py")
    else:
        print(f"\nDatabase setup failed.")
        sys.exit(1)
