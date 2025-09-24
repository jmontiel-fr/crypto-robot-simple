#!/usr/bin/env python3
"""
Crypto Robot - Main Application Entry Point
Supports multiple modes: robot trading, web interface, simulation
"""

import os
import sys
import argparse
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / 'src'))

def run_robot_mode(initial_reserve=None):
    """Run the crypto robot in trading mode - supports multiple strategies"""
    print("🤖 Starting Multi-Strategy Crypto Robot")
    
    # Get strategy from environment or default
    strategy_name = os.getenv('ROBOT_STRATEGY', 'daily_rebalance')
    
    try:
        # Import multi-strategy robot
        from src.multi_strategy_robot import MultiStrategyRobot
        
        # Create robot with selected strategy
        robot = MultiStrategyRobot(strategy_name)
        
        # Show strategy info
        status = robot.get_status()
        strategy_info = status['strategy_info']
        
        print(f"🎯 Strategy: {strategy_info['name']}")
        print(f"📊 Risk Level: {strategy_info['risk_level']}")
        print(f"⏰ Cycle Frequency: {strategy_info['cycle_frequency']}")
        print(f"💰 Expected Return: {strategy_info['expected_return']}")
        print(f"📝 Description: {strategy_info['description']}")
        
        if initial_reserve:
            print(f"💰 Starting capital: {initial_reserve} BNB")
        
        print("🚀 Multi-strategy robot initialized successfully!")
        
        # Start automated trading
        robot.start_automated_trading()
        
    except KeyboardInterrupt:
        print("\n🛑 Robot stopped by user")
    except Exception as e:
        print(f"❌ Error running robot: {e}")
        # Fallback to old robot system
        print("⚠️  Using legacy robot system - consider switching to single_strategy")
        try:
            from crypto_robot import CryptoRobot
            
            robot = CryptoRobot()
            
            if initial_reserve:
                print(f"💰 Setting initial reserve: {initial_reserve}")
            
            print("🚀 Robot started successfully!")
            robot.run()
        except Exception as fallback_error:
            print(f"❌ Fallback robot also failed: {fallback_error}")
            sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n🛑 Robot stopped by user")
    except Exception as e:
        print(f"❌ Error running robot: {e}")
        sys.exit(1)

def run_web_mode(port=None, host=None):
    """Run the web interface with dynamic configuration from .env"""
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Get configuration from .env with fallbacks to parameters or defaults
    # Command line parameters override .env values for direct execution
    flask_port = port if port is not None else int(os.getenv('FLASK_PORT', 5000))
    flask_host = host if host is not None else os.getenv('FLASK_HOST', '127.0.0.1')
    flask_protocol = os.getenv('FLASK_PROTOCOL', 'http')
    use_https = os.getenv('USE_HTTPS', 'false').lower() == 'true'
    
    print(f"🌐 Starting Crypto Robot - Web Interface Mode")
    print(f"📡 Server: {flask_host}:{flask_port}")
    print(f"🔒 Protocol: {flask_protocol.upper()}")
    
    try:
        from web_app import app, socketio
        
        # Configure Flask app with .env values
        app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        
        print(f"🔄 Real-time updates: Enabled (Flask-SocketIO)")
        
        if use_https and flask_protocol == 'https':
            # Use HTTPS configuration
            import ssl
            ssl_cert_path = os.getenv('SSL_CERT_PATH', 'certs/cert.pem')
            ssl_key_path = os.getenv('SSL_KEY_PATH', 'certs/key.pem')
            
            print(f"🌍 Access URL: https://{flask_host}:{flask_port}")
            print(f"🔒 SSL Certificate: {ssl_cert_path}")
            
            # Create SSL context
            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
            context.load_cert_chain(ssl_cert_path, ssl_key_path)
            
            # Run with HTTPS
            socketio.run(app, host=flask_host, port=flask_port, 
                        debug=app.config['DEBUG'], ssl_context=context)
        else:
            print(f"🌍 Access URL: http://{flask_host}:{flask_port}")
            
            # Run with HTTP
            socketio.run(app, host=flask_host, port=flask_port, debug=app.config['DEBUG'])
        
    except KeyboardInterrupt:
        print("\n🛑 Web server stopped by user")
    except Exception as e:
        print(f"❌ Error running web server: {e}")
        sys.exit(1)

def run_simulation_mode(name, days=21, reserve=100):
    """Run a single simulation"""
    print(f"🧪 Starting Crypto Robot - Simulation Mode")
    print(f"📊 Simulation: {name}")
    print(f"⏱️  Duration: {days} days")
    print(f"💰 Reserve: {reserve}")
    
    try:
        from enhanced_simulation_engine import EnhancedSimulationEngine
        from datetime import datetime, timedelta
        from src.daily_rebalance_simulation_engine import DailyRebalanceSimulationEngine
        
        engine = DailyRebalanceSimulationEngine()
        
        # Run simulation starting 30 days ago
        start_date = datetime.now() - timedelta(days=30)
        
        result = engine.run_simulation(
            start_date=start_date,
            duration_days=days,
            cycle_length_minutes=int(os.getenv('CYCLE_DURATION', '1440')),
            starting_reserve=reserve
        )
        
        print(f"✅ Simulation completed!")
        print(f"📈 Final Total: {result.get('final_total_value', 0):.2f}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error running simulation: {e}")
        sys.exit(1)

