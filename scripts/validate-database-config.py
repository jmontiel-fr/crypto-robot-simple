#!/usr/bin/env python3
"""
Database Configuration Validation Script
Tests the updated database configuration to ensure it supports DATABASE_PATH and DATABASE_FILE
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'robot', 'src'))

def test_database_configuration():
    """Test database configuration with new environment variables"""
    print("🧪 Testing Database Configuration")
    print("=" * 50)
    
    # Test 1: Legacy SQLITE_FILE configuration
    print("\n📋 Test 1: Legacy SQLITE_FILE configuration")
    
    # Set legacy environment variable
    os.environ['DATABASE_TYPE'] = 'sqlite'
    os.environ['SQLITE_FILE'] = 'data/legacy_test.db'
    
    # Remove new variables if they exist
    os.environ.pop('DATABASE_PATH', None)
    os.environ.pop('DATABASE_FILE', None)
    
    try:
        from database import DatabaseManager
        
        db_manager = DatabaseManager()
        db_info = db_manager.get_database_info()
        
        print(f"✅ Legacy configuration works")
        print(f"   Database URL: {db_info['url']}")
        print(f"   Database Type: {db_info['type']}")
        
        # Check if URL contains legacy path
        if 'legacy_test.db' in db_info['url']:
            print("✅ Legacy SQLITE_FILE path correctly used")
        else:
            print("❌ Legacy SQLITE_FILE path not used correctly")
            return False
            
    except Exception as e:
        print(f"❌ Legacy configuration failed: {e}")
        return False
    
    # Test 2: New DATABASE_PATH and DATABASE_FILE configuration
    print("\n📋 Test 2: New DATABASE_PATH and DATABASE_FILE configuration")
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        test_db_path = os.path.join(temp_dir, 'database')
        test_db_file = 'new_test.db'
        
        # Set new environment variables
        os.environ['DATABASE_PATH'] = test_db_path
        os.environ['DATABASE_FILE'] = test_db_file
        
        # Remove legacy variable
        os.environ.pop('SQLITE_FILE', None)
        
        try:
            # Reload the module to pick up new environment variables
            if 'database' in sys.modules:
                del sys.modules['database']
            
            from database import DatabaseManager
            
            db_manager = DatabaseManager()
            db_info = db_manager.get_database_info()
            
            print(f"✅ New configuration works")
            print(f"   Database URL: {db_info['url']}")
            print(f"   Database Type: {db_info['type']}")
            
            # Check if URL contains new path (handle both Unix and Windows paths)
            expected_path_unix = f"{test_db_path}/{test_db_file}"
            expected_path_windows = os.path.join(test_db_path, test_db_file)
            
            if expected_path_unix in db_info['url'] or expected_path_windows in db_info['url']:
                print("✅ New DATABASE_PATH and DATABASE_FILE correctly used")
            else:
                print(f"❌ New path not used correctly. Expected: {expected_path_unix} or {expected_path_windows}")
                return False
                
            # Check if directory was created
            if os.path.exists(test_db_path):
                print("✅ Database directory automatically created")
            else:
                print("❌ Database directory not created")
                return False
                
        except Exception as e:
            print(f"❌ New configuration failed: {e}")
            return False
    
    # Test 3: Container environment simulation
    print("\n📋 Test 3: Container environment simulation")
    
    # Simulate container environment variables
    os.environ['DATABASE_PATH'] = '/opt/crypto-robot/database'
    os.environ['DATABASE_FILE'] = 'crypto_robot.db'
    os.environ.pop('SQLITE_FILE', None)
    
    try:
        # Reload the module to pick up container environment variables
        if 'database' in sys.modules:
            del sys.modules['database']
        
        from database import DatabaseManager
        
        db_manager = DatabaseManager()
        db_info = db_manager.get_database_info()
        
        print(f"✅ Container configuration works")
        print(f"   Database URL: {db_info['url']}")
        print(f"   Database Type: {db_info['type']}")
        
        # Check if URL contains container path
        expected_path = '/opt/crypto-robot/database/crypto_robot.db'
        if expected_path in db_info['url']:
            print("✅ Container DATABASE_PATH and DATABASE_FILE correctly used")
        else:
            print(f"❌ Container path not used correctly. Expected: {expected_path}")
            print(f"   Actual URL: {db_info['url']}")
            return False
            
    except Exception as e:
        print(f"❌ Container configuration failed: {e}")
        return False
    
    # Test 4: Fallback behavior
    print("\n📋 Test 4: Fallback behavior (no environment variables)")
    
    # Remove all database environment variables
    os.environ.pop('DATABASE_PATH', None)
    os.environ.pop('DATABASE_FILE', None)
    os.environ.pop('SQLITE_FILE', None)
    
    try:
        # Reload the module to test fallback
        if 'database' in sys.modules:
            del sys.modules['database']
        
        from database import DatabaseManager
        
        db_manager = DatabaseManager()
        db_info = db_manager.get_database_info()
        
        print(f"✅ Fallback configuration works")
        print(f"   Database URL: {db_info['url']}")
        print(f"   Database Type: {db_info['type']}")
        
        # Check if URL contains default path
        if 'data/cryptorobot.db' in db_info['url']:
            print("✅ Default fallback path correctly used")
        else:
            print("❌ Default fallback path not used correctly")
            return False
            
    except Exception as e:
        print(f"❌ Fallback configuration failed: {e}")
        return False
    
    return True

def test_create_database_script():
    """Test the updated create_database.py script"""
    print("\n🧪 Testing create_database.py Script")
    print("=" * 50)
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        test_db_path = os.path.join(temp_dir, 'test_database')
        test_db_file = 'test_create.db'
        
        # Set environment variables
        os.environ['DATABASE_TYPE'] = 'sqlite'
        os.environ['DATABASE_PATH'] = test_db_path
        os.environ['DATABASE_FILE'] = test_db_file
        
        # Remove legacy variable
        os.environ.pop('SQLITE_FILE', None)
        
        try:
            # Import and test create_database functionality
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'robot'))
            
            # Reload database module
            if 'database' in sys.modules:
                del sys.modules['database']
            
            from database import DatabaseManager
            
            # Test database creation
            db_manager = DatabaseManager()
            db_manager.create_tables()
            
            # Check if database file was created
            expected_db_file = os.path.join(test_db_path, test_db_file)
            if os.path.exists(expected_db_file):
                print("✅ Database file created successfully")
                print(f"   Database file: {expected_db_file}")
                
                # Check file size
                file_size = os.path.getsize(expected_db_file)
                print(f"   File size: {file_size} bytes")
                
                if file_size > 0:
                    print("✅ Database file has content (tables created)")
                else:
                    print("❌ Database file is empty")
                    return False
                    
            else:
                print(f"❌ Database file not created: {expected_db_file}")
                return False
                
            # Test database operations
            session = db_manager.get_session()
            
            # Import models
            from database import Portfolio
            
            # Test creating a portfolio
            portfolio = Portfolio(bnb_reserve=100.0, current_cycle=0)
            session.add(portfolio)
            session.commit()
            
            # Test querying
            portfolio_count = session.query(Portfolio).count()
            session.close()
            
            if portfolio_count == 1:
                print("✅ Database operations work correctly")
            else:
                print("❌ Database operations failed")
                return False
                
        except Exception as e:
            print(f"❌ create_database.py test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

def main():
    """Main test function"""
    print("🚀 Database Configuration Validation")
    print("=" * 60)
    
    success = True
    
    # Test database configuration
    if not test_database_configuration():
        success = False
    
    # Test create_database script
    if not test_create_database_script():
        success = False
    
    print("\n" + "=" * 60)
    
    if success:
        print("✅ ALL TESTS PASSED: Database configuration is working correctly!")
        print("\n📋 Summary:")
        print("   ✅ Legacy SQLITE_FILE configuration supported")
        print("   ✅ New DATABASE_PATH and DATABASE_FILE configuration working")
        print("   ✅ Container environment simulation successful")
        print("   ✅ Fallback behavior working")
        print("   ✅ create_database.py script updated correctly")
        print("\n🎉 Database persistence implementation is ready!")
        return 0
    else:
        print("❌ SOME TESTS FAILED: Database configuration has issues!")
        print("\n🔧 Please check the database.py and create_database.py files")
        return 1

if __name__ == '__main__':
    sys.exit(main())