#!/usr/bin/env python3
"""
Update database schema to include simulation tables
"""
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.database import get_db_manager

def update_database_schema():
    """Update database schema with new simulation tables"""
    print("🔄 Updating database schema...")
    
    try:
        # Get database manager
        db_manager = get_db_manager()
        
        # Create all tables (this will add new tables without affecting existing ones)
        db_manager.create_tables()
        
        print("✅ Database schema updated successfully!")
        print(f"📊 Database type: {db_manager.db_type}")
        print(f"🔗 Database info: {db_manager.get_database_info()}")
        
        return True
    
    except Exception as e:
        print(f"❌ Error updating database schema: {e}")
        return False

if __name__ == "__main__":
    success = update_database_schema()
    sys.exit(0 if success else 1)
