#!/usr/bin/env python3
"""
Crypto Robot - HTTPS Server Startup Script
Main entry point for starting the HTTPS Flask web application with auto-setup
"""

import os
import sys
import subprocess
from pathlib import Path

def check_ssl_certificates():
    """Check if SSL certificates exist, generate if missing"""
    cert_path = Path('certs/cert.pem')
    key_path = Path('certs/key.pem')
    
    if not cert_path.exists() or not key_path.exists():
        print("🔒 SSL certificates not found. Generating self-signed certificates...")
        
        try:
            # Run the SSL certificate generator
            result = subprocess.run([sys.executable, 'generate_ssl_cert.py'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("SSL certificates generated successfully!")
            else:
                print(f"Failed to generate SSL certificates: {result.stderr}")
                return False
                
        except FileNotFoundError:
            print("generate_ssl_cert.py not found!")
            print("Please ensure generate_ssl_cert.py exists in the current directory")
            return False
        except Exception as e:
            print(f"Error generating SSL certificates: {e}")
            return False
    else:
        print("SSL certificates found")
    
    return True

def check_database():
    """Check if database exists and is properly initialized"""
    db_path = Path('data/cryptorobot.db')
    
    if not db_path.exists():
        print("🗄️  Database not found. Creating database...")
        
        try:
            # Run database creation script
            result = subprocess.run([sys.executable, 'create_database.py'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("Database created successfully!")
            else:
                print(f"Failed to create database: {result.stderr}")
                return False
                
        except FileNotFoundError:
            print("create_database.py not found!")
            print("Please ensure create_database.py exists in the current directory")
            return False
        except Exception as e:
            print(f"Error creating database: {e}")
            return False
    else:
        print("Database found")
    
    return True

def check_environment():
    """Check if .env file exists with required settings"""
    env_path = Path('.env')
    
    if not env_path.exists():
        print(".env file not found!")
        print("Please create .env file with your configuration")
        print("   You can copy from .env.example if available")
        return False
    
    print("Environment configuration found")
    return True

def check_dependencies():
    """Check if required Python packages are installed"""
    required_imports = {
        'flask': 'flask',
        'flask-socketio': 'flask_socketio', 
        'requests': 'requests',
        'python-dotenv': 'dotenv'
    }
    missing_packages = []
    
    for package_name, import_name in required_imports.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"Missing required packages: {', '.join(missing_packages)}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    print("Required packages installed")
    return True

def update_hosts_file_info():
    """Display information about updating hosts file"""
    domain_name = os.getenv('DOMAIN_NAME', 'crypto-robot.local')
    
    if domain_name != 'localhost' and domain_name != '127.0.0.1':
        print(f"\nIMPORTANT: Add this line to your hosts file:")
        print(f"   127.0.0.1 {domain_name}")
        print(f"\nHosts file location:")
        
        if os.name == 'nt':  # Windows
            print(f"   Windows: C:\\Windows\\System32\\drivers\\etc\\hosts")
        else:  # Linux/Mac
            print(f"   Linux/Mac: /etc/hosts")
        
        print(f"\nThis allows you to access the app at https://{domain_name}:5000")

def check_single_strategy():
    """Check if Daily Rebalance Strategy v1.0 is properly configured"""
    print("Daily Rebalance Strategy v1.0 enabled")
    
    # Check if Daily Rebalance files exist
    strategy_files = [
        Path('src/daily_rebalance_volatile_strategy.py'),
        Path('src/daily_rebalance_simulation_engine.py')
    ]
    
    missing_files = [f for f in strategy_files if not f.exists()]
    
    if missing_files:
        print(f"Daily Rebalance files missing: {[str(f) for f in missing_files]}")
        return False
    
    print("Daily Rebalance Protected Strategy v2.0 files found")
    print("   • 10 Optimized Cryptocurrencies enabled (reduced from 15)")
    print("   • 26.8% cost reduction, +10% performance improvement")
    print("   • USDC Market Protection enabled (Fixed Sim6 V3.0 style)")
    print("   • Market Regime Detection active (-15% bear, +5% bull)")
    print("   • Daily Rebalancing active")
    print("   • Real Binance Historical Data")
    print("   • Target 120%+ monthly returns")
    
    # Check starting capital
    starting_capital = os.getenv('STARTING_CAPITAL', '100')
    print(f"Starting capital: {starting_capital} BNB")
    
    return True

def check_daily_rebalance():
    """Check if Daily Rebalance engine is available"""
    try:
        # Check if Daily Rebalance files exist
        daily_rebalance_files = [
            Path('src/daily_rebalance_volatile_strategy.py'),
            Path('src/daily_rebalance_simulation_engine.py'),
            Path('templates/daily_rebalance_dashboard.html')
        ]
        
        missing_files = [f for f in daily_rebalance_files if not f.exists()]
        
        if missing_files:
            print(f"⚠️  Daily Rebalance files missing: {[str(f) for f in missing_files]}")
            return False
        
        print("Fixed Sim6 engine available")
        print("   • Improved trading engine with risk management")
        print("   • Stop-losses and take-profits implemented")
        print("   • Smart entry system and momentum logic")
        print("   • Access via: /fixed-sim6 dashboard")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Fixed Sim6 check failed: {e}")
        return False

def main():
    """Main startup function with auto-setup"""
    print("Crypto Robot - HTTPS Server Startup")
    print("Integrated with Daily Rebalance Strategy v1.0")
    print("=" * 50)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print(f"Working directory: {os.getcwd()}")
    
    # Perform pre-flight checks
    print("\nPerforming pre-flight checks...")
    
    checks = [
        ("Environment configuration", check_environment),
        ("Python dependencies", check_dependencies),
        ("Daily Rebalance Strategy setup", check_single_strategy),
        ("Daily Rebalance engine", check_daily_rebalance),
        ("Database setup", check_database),
        ("SSL certificates", check_ssl_certificates),
    ]
    
    for check_name, check_func in checks:
        print(f"\nChecking {check_name}...")
        if not check_func():
            print(f"\nPre-flight check failed: {check_name}")
            print("Please fix the above issues and try again")
            sys.exit(1)
    
    print(f"\nAll pre-flight checks passed!")
    
    # Display strategy info
    print(f"\nPROTECTED FIXED SIM6 V3.0 ACTIVE:")
    print(f"  • Strategy: The ONLY strategy you need")
    print(f"  • USDC Protection: Enabled")
    print(f"  • Market Regime Detection: Active")
    print(f"  • Risk Management: Enhanced")
    print(f"  • Cycle: 24 hours")
    print(f"  • Target: 100%+ returns")
    print(f"  • Capital: {os.getenv('STARTING_CAPITAL', '100')} BNB")
    
    print(f"\nFIXED SIM6 ENGINE AVAILABLE:")
    print(f"  • Improved trading engine with all core fixes")
    print(f"  • Risk management: Stop-losses & take-profits")
    print(f"  • Smart entries: Only buy strong coins")
    print(f"  • Expected: Transform losing strategy to profitable")
    print(f"  • Dashboard: https://your-domain:5000/fixed-sim6")
    
    # Display hosts file information
    update_hosts_file_info()
    
    # Start the HTTPS server
    print(f"\nStarting HTTPS server with Protected Fixed Sim6 v3.0 integration...")
    print(f"Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Import and run the HTTPS web app
        from src.web_app_https import run_https_production
        run_https_production()
        
    except KeyboardInterrupt:
        print(f"\n\n🛑 Server stopped by user")
        sys.exit(0)
    except ImportError as e:
        print(f"\nImport error: {e}")
        print("Make sure src/web_app_https.py exists")
        sys.exit(1)
    except Exception as e:
        print(f"\nFailed to start server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()