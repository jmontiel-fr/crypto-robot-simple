#!/usr/bin/env python3
"""
Quick setup script for the crypto trading robot
Automatically configures SQLite database (default) and creates sample data
"""
import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and print its description"""
    print(f"📋 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout.strip():
            # Only show relevant output
            output_lines = result.stdout.strip().split('\n')
            for line in output_lines[-3:]:  # Show last 3 lines
                if line.strip():
                    print(f"   {line.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stderr:
            print(f"   Error: {e.stderr.strip()}")
        return False

def create_directories():
    """Create necessary directories"""
    directories = ['data', 'logs', 'static', 'templates']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    print("✅ Created project directories")

def main():
    print("Crypto Trading Robot - Quick Setup with SQLite")
    print("==================================================")
    print("This script will set up the robot with SQLite database (default)")
    print("No additional database server installation required!")
    print()
    
    # Check if we're in the right directory
    if not os.path.exists('src/database.py'):
        print("❌ Please run this script from the crypto robot project directory")
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    steps = [
        ("python -m pip install -r requirements.txt", "Installing Python dependencies"),
        ("python db_config.py init", "Initializing SQLite database (default)"),
        ("python create_mock_data.py", "Creating sample trading data"),
    ]
    
    success_count = 0
    for command, description in steps:
        if run_command(command, description):
            success_count += 1
        print()
    
    print("🎯 Setup Summary")
    print("================")
    print(f"✅ {success_count}/{len(steps)} steps completed successfully")
    
    if success_count == len(steps):
        print()
        print("🎉 Setup completed successfully!")
        print()
        print("Ready to start! Next steps:")
        print("  1. Start the web interface:")
        print("     python src/web_app.py")
        print()
        print("  2. Open your browser to:")
        print("     http://localhost:5000")
        print()
        print("  3. Navigate to 'Combined View' to see:")
        print("     📈 Portfolio value (blue line)")
        print("     💰 Reserve value (red line)")
        print("     📊 Per cycle iteration")
        print()
        print("💡 Database info:")
        run_command("python db_config.py info", "Current database configuration")
        print()
        print("📚 For advanced database configuration, see DATABASE_CONFIG.md")
    else:
        print()
        print("⚠️  Some steps failed. Please check the errors above and try again.")
        print("   You can also run individual commands manually.")

if __name__ == '__main__':
    main()
    required_packages = [
        ('binance', 'python-binance'),
        ('pandas', 'pandas'),
        ('plotly', 'plotly'),
        ('flask', 'flask'),
        ('dotenv', 'python-dotenv'),
        ('schedule', 'schedule'),
        ('requests', 'requests')
    ]
    
    failed_imports = []
    
    for package, pip_name in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} imported successfully")
        except ImportError:
            failed_imports.append(pip_name)
            print(f"❌ Failed to import {package}")
    
    if failed_imports:
        print(f"\nMissing packages: {', '.join(failed_imports)}")
        print("Install them with: pip install " + " ".join(failed_imports))
        return False
    
    return True

def main():
    print("🤖 Crypto Trading Robot Setup")
    print("=" * 40)
    
    # Create directories
    print("\n📁 Creating directories...")
    create_directories()
    
    # Test imports
    print("\n📦 Testing package imports...")
    imports_ok = test_imports()
    
    # Check environment file
    print("\n⚙️  Checking configuration...")
    env_ok = check_env_file()
    
    print("\n" + "=" * 40)
    
    if imports_ok and env_ok:
        print("✅ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Configure your Binance API credentials in .env")
        print("2. Run: python main.py --mode both --initial-reserve 100.0")
        print("3. Access web interface at http://localhost:5000")
    else:
        print("❌ Setup incomplete. Please fix the issues above.")
        sys.exit(1)

if __name__ == '__main__':
    main()