def check_dependencies():
    """Check if required dependencies are installed"""
    required_imports = {
        'flask': 'flask',
        'flask-socketio': 'flask_socketio',
        'requests': 'requests', 
        'python-dotenv': 'dotenv',
        'sqlite3': 'sqlite3',
        'datetime': 'datetime',
        'json': 'json',
        'os': 'os',
        'sys': 'sys'
    }
    
    missing = []
    for package_name, import_name in required_imports.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(package_name)
    
    if missing:
        print(f"❌ Missing required modules: {', '.join(missing)}")
        print("💡 Install with: pip install -r requirements.txt")
        return False
    
    return True

def run_live_trading_mode(starting_capital=None):
    """Run live trading mode with real money"""
    print("🚨 LIVE TRADING MODE - REAL MONEY AT RISK")
    print("⚠️  WARNING: This will execute real trades on Binance")
    
    # Safety confirmation
    confirmation = input("\nType 'I UNDERSTAND THE RISKS' to continue: ")
    if confirmation != "I UNDERSTAND THE RISKS":
        print("❌ Live trading cancelled for safety")
        return
    
    try:
        from src.real_trading_robot import create_live_trading_robot
        
        # Override starting capital if provided
        if starting_capital:
            os.environ['STARTING_CAPITAL'] = str(starting_capital)
        
        # Create live trading robot
        robot = create_live_trading_robot()
        
        print(f"💰 Starting capital: {robot.starting_capital} USDT")
        print("🚀 Starting LIVE Trading with Volatility Optimization...")
        print(f"🎯 Strategy: {robot.engine.strategy.strategy_name} v{robot.engine.strategy.strategy_version}")
        print(f"📊 Volatility Mode: {robot.engine.strategy.volatility_mode}")
        print(f"⏰ Cycle Frequency: {robot.cycle_hours} hours")
        
        # Start automated trading
        robot.run_automated_trading()
        
    except KeyboardInterrupt:
        print("\n🛑 Live trading stopped by user")
    except Exception as e:
        print(f"❌ Error in live trading: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def run_single_strategy_mode(starting_capital=None):
    """Run the single strategy directly using unified engine"""
    print("🎯 Starting Single Strategy Mode (Unified Engine)")
    
    try:
        from src.real_trading_robot import create_real_trading_robot
        
        # Override starting capital if provided
        if starting_capital:
            os.environ['STARTING_CAPITAL'] = str(starting_capital)
        
        # Create robot in dry run mode
        robot = create_real_trading_robot(dry_run=True)
        
        print(f"💰 Starting capital: {robot.starting_capital} USDT")
        print("🚀 Running Daily Rebalance Strategy with Volatility Optimization...")
        print(f"🎯 Strategy: {robot.engine.strategy.strategy_name} v{robot.engine.strategy.strategy_version}")
        print(f"📊 Volatility Mode: {robot.engine.strategy.volatility_mode}")
        
        # Execute a single trading cycle
        result = robot.run_single_cycle()
        
        if result and result.success:
            print("✅ Trading cycle completed successfully")
            print(f"📈 Performance: {result.total_return:.2f}% return")
            print(f"💰 Final Capital: ${result.ending_capital:.2f}")
        else:
            error_msg = result.error_message if result else "Unknown error"
            print(f"❌ Trading cycle failed: {error_msg}")
        
        print(f"\n✅ Single strategy execution complete!")
        print(f"⏰ Next cycle in {robot.cycle_hours} hours")
        print(f"🔄 Use --mode auto for continuous trading")
        
    except KeyboardInterrupt:
        print("\n🛑 Single strategy stopped by user")
    except Exception as e:
        print(f"❌ Error running single strategy: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(description='Crypto Robot - Multi-mode Application')
    parser.add_argument('--mode', choices=['robot', 'web', 'simulation', 'single', 'live'], 
                       default='web', help='Application mode (default: web)')
    parser.add_argument('--port', type=int, default=5000, 
                       help='Port for web mode (default: 5000)')
    parser.add_argument('--host', default='127.0.0.1', 
                       help='Host for web mode (default: 127.0.0.1)')
    parser.add_argument('--initial-reserve', type=float, 
                       help='Initial reserve for robot mode')
    parser.add_argument('--starting-capital', type=float,
                       help='Starting capital for single strategy mode')
    parser.add_argument('--simulation-name', default='CLI Simulation',
                       help='Name for simulation mode')
    parser.add_argument('--simulation-days', type=int, default=21,
                       help='Duration for simulation mode (default: 21)')
    parser.add_argument('--simulation-reserve', type=float, default=100,
                       help='Reserve for simulation mode (default: 100)')
    
    args = parser.parse_args()
    
    print("🤖 Crypto Robot - Main Application")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run in specified mode
    try:
        if args.mode == 'robot':
            run_robot_mode(args.initial_reserve)
        elif args.mode == 'web':
            run_web_mode(args.port, args.host)
        elif args.mode == 'simulation':
            run_simulation_mode(
                args.simulation_name, 
                args.simulation_days, 
                args.simulation_reserve
            )
        elif args.mode == 'single':
            run_single_strategy_mode(args.starting_capital)
        elif args.mode == 'live':
            run_live_trading_mode(args.starting_capital)
    except Exception as e:
        print(f"❌ Application error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()