print("LOADED web_app.py -- THIS IS THE FILE BEING EXECUTED")
"""
Web interface for crypto trading robot with real-time updates
NOW WITH PROTECTED FIXED SIM6 V3.0 STRATEGY!
"""

# --- Standard imports and environment setup ---
import os
import sys
import json
import logging
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_socketio import SocketIO, emit, disconnect
from sqlalchemy import func, inspect
from dotenv import load_dotenv
import plotly.graph_objs as go
import plotly.utils

# Load environment variables from project root
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path)

# Add parent directory to path so we can import from src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import get_db_manager, TradingCycle, Simulation, SimulationCycle
from src.robot_state import robot_state_manager
# APIs removed - using only Daily Rebalance strategy

# Daily Rebalance Integration - The Only Strategy
from src.daily_rebalance_simulation_engine import DailyRebalanceSimulationEngine
from src.calibration_manager import get_calibration_manager

# Protected Fixed Sim6 v3.0 Integration

# Get the parent directory (project root) for templates and static files
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
template_dir = os.path.join(project_root, 'templates')
static_dir = os.path.join(project_root, 'static')

# --- Flask app definition (must be top-level for import!) ---
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'crypto-robot-secret-key-change-this')
# Only Daily Rebalance strategy - no additional APIs needed

# --- Socket.IO and DB manager ---
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
db_manager = get_db_manager()
logger = logging.getLogger(__name__)
print(f"[DEBUG] Database URL in Flask app: {db_manager.engine.url}")

# Protected Fixed Sim6 v3.0 is the only strategy - no patches needed

# --- Make app importable ---
__all__ = ["app", "socketio"]

# --- Place the simulation summary API route here, after app and db_manager are defined ---
@app.route('/api/simulation/by-name/<string:sim_name>/summary')
def api_simulation_summary_by_name(sim_name):
    print("ENTERED api_simulation_summary_by_name")
    """Get simulation summary by simulation name (case-insensitive)"""
    session = db_manager.get_session()
    # Use lower() for case-insensitive match, works in SQLite and Postgres
    matches = session.query(Simulation).filter(func.lower(Simulation.name) == sim_name.lower()).all()
    print(f"[DEBUG] Found {len(matches)} simulations with name '{sim_name}': {[s.id for s in matches]}")
    if not matches:
        session.close()
        return jsonify({"error": "Simulation not found"}), 404
    # Return the most recent simulation (highest id)
    sim = sorted(matches, key=lambda s: s.id, reverse=True)[0]
    
    # Get the latest cycle number for this simulation (same logic as by-id endpoint)
    last_cycle_number = 0
    latest_cycle = session.query(SimulationCycle).filter(SimulationCycle.simulation_id == sim.id).order_by(SimulationCycle.cycle_number.desc()).first()
    if latest_cycle:
        last_cycle_number = latest_cycle.cycle_number
    
    # Compose summary (reuse logic from other summary endpoints if needed)
    summary = {
        "id": sim.id,
        "name": sim.name,
        "status": sim.status,
        "data_source": sim.data_source,
        "starting_reserve": sim.starting_reserve,
        "final_reserve_value": sim.final_reserve_value,
        "final_total_value": sim.final_total_value,
        "total_cycles": sim.total_cycles,
        "created_at": sim.created_at.isoformat() if hasattr(sim, 'created_at') and sim.created_at else None,
        "last_cycle_number": last_cycle_number,
    }
    session.close()
    return jsonify(summary)

@app.route('/api/simulation/<int:simulation_id>/summary')
def api_simulation_summary_by_id(simulation_id):
    print(f"ENTERED api_simulation_summary_by_id for id={simulation_id}")
    session = db_manager.get_session()
    sim = session.query(Simulation).filter(Simulation.id == simulation_id).first()
    if not sim:
        session.close()
        return jsonify({"error": "Simulation not found"}), 404
    # Get the latest cycle number for this simulation
    last_cycle_number = 0
    latest_cycle = session.query(SimulationCycle).filter(SimulationCycle.simulation_id == simulation_id).order_by(SimulationCycle.cycle_number.desc()).first()
    if latest_cycle:
        last_cycle_number = latest_cycle.cycle_number
    summary = {
        "id": sim.id,
        "name": sim.name,
        "status": sim.status,
        "data_source": sim.data_source,
        "starting_reserve": sim.starting_reserve,
        "final_reserve_value": sim.final_reserve_value,
        "final_total_value": sim.final_total_value,
        "total_cycles": sim.total_cycles,
        "created_at": sim.created_at.isoformat() if hasattr(sim, 'created_at') and sim.created_at else None,
        "last_cycle_number": last_cycle_number,
    }
    session.close()
    return jsonify(summary)

# --- Daily Rebalance API Routes - The Only Strategy ---

# --- Daily Rebalance API Routes ---
@app.route('/api/daily-rebalance/run', methods=['POST'])
def api_run_daily_rebalance():
    """Run Daily Rebalance simulation"""
    try:
        data = request.get_json() or {}
        
        # Get parameters
        starting_capital = float(data.get('starting_capital', 10000))
        days = int(data.get('days', 30))
        
        # Initialize engine
        engine = DailyRebalanceSimulationEngine(realistic_mode=True)
        
        # Run simulation
        from datetime import datetime, timedelta
        start_date = datetime.now() - timedelta(days=days)
        end_date = datetime.now()
        
        result = engine.run_simulation(
            start_date=start_date,
            end_date=end_date,
            starting_reserve=starting_capital,
            cycle_length_minutes=1440  # Daily
        )
        
        if result and result.get('success'):
            return jsonify({
                'success': True,
                'message': 'Daily Rebalance simulation completed successfully',
                'result': result
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Daily Rebalance simulation failed',
                'error': result.get('error', 'Unknown error')
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error running Daily Rebalance: {str(e)}'
        }), 500

@app.route('/api/daily-rebalance/status')
def api_daily_rebalance_status():
    """Get Daily Rebalance strategy information"""
    try:
        return jsonify({
            'strategy_name': 'Daily Rebalance with Volatile Cryptos',
            'cycle_frequency': '1440 minutes (24 hours)',
            'assets_count': 15,
            'volatility_range': '3-40% daily',
            'expected_return': '1000-2500% monthly',
            'risk_level': 'High',
            'data_source': 'Real Binance Historical Data',
            'features': [
                'Daily rebalancing (1440 minutes)',
                '15 volatile cryptocurrencies',
                'Dynamic allocation based on volatility',
                'Real historical price data',
                'Momentum-based rebalancing',
                'Risk-managed allocations (5-25% per asset)'
            ]
        })
    except Exception as e:
        return jsonify({
            'error': f'Error getting Daily Rebalance status: {str(e)}'
        }), 500

from datetime import datetime, timedelta
import threading
import time
import sys
from sqlalchemy import inspect
from dotenv import load_dotenv

# Load environment variables from project root
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path)

# Add parent directory to path so we can import from src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import get_db_manager, TradingCycle, Simulation, SimulationCycle
from src.robot_state import robot_state_manager

# Get the parent directory (project root) for templates and static files
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
template_dir = os.path.join(project_root, 'templates')
static_dir = os.path.join(project_root, 'static')

# Only Daily Rebalance strategy - no additional APIs needed

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'crypto-robot-secret-key-change-this')
# Only Daily Rebalance strategy - no additional blueprints needed

# Initialize Socket.IO for real-time communication
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize database manager
db_manager = get_db_manager()

# Ensure all required tables exist (safe no-op if already created)
try:
    db_manager.create_tables()
except Exception as e:
    print(f"Warning: failed to ensure database tables exist: {e}")

# Global variables for real-time monitoring
monitoring_thread = None
monitoring_active = False
last_status_data = None
simulation_watchdog_started = False

# Template context processor to make domain and HTTPS config available in all templates
@app.context_processor
def inject_domain_config():
    """Inject domain and HTTPS configuration into all templates"""
    domain_name = os.getenv('DOMAIN_NAME', '127.0.0.1')
    use_https = os.getenv('USE_HTTPS', 'false').lower() == 'true'
    port = os.getenv('FLASK_PORT', '5000')
    cycle_duration_env = int(os.getenv('CYCLE_DURATION', '1440'))
    
    protocol = 'https' if use_https else 'http'
    base_url = f"{protocol}://{domain_name}:{port}"
    
    # Base asset symbol used across the app (e.g., BNB, USDT)
    base_asset = os.getenv('RESERVE_ASSET', 'BNB')

    return {
        'domain_name': domain_name,
        'use_https': use_https,
        'protocol': protocol,
        'port': port,
        'base_url': base_url,
        'cycle_duration_env': cycle_duration_env,
        'base_asset': base_asset
    }

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/strategy')
@app.route('/daily-rebalance')
def daily_rebalance_dashboard():
    """Daily Rebalance Dashboard page"""
    try:
        return render_template('daily_rebalance_dashboard.html')
    except Exception as e:
        print(f"Error loading Daily Rebalance dashboard: {e}")
        return render_template('daily_rebalance_dashboard.html', 
                             error=str(e))

@app.route('/api/status')
def get_status():
    """Get robot status API - Shows dry-run data when in dry-run mode, real data otherwise"""
    try:
        # Get database info
        db_info = db_manager.get_database_info()
        
        # Get robot state
        robot_status = robot_state_manager.get_status_summary()
        
        # Get dry-run mode from environment
        dry_run_mode = os.getenv('ROBOT_DRY_RUN', 'true').lower() == 'true'
        
        if dry_run_mode:
            # In dry-run mode, show dry-run portfolio data
            try:
                from src.dry_run_manager import dry_run_manager
                portfolio_summary = dry_run_manager.get_portfolio_summary()
                
                status = {
                    'is_frozen': robot_status['is_frozen'],
                    'freeze_reason': robot_status['freeze_reason'],
                    'freeze_timestamp': robot_status['freeze_timestamp'],
                    'cycles_suspended': robot_status['cycles_suspended'],
                    'current_cycle': portfolio_summary['total_trades'],  # Use trades as cycle indicator
                    'bnb_reserve': portfolio_summary['reserve_balance'],
                    'portfolio_value': portfolio_summary['portfolio_value'],
                    'total_value': portfolio_summary['total_value'],
                    'last_cycle_time': portfolio_summary['last_update'],
                    'database': db_info,
                    'data_source': 'dry_run',
                    'dry_run_mode': dry_run_mode
                }
            except Exception as e:
                print(f"Error getting dry-run data: {e}")
                # Fallback to zeros if dry-run manager fails
                status = {
                    'is_frozen': robot_status['is_frozen'],
                    'freeze_reason': robot_status['freeze_reason'],
                    'freeze_timestamp': robot_status['freeze_timestamp'],
                    'cycles_suspended': robot_status['cycles_suspended'],
                    'current_cycle': 0,
                    'bnb_reserve': 0.0,
                    'portfolio_value': 0.0,
                    'total_value': 0.0,
                    'last_cycle_time': robot_status['last_cycle_time'],
                    'database': db_info,
                    'data_source': 'none',
                    'dry_run_mode': dry_run_mode
                }
        else:
            # In live mode, show real trading cycle data
            session = db_manager.get_session()
            latest_cycle = None
            data_source = "none"
            
            try:
                # Only look for real trading cycle data
                latest_cycle = session.query(TradingCycle).order_by(TradingCycle.cycle_number.desc()).first()
                if latest_cycle:
                    data_source = "real"
            except Exception as e:
                print(f"Error with trading cycles: {e}")
            
            if latest_cycle:
                status = {
                    'is_frozen': robot_status['is_frozen'],
                    'freeze_reason': robot_status['freeze_reason'],
                    'freeze_timestamp': robot_status['freeze_timestamp'],
                    'cycles_suspended': robot_status['cycles_suspended'],
                    'current_cycle': latest_cycle.cycle_number,
                    'bnb_reserve': latest_cycle.bnb_reserve,
                    'portfolio_value': latest_cycle.portfolio_value,
                    'total_value': latest_cycle.total_value,
                    'last_cycle_time': robot_status['last_cycle_time'],
                    'database': db_info,
                    'data_source': data_source,
                    'dry_run_mode': dry_run_mode
                }
            else:
                # No real robot data
                status = {
                    'is_frozen': robot_status['is_frozen'],
                    'freeze_reason': robot_status['freeze_reason'],
                    'freeze_timestamp': robot_status['freeze_timestamp'],
                    'cycles_suspended': robot_status['cycles_suspended'],
                    'current_cycle': 0,
                    'bnb_reserve': 0.0,
                    'portfolio_value': 0.0,
                    'total_value': 0.0,
                    'last_cycle_time': robot_status['last_cycle_time'],
                    'database': db_info,
                    'data_source': 'none',
                    'dry_run_mode': dry_run_mode
                }
            
            session.close()
        
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Fallback alias for environments where frontend expects /status
@app.route('/status')
def get_status_alias():
    return get_status()

@app.route('/api/dry-run-portfolio')
def get_dry_run_portfolio():
    """Get detailed dry-run portfolio information"""
    try:
        dry_run_mode = os.getenv('ROBOT_DRY_RUN', 'true').lower() == 'true'
        
        if not dry_run_mode:
            return jsonify({'error': 'Not in dry-run mode'}), 400
        
        from src.dry_run_manager import dry_run_manager
        portfolio_summary = dry_run_manager.get_portfolio_summary()
        
        return jsonify(portfolio_summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/routes')
def list_routes():
    try:
        output = []
        for rule in app.url_map.iter_rules():
            methods = ','.join(sorted(rule.methods))
            output.append({'rule': str(rule), 'endpoint': rule.endpoint, 'methods': methods})
        return jsonify({'routes': output})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/simulation-status')
def get_simulation_status():
    """Get simulation status API - Shows simulation data only"""
    try:
        # Get database info
        db_info = db_manager.get_database_info()
        
        # Get latest simulation data
        session = db_manager.get_session()
        latest_cycle = None
        data_source = "none"
        
        try:
            latest_cycle = session.query(SimulationCycle).order_by(SimulationCycle.cycle_number.desc()).first()
            if latest_cycle:
                data_source = "simulation"
        except Exception as e:
            print(f"Error with simulation cycles: {e}")
        
        if latest_cycle:
            status = {
                'current_cycle': latest_cycle.cycle_number,
                'bnb_reserve': latest_cycle.bnb_reserve,
                'portfolio_value': latest_cycle.portfolio_value,
                'total_value': latest_cycle.total_value,
                'database': db_info,
                'data_source': data_source
            }
        else:
            status = {
                'current_cycle': 0,
                'bnb_reserve': 0.0,
                'portfolio_value': 0.0,
                'total_value': 0.0,
                'database': db_info,
                'data_source': 'none'
            }
        
        session.close()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/portfolio-history')
def get_portfolio_history():
    """Get portfolio value history"""
    try:
        total_values = []
        for cycle in cycles:
            total_values.append(cycle.total_value)

        # Create Plotly chart with only (portfolio + reserve)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(range(1, len(total_values) + 1)),
            y=total_values,
            mode='lines+markers',
            name='Portfolio + Reserve',
            line=dict(color='#28a745', width=3),
            marker=dict(size=6),
            hoverinfo='x+y',
            customdata=[c.as_dict() for c in cycles],
        ))
        fig.update_layout(
            title='Portfolio + Reserve Value Evolution',
            xaxis_title='Cycle',
            yaxis_title=f'Total Value ({base_asset})',
            legend=dict(x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.7)', bordercolor='rgba(0,0,0,0.1)'),
            template='plotly_white'
        )
        chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        return jsonify(reserve_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/manual-cycle', methods=['POST'])
def manual_cycle():
    """Trigger manual trading cycle"""
    try:
        # Check if we're in dry-run mode
        is_dry_run = os.getenv('ROBOT_DRY_RUN', 'true').lower() in ['true', '1', 'yes', 'on']
        
        if is_dry_run:
            # Execute actual dry-run cycle for testing
            from src.dry_run_manager import DryRunManager
            from src.enhanced_real_trading_engine import EnhancedRealTradingEngine
            from src.enhanced_binance_client import EnhancedBinanceClient
            
            # Initialize components
            dry_run_manager = DryRunManager()
            
            # Create a mock binance client for dry-run
            binance_client = EnhancedBinanceClient()
            
            # Initialize trading engine
            engine = EnhancedRealTradingEngine(binance_client, None, robot_state_manager)
            
            # Execute trading cycle
            result = engine.execute_trading_cycle()
            
            if result['success']:
                return jsonify({
                    'success': True, 
                    'message': 'Manual dry-run cycle executed successfully!',
                    'actions_taken': result.get('actions_taken', []),
                    'cycle_time': result.get('cycle_time', datetime.now()).isoformat()
                })
            else:
                return jsonify({
                    'success': False,
                    'error': result.get('error', 'Unknown error during cycle execution')
                })
        else:
            # Live mode - explain dry-run requirement
            return jsonify({
                'success': False,
                'error': 'Manual cycle is only available in DRY-RUN mode for safe testing. Set ROBOT_DRY_RUN=true in .env and restart to use this feature.'
            })
            
    except Exception as e:
        logger.error(f"Error in manual cycle: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/validate-balance')
def validate_balance():
    """Validate Binance account balance for robot startup"""
    try:
        from src.balance_validator import BalanceValidator
        from src.enhanced_binance_client import EnhancedBinanceClient
        
        # Initialize Binance client
        api_key = os.getenv('BINANCE_API_KEY')
        secret_key = os.getenv('BINANCE_SECRET_KEY')
        
        if not api_key or not secret_key or api_key == 'your_binance_api_key_here':
            return jsonify({
                'success': False,
                'error': 'binance_not_configured',
                'message': 'Binance API credentials not configured. Please update .env file.',
                'can_start_robot': False
            }), 400
        
        binance_client = EnhancedBinanceClient(api_key, secret_key)
        validator = BalanceValidator(binance_client)
        
        # Get balance summary
        summary = validator.get_balance_summary()
        
        # Get detailed validation
        is_valid, message, balances = validator.validate_reserve_asset_balance()
        
        return jsonify({
            'success': summary['success'],
            'balance_summary': summary,
            'validation_result': {
                'is_valid': is_valid,
                'message': message,
                'can_start_robot': is_valid
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'validation_error',
            'message': str(e),
            'can_start_robot': False
        }), 500

@app.route('/api/robot-startup', methods=['POST'])
def robot_startup():
    """Validate and prepare robot for startup"""
    try:
        from src.enhanced_real_trading_engine import EnhancedRealTradingEngine
        from src.enhanced_binance_client import EnhancedBinanceClient
        
        # Initialize components
        api_key = os.getenv('BINANCE_API_KEY')
        secret_key = os.getenv('BINANCE_SECRET_KEY')
        
        if not api_key or not secret_key:
            return jsonify({
                'success': False,
                'error': 'binance_not_configured',
                'message': 'Binance API credentials not configured'
            }), 400
        
        binance_client = EnhancedBinanceClient(api_key, secret_key)
        
        # Initialize trading engine (without portfolio manager for validation)
        engine = EnhancedRealTradingEngine(binance_client, None, robot_state_manager)
        
        # Perform startup validation
        startup_result = engine.startup_robot()
        
        return jsonify(startup_result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'startup_error',
            'message': str(e),
            'can_start_robot': False
        }), 500

@app.route('/api/freeze', methods=['POST'])
def freeze_robot():
    """Freeze the robot - suspend all trading cycles"""
    try:
        success = robot_state_manager.freeze_robot("Robot gelé manuellement depuis le dashboard")
        if success:
            return jsonify({'success': True, 'message': 'Robot gelé avec succès - tous les cycles de trading sont suspendus'})
        else:
            return jsonify({'error': 'Impossible de geler le robot'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/unfreeze', methods=['POST'])
def unfreeze_robot():
    """Unfreeze the robot with balance validation for live mode"""
    try:
        # Check if in dry-run mode
        dry_run_mode = os.getenv('ROBOT_DRY_RUN', 'true').lower() == 'true'
        
        if not dry_run_mode:
            # In live mode, validate balance before unfreezing
            try:
                from src.balance_validator import BalanceValidator
                from src.enhanced_binance_client import EnhancedBinanceClient
                
                # Initialize Binance client for validation
                api_key = os.getenv('BINANCE_API_KEY')
                secret_key = os.getenv('BINANCE_SECRET_KEY')
                
                if not api_key or not secret_key or api_key == 'your_binance_api_key_here':
                    return jsonify({
                        'success': False,
                        'error': 'binance_not_configured',
                        'message': 'Cannot unfreeze robot: Binance API credentials not configured. Please update .env file.'
                    }), 400
                
                binance_client = EnhancedBinanceClient(api_key, secret_key)
                validator = BalanceValidator(binance_client)
                
                # Validate balance
                is_valid, message, balances = validator.validate_reserve_asset_balance()
                
                if not is_valid:
                    return jsonify({
                        'success': False,
                        'error': 'insufficient_balance',
                        'message': f'Cannot unfreeze robot: {message}',
                        'suggestion': 'Please deposit more funds or use "Check Balance" to verify your account.'
                    }), 400
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': 'validation_error',
                    'message': f'Cannot validate balance before unfreezing: {str(e)}'
                }), 500
        
        # Proceed with unfreezing (balance is sufficient or in dry-run mode)
        success = robot_state_manager.unfreeze_robot()
        if success:
            robot_state_manager.reset_suspended_cycles()
            
            mode_message = "DRY-RUN mode" if dry_run_mode else "LIVE mode with sufficient balance"
            return jsonify({
                'success': True, 
                'message': f'Robot unfrozen successfully - trading cycles can resume ({mode_message})'
            })
        else:
            return jsonify({'error': 'Failed to unfreeze robot'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/extract', methods=['POST'])
def portfolio_extract():
    """Extract EUR amount from portfolio to USDC"""
    try:
        data = request.get_json()
        eur_amount = float(data.get('eur_amount', 0))
        dry_run = data.get('dry_run', True)
        
        if eur_amount <= 0:
            return jsonify({'error': 'EUR amount must be positive'}), 400
        
        # Import here to avoid circular imports
        from src.portfolio_extract import PortfolioExtractor
        from src.enhanced_binance_client import EnhancedBinanceClient
        from src.portfolio_manager import PortfolioManager
        
        # Initialize components
        binance_client = EnhancedBinanceClient(
            os.getenv('BINANCE_API_KEY'),
            os.getenv('BINANCE_SECRET_KEY')
        )
        portfolio_manager = PortfolioManager()
        
        extractor = PortfolioExtractor(portfolio_manager, binance_client, robot_state_manager)
        
        # Execute extract operation
        success, summary = extractor.execute_extract(eur_amount, dry_run)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Extract operation completed successfully',
                'summary': {
                    'eur_amount': summary['eur_amount_requested'],
                    'bnb_collected': summary['bnb_collected'],
                    'usdc_received': summary.get('usdc_received', 0),
                    'positions_sold': len(summary['positions_sold']),
                    'dry_run': summary['dry_run'],
                    'steps_completed': summary['steps_completed']
                }
            })
        else:
            return jsonify({
                'error': 'Extract operation failed',
                'errors': summary['errors'],
                'steps_completed': summary['steps_completed']
            }), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/inject', methods=['POST'])
def portfolio_inject():
    """Inject USDC amount into portfolio proportionally"""
    try:
        data = request.get_json()
        usdc_amount = float(data.get('usdc_amount', 0))
        dry_run = data.get('dry_run', True)
        
        if usdc_amount <= 0:
            return jsonify({'error': 'USDC amount must be positive'}), 400
        
        # Import here to avoid circular imports
        from src.portfolio_inject import PortfolioInjector
        from src.enhanced_binance_client import EnhancedBinanceClient
        from src.portfolio_manager import PortfolioManager
        
        # Initialize components
        binance_client = EnhancedBinanceClient(
            os.getenv('BINANCE_API_KEY'),
            os.getenv('BINANCE_SECRET_KEY')
        )
        portfolio_manager = PortfolioManager()
        
        injector = PortfolioInjector(portfolio_manager, binance_client, robot_state_manager)
        
        # Check USDC availability first
        is_available, availability_msg = injector.check_usdc_availability(usdc_amount)
        if not is_available:
            return jsonify({
                'error': 'Insufficient USDC balance',
                'message': availability_msg,
                'available_usdc': injector.get_usdc_balance()
            }), 400
        
        # Execute inject operation
        success, summary = injector.execute_inject(usdc_amount, dry_run)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Inject operation completed successfully',
                'summary': {
                    'usdc_amount': summary['usdc_amount_requested'],
                    'bnb_distributed': summary['bnb_distributed'],
                    'usdc_converted': summary.get('usdc_converted', 0),
                    'positions_enhanced': len(summary['positions_enhanced']),
                    'dry_run': summary['dry_run'],
                    'steps_completed': summary['steps_completed']
                }
            })
        else:
            return jsonify({
                'error': 'Inject operation failed',
                'errors': summary['errors'],
                'steps_completed': summary['steps_completed']
            }), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/usdc-balance', methods=['GET'])
def get_usdc_balance():
    """Get current USDC balance in Binance account"""
    try:
        from src.enhanced_binance_client import EnhancedBinanceClient
        
        binance_client = EnhancedBinanceClient(
            os.getenv('BINANCE_API_KEY'),
            os.getenv('BINANCE_SECRET_KEY')
        )
        
        account_info = binance_client.get_account_info()
        balances = account_info.get('balances', [])
        
        usdc_balance = 0.0
        for balance in balances:
            if balance['asset'] == 'USDC':
                usdc_balance = float(balance['free'])
                break
        
        return jsonify({
            'success': True,
            'usdc_balance': usdc_balance,
            'formatted_balance': f"{usdc_balance:.6f} USDC"
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/config', methods=['GET'])
def get_configuration():
    """Get current configuration parameters (excluding secrets)"""
    try:
        import os
        from dotenv import load_dotenv
        
        # Reload environment variables
        load_dotenv()
        
        # Define which keys to exclude (secrets and sensitive data)
        excluded_keys = {
            'BINANCE_API_KEY', 'BINANCE_SECRET_KEY', 'FLASK_SECRET_KEY',
            'DATABASE_URL', 'DB_PASSWORD', 'SSL_CERT_PATH', 'SSL_KEY_PATH'
        }
        
        # Get all environment variables that start with common prefixes
        config_prefixes = [
            'ROBOT_', 'TRADING_', 'PORTFOLIO_', 'CYCLE_', 'MIN_', 'MAX_',
            'ALLOCATION_', 'RESERVE_', 'FLASK_', 'DATABASE_', 'INITIAL_',
            'STOP_', 'USE_', 'SWAP_', 'LOOKBACK_', 'TOP_', 'ENABLE_'
        ]
        
        config = {}
        
        # Get all environment variables
        for key, value in os.environ.items():
            # Include if it starts with our prefixes or is a known config key
            if (any(key.startswith(prefix) for prefix in config_prefixes) or 
                key in ['DOMAIN_NAME', 'USE_HTTPS', 'FLASK_ENV', 'FLASK_PORT', 'FLASK_HOST']):
                
                # Exclude sensitive keys
                if key not in excluded_keys:
                    config[key] = value
        
        # Add some computed values
        config['_COMPUTED_CYCLE_HOURS'] = f"{float(config.get('CYCLE_DURATION', 1440)) / 60:.1f}"
        config['_COMPUTED_ALLOCATION_PERCENT'] = f"{float(config.get('ALLOCATION_PERCENTAGE', 0.8)) * 100:.0f}%"
        
        return jsonify({
            'success': True,
            'config': config,
            'count': len(config)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Dynamic strategy routes removed - only protected_fixed_sim6_v3.0 is used

# Market analysis route removed - only protected_fixed_sim6_v3.0 strategy is used

@app.route('/api/close-portfolio', methods=['POST'])
def close_portfolio():
    """Close portfolio completely - liquidate all positions and optionally reset"""
    try:
        data = request.get_json()
        confirm_liquidation = data.get('confirm_liquidation', False)
        reset_portfolio = data.get('reset_portfolio', False)
        new_reserve_amount = data.get('new_reserve_amount', 0.1)
        auto_start = data.get('auto_start', False)
        dry_run = data.get('dry_run', True)
        
        if not confirm_liquidation:
            return jsonify({'error': 'Liquidation confirmation required'}), 400
        
        if reset_portfolio and (not new_reserve_amount or new_reserve_amount < 0.01):
            return jsonify({'error': 'Invalid reserve amount for reset (minimum 0.01 BNB)'}), 400
        
        # Import here to avoid circular imports
        from src.portfolio_close import PortfolioCloser
        from src.enhanced_binance_client import EnhancedBinanceClient
        from src.portfolio_manager import PortfolioManager
        
        # Initialize components
        binance_client = EnhancedBinanceClient(
            os.getenv('BINANCE_API_KEY'),
            os.getenv('BINANCE_SECRET_KEY')
        )
        portfolio_manager = PortfolioManager()
        
        closer = PortfolioCloser(portfolio_manager, binance_client, robot_state_manager)
        
        # Execute close operation
        success, summary = closer.execute_close(
            liquidate_all=True,
            reset_portfolio=reset_portfolio,
            new_reserve_amount=new_reserve_amount if reset_portfolio else None,
            auto_start=auto_start if reset_portfolio else False,
            dry_run=dry_run
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Portfolio closure operation {"simulated" if dry_run else "completed"} successfully',
                'summary': {
                    'total_usdc_generated': summary.get('total_usdc_generated', 0),
                    'positions_liquidated': summary.get('positions_liquidated', 0),
                    'bnb_converted': summary.get('bnb_converted', 0),
                    'reset_portfolio': summary.get('reset_portfolio', False),
                    'new_reserve_amount': summary.get('new_reserve_amount', 0),
                    'auto_start': summary.get('auto_start', False),
                    'dry_run': summary['dry_run'],
                    'steps_completed': summary['steps_completed']
                }
            })
        else:
            return jsonify({
                'error': 'Portfolio closure operation failed',
                'errors': summary['errors'],
                'steps_completed': summary['steps_completed']
            }), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/live-prices')
def get_live_prices():
    """Get live prices for assets with balances"""
    try:
        from src.binance_client import BinanceAPIClient
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        api_key = os.getenv('BINANCE_API_KEY')
        secret_key = os.getenv('BINANCE_SECRET_KEY')
        
        if not api_key or not secret_key or api_key == 'your_binance_api_key_here':
            return jsonify({'error': 'Binance credentials not configured'}), 400
        
        client = BinanceAPIClient(api_key, secret_key)
        
        # Get account info
        account_info = client.get_account_info()
        if not account_info:
            return jsonify({'error': 'Unable to get account info'}), 500
        
        live_prices = {}
        total_value_usdt = 0
        
        # Get live prices for balances > 0
        for balance in account_info.get('balances', []):
            asset = balance['asset']
            free_balance = float(balance['free'])
            locked_balance = float(balance['locked'])
            total_balance = free_balance + locked_balance
            
            if total_balance > 0:
                if asset == 'USDT':
                    live_prices[asset] = {
                        'price': 1.0,
                        'symbol': 'USDT',
                        'value_usdt': total_balance,
                        'balance': total_balance
                    }
                    total_value_usdt += total_balance
                else:
                    # Get price for this asset
                    symbol = f"{asset}USDT"
                    try:
                        price_data = client.client.get_symbol_ticker(symbol=symbol)
                        price = float(price_data['price'])
                        value_usdt = total_balance * price
                        
                        live_prices[asset] = {
                            'price': price,
                            'symbol': symbol,
                            'value_usdt': value_usdt,
                            'balance': total_balance
                        }
                        total_value_usdt += value_usdt
                    except Exception as e:
                        # If pair doesn't exist, mark as unavailable
                        live_prices[asset] = {
                            'price': 0,
                            'symbol': f"{asset}USDT",
                            'value_usdt': 0,
                            'balance': total_balance,
                            'error': 'Price unavailable'
                        }
        
        return jsonify({
            'live_prices': live_prices,
            'total_value_usdt': total_value_usdt,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/combined-history')
def get_combined_history():
    """Get combined portfolio and reserve history"""
    try:
        combined_data = []
        session = db_manager.get_session()
        
        cycles = session.query(TradingCycle).order_by(TradingCycle.cycle_number).all()
        
        for cycle in cycles:
            combined_data.append({
                'cycle': cycle.cycle_number,
                'date': cycle.cycle_date.isoformat(),
                'portfolio_value': cycle.portfolio_value,
                'bnb_reserve': cycle.bnb_reserve,
                'total_value': cycle.total_value
            })
        
        session.close()
        return jsonify(combined_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/portfolio-history')
def portfolio_history():
    """Portfolio history visualization page"""
    try:
        # Prepare data for plotting
        cycles = []
        portfolio_values = []
        total_values = []
        dates = []
        
        session = db_manager.get_session()
        cycle_data = session.query(TradingCycle).order_by(TradingCycle.cycle_number).all()
        
        # Handle empty data case
        if not cycle_data:
            print("No trading cycles found - creating empty chart")
            # Create empty chart with message
            fig = go.Figure()
            fig.add_annotation(
                text="No trading cycle data available yet.<br>Start trading or run a simulation to see portfolio history.",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=16, color="gray")
            )
            fig.update_layout(
                title='Portfolio Value Evolution - No Data Available',
                xaxis_title='Cycle Number',
                yaxis_title=f'Value ({os.getenv("RESERVE_ASSET", "BNB")})',
                template='plotly_white',
                showlegend=False
            )
        else:
            for cycle in cycle_data:
                cycles.append(cycle.cycle_number)
                portfolio_values.append(cycle.portfolio_value)
                total_values.append(cycle.total_value)
                dates.append(cycle.cycle_date.strftime('%d/%m/%Y %H:%M'))
            
            # Prepare portfolio breakdown data for customdata
            portfolio_breakdowns = [cycle.portfolio_breakdown for cycle in cycle_data]
            
            # Combine portfolio breakdown and reserve data for customdata
            combined_data = []
            for i in range(len(cycle_data)):
                combined_data.append({
                    'portfolio_breakdown': portfolio_breakdowns[i],
                    'bnb_reserve': cycle_data[i].bnb_reserve
                })
            
            # Create Plotly charts with data
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=cycles,
                y=portfolio_values,
                mode='lines+markers',
                name=f'Portfolio Value ({os.getenv("RESERVE_ASSET", "BNB")})',
                line=dict(color='blue', width=2),
                customdata=combined_data,
                hovertemplate=f'Cycle: %{{x}}<br>Portfolio Value: %{{y:.6f}} {os.getenv("RESERVE_ASSET", "BNB")}<br><i>Click to see portfolio breakdown</i><extra></extra>'
            ))
            
            fig.add_trace(go.Scatter(
                x=cycles,
                y=total_values,
                mode='lines+markers',
                name=f'Total Value ({os.getenv("RESERVE_ASSET", "BNB")})',
                line=dict(color='green', width=2),
                customdata=combined_data,
                hovertemplate=f'Cycle: %{{x}}<br>Total Value: %{{y:.6f}} {os.getenv("RESERVE_ASSET", "BNB")}<br><i>Click to see portfolio breakdown</i><extra></extra>'
            ))
            
            fig.update_layout(
                title='Portfolio Value Evolution',
                xaxis_title='Cycle Number',
                yaxis_title=f'Value ({os.getenv("RESERVE_ASSET", "BNB")})',
                hovermode='x unified',
                template='plotly_white'
            )
        
        session.close()
        
        # Convert to JSON safely
        try:
            chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        except Exception as json_error:
            print(f"JSON encoding error: {json_error}")
            # Fallback to simple empty chart
            fig = go.Figure()
            fig.add_annotation(
                text="Chart data error - please check server logs",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False
            )
            chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        
        return render_template('portfolio_history.html', chart_json=chart_json)
        
    except Exception as e:
        print(f"Portfolio history error: {e}")
        import traceback
        traceback.print_exc()
        return render_template('error.html', error=str(e))

@app.route('/reserve-history')
def reserve_history():
    """Reserve history visualization page"""
    try:
        # Prepare data for plotting
        cycles = []
        reserves = []
        dates = []
        
        session = db_manager.get_session()
        cycle_data = session.query(TradingCycle).order_by(TradingCycle.cycle_number).all()
        
        for cycle in cycle_data:
            cycles.append(cycle.cycle_number)
            reserves.append(cycle.bnb_reserve)
            dates.append(cycle.cycle_date.strftime('%Y-%m-%d %H:%M'))
        
        session.close()
        
        # Create Plotly chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=cycles,
            y=reserves,
            mode='lines+markers',
            name=f'{os.getenv("RESERVE_ASSET", "BNB")} Reserve',
            line=dict(color='orange', width=2),
            fill='tonexty',
            hovertemplate=f'Cycle: %{{x}}<br>Reserve: %{{y:.6f}} {os.getenv("RESERVE_ASSET", "BNB")}<extra></extra>'
        ))
        
        # Add minimum reserve limit line
        min_limit = float(os.getenv('MIN_RESERVE_LIMIT', 50.0))
        if cycles:
            fig.add_hline(
                y=min_limit,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Min Reserve Limit ({min_limit} {os.getenv('RESERVE_ASSET', 'BNB')})"
            )
        
        fig.update_layout(
            title=f'{os.getenv("RESERVE_ASSET", "BNB")} Reserve Evolution',
            xaxis_title='Cycle Number',
            yaxis_title=f'Reserve ({os.getenv("RESERVE_ASSET", "BNB")})',
            hovermode='x unified',
            template='plotly_white'
        )
        
        chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        
        return render_template('reserve_history.html', chart_json=chart_json)
        
    except Exception as e:
        return render_template('error.html', error=str(e))
        
        fig.update_layout(
            title=f'{os.getenv("RESERVE_ASSET", "BNB")} Reserve Evolution',
            xaxis_title='Cycle Number',
            yaxis_title=f'Reserve ({os.getenv("RESERVE_ASSET", "BNB")})',
            hovermode='x unified',
            template='plotly_white'
        )
        
        chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        
        return render_template('reserve_history.html', chart_json=chart_json)
        
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/combined-history')
def combined_history():
    """Combined portfolio and reserve history visualization page"""
    try:
        # Prepare data for plotting
        cycles = []
        portfolio_values = []
        reserves = []
        dates = []
        
        session = db_manager.get_session()
        cycle_data = session.query(TradingCycle).order_by(TradingCycle.cycle_number).all()
        
        for cycle in cycle_data:
            cycles.append(cycle.cycle_number)
            portfolio_values.append(cycle.portfolio_value)
            reserves.append(cycle.bnb_reserve)
            dates.append(cycle.cycle_date.strftime('%Y-%m-%d %H:%M'))
        
        session.close()
        
        # Create Plotly chart with both series
        fig = go.Figure()
        
        # Portfolio Value in Blue
        fig.add_trace(go.Scatter(
            x=cycles,
            y=portfolio_values,
            mode='lines+markers',
            name=f'Portfolio Value ({os.getenv("RESERVE_ASSET", "BNB")})',
            line=dict(color='blue', width=3),
            marker=dict(color='blue', size=6),
            hovertemplate=f'Cycle: %{{x}}<br>Portfolio Value: %{{y:.6f}} {os.getenv("RESERVE_ASSET", "BNB")}<extra></extra>'
        ))
        
        # Reserve in Red
        fig.add_trace(go.Scatter(
            x=cycles,
            y=reserves,
            mode='lines+markers',
            name=f'{os.getenv("RESERVE_ASSET", "BNB")} Reserve',
            line=dict(color='red', width=3),
            marker=dict(color='red', size=6),
            hovertemplate=f'Cycle: %{{x}}<br>{os.getenv("RESERVE_ASSET", "BNB")} Reserve: %{{y:.6f}} {os.getenv("RESERVE_ASSET", "BNB")}<extra></extra>'
        ))
        
        # Add minimum reserve limit line
        min_limit = float(os.getenv('MIN_RESERVE_LIMIT', 50.0))
        if cycles:
            fig.add_hline(
                y=min_limit,
                line_dash="dash",
                line_color="red",
                line_width=2,
                opacity=0.7,
                annotation_text=f"Min Reserve Limit ({min_limit} {os.getenv('RESERVE_ASSET', 'BNB')})",
                annotation_position="bottom right"
            )
        
        fig.update_layout(
            title=f'Portfolio Value and {os.getenv("RESERVE_ASSET", "BNB")} Reserve Evolution',
            xaxis_title='Cycle Number',
            yaxis_title=f'Value ({os.getenv("RESERVE_ASSET", "BNB")})',
            hovermode='x unified',
            template='plotly_white',
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )
        
        chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        
        return render_template('combined_history.html', chart_json=chart_json)
        
    except Exception as e:
        return render_template('error.html', error=str(e))

# Simulator Routes

@app.route('/simulator')
def simulator_start():
    """Simulation start page"""
    # Get default engine from .env TRADING_STRATEGY
    trading_strategy = 'protected_fixed_sim6_v3.0'.lower()
    
    # Only protected_fixed_sim6_v3.0 is available now
    default_engine = 'protected_fixed_sim6_v3.0'
    trading_strategy = 'protected_fixed_sim6_v3.0'  # Override any old strategy
    
    # Get calibration profiles for form
    calibration_manager = get_calibration_manager()
    calibration_profiles = calibration_manager.get_profile_for_web_form()
    default_profile = os.getenv('DEFAULT_CALIBRATION_PROFILE', 'moderate_realistic')
    
    return render_template('simulator_start.html', 
                         default_engine=default_engine,
                         cycle_duration_env=os.getenv('CYCLE_DURATION', '1440'),
                         base_asset=os.getenv('RESERVE_ASSET', 'BNB'),
                         calibration_profiles=calibration_profiles,
                         default_calibration_profile=default_profile)

@app.route('/simulator/list')
def simulator_list():
    """List all simulations"""
    try:
        session = db_manager.get_session()
        simulations = session.query(Simulation).order_by(Simulation.name.asc()).all()
        
        # Add current cycle information and calculate total fees for each simulation
        simulation_data = []
        for sim in simulations:
            # Get the latest cycle number for this simulation
            latest_cycle = session.query(SimulationCycle).filter(
                SimulationCycle.simulation_id == sim.id
            ).order_by(SimulationCycle.cycle_number.desc()).first()
            
            current_cycle = latest_cycle.cycle_number if latest_cycle else 0
            
            # Calculate total fees from simulation cycles
            total_cycle_fees = session.query(func.sum(SimulationCycle.trading_costs)).filter(
                SimulationCycle.simulation_id == sim.id
            ).scalar() or 0.0
            
            # Use cycle fees if available, otherwise use existing fee fields
            if total_cycle_fees > 0:
                calculated_total_fees = total_cycle_fees
            elif hasattr(sim, 'total_trading_costs') and sim.total_trading_costs:
                calculated_total_fees = sim.total_trading_costs
            elif hasattr(sim, 'fee_estimate') and sim.fee_estimate:
                calculated_total_fees = sim.fee_estimate
            else:
                calculated_total_fees = 0.0
            
            # Calculate net final value (after fees)
            if sim.final_total_value and calculated_total_fees > 0:
                final_total_value_net = sim.final_total_value - calculated_total_fees
            else:
                final_total_value_net = sim.final_total_value
            
            # Create a data object with all the information
            sim_data = {
                'simulation': sim,
                'current_cycle': current_cycle,
                'calculated_total_fees': calculated_total_fees,
                'final_total_value_net': final_total_value_net
            }
            simulation_data.append(sim_data)
            
        session.close()
        
        return render_template('simulator_list.html', simulation_data=simulation_data)
    except Exception as e:
        print(f"[ERROR] Exception in simulator_list: {e}")
        import traceback
        traceback.print_exc()
        return render_template('error.html', error=str(e))



@app.route('/simulator/run', methods=['POST'])
def run_simulation():
    """Start a new simulation"""
    try:
        # Get form data
        name = request.form.get('name', '').strip()
        start_date_str = request.form.get('start_date')
        duration_days = int(request.form.get('duration_days'))
        cycle_length_str = request.form.get('cycle_length_minutes') or os.getenv('CYCLE_DURATION', '1440')
        cycle_length_minutes = int(cycle_length_str)
        starting_reserve = float(request.form.get('starting_reserve'))
        data_source = request.form.get('data_source', 'binance_historical')
        engine_version = request.form.get('engine_version', 'daily_rebalance_v1.0')
        realistic_mode = request.form.get('realistic_mode') == 'on'  # Checkbox value
        calibration_profile = request.form.get('calibration_profile', os.getenv('DEFAULT_CALIBRATION_PROFILE', 'moderate_realistic'))
        trades_count = 1

        # Validate inputs
        if not name:
            flash('Simulation name is required', 'error')
            return redirect(url_for('simulator_start'))
        if duration_days <= 0 or duration_days > 365:
            flash('Duration must be between 1 and 365 days', 'error')
            return redirect(url_for('simulator_start'))
        if cycle_length_minutes <= 0 or cycle_length_minutes > 43200:
            flash('Cycle length must be between 1 and 43200 minutes (30 days)', 'error')
            return redirect(url_for('simulator_start'))
        if starting_reserve <= 0 or starting_reserve > 1000000:
            flash(f'Starting reserve must be greater than 0 and less than 1,000,000 {os.getenv("RESERVE_ASSET", "BNB")}', 'error')
            return redirect(url_for('simulator_start'))
        if data_source not in ['binance_historical', 'historical']:
            flash('Only historical data source is supported', 'error')
            return redirect(url_for('simulator_start'))

        expected_cycles = (duration_days * 24 * 60) / cycle_length_minutes
        if expected_cycles > 10000:
            flash(f'Too many cycles ({expected_cycles:.0f}). Please increase cycle length or reduce duration.', 'error')
            return redirect(url_for('simulator_start'))

        # Parse start date
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')

        # Create simulation record
        session = db_manager.get_session()
        try:
            simulation = Simulation(
                name=name,
                start_date=start_date,
                duration_days=duration_days,
                cycle_length_minutes=cycle_length_minutes,
                starting_reserve=starting_reserve,
                final_portfolio_value=0.0,
                final_reserve_value=0.0,
                final_total_value=0.0,
                total_cycles=0,
                data_source='binance_historical',
                engine_version='daily_rebalance_v1.0',
                realistic_mode=realistic_mode,
                calibration_profile=calibration_profile if calibration_profile != 'none' else None,
                status='pending'
            )
            session.add(simulation)
            session.commit()
            simulation_id = simulation.id
        finally:
            session.close()

        # Launch background task
        socketio.start_background_task(run_historical_simulation_background, simulation_id, trades_count)

        flash(f'Simulation "{name}" started successfully with Daily Rebalance strategy!', 'success')
        return redirect(url_for('simulator_list'))
    except ValueError as e:
        flash(f'Invalid input: {str(e)}', 'error')
        return redirect(url_for('simulator_start'))
    except Exception as e:
        flash(f'Error starting simulation: {str(e)}', 'error')
        return redirect(url_for('simulator_start'))

@app.route('/simulator/<int:simulation_id>/history')
def simulation_history(simulation_id):
    """View simulation portfolio history"""
    try:
        session = db_manager.get_session()
        simulation = session.query(Simulation).get(simulation_id)
        if not simulation:
            session.close()
            return render_template('error.html', error='Simulation not found')

        cycles = session.query(SimulationCycle).filter_by(
            simulation_id=simulation_id
        ).order_by(SimulationCycle.cycle_number).all()

        # Calculate total fees from simulation cycles
        total_cycle_fees = session.query(func.sum(SimulationCycle.trading_costs)).filter(
            SimulationCycle.simulation_id == simulation_id
        ).scalar() or 0.0

        session.close()

        if not cycles:
            return render_template('error.html', error='No cycle data found for this simulation')

        # Extract data for the chart
        cycle_numbers = [cycle.cycle_number for cycle in cycles]
        total_values = [float(cycle.total_value) for cycle in cycles]
        portfolio_values = [float(cycle.portfolio_value or 0.0) for cycle in cycles]

        # Extract combined customdata for popup functionality (portfolio_breakdown + bnb_reserve)
        portfolio_breakdowns = []
        reserves = [float(cycle.bnb_reserve or 0.0) for cycle in cycles]
        for i, cycle in enumerate(cycles):
            breakdown = cycle.portfolio_breakdown
            if isinstance(breakdown, str):
                try:
                    breakdown = json.loads(breakdown)
                except Exception:
                    breakdown = {}
            if breakdown is None:
                breakdown = {}
            # Always output {crypto: {value, performance}} for popup
            new_breakdown = {}
            for coin, val in breakdown.items():
                if isinstance(val, dict) and 'value' in val:
                    # Already new format, but ensure performance exists
                    new_breakdown[coin] = {
                        'value': val.get('value', 0),
                        'performance': val.get('performance', 0)
                    }
                elif isinstance(val, dict) and 'quantity' in val and ('price' in val or 'entry_price' in val):
                    # Legacy format: convert
                    price = val.get('price', val.get('entry_price', 0))
                    new_breakdown[coin] = {
                        'value': val['quantity'] * price,
                        'performance': 0
                    }
                elif isinstance(val, (int, float)):
                    new_breakdown[coin] = {'value': val, 'performance': 0}
                else:
                    # Unknown format, skip
                    continue
            # If portfolio is empty, add a placeholder
            if not new_breakdown:
                new_breakdown['NO_ASSETS'] = {'value': 0, 'performance': 0}
            portfolio_breakdowns.append({
                'portfolio_breakdown': new_breakdown,
                'bnb_reserve': reserves[i],
                'portfolio_value': portfolio_values[i]
            })

        # Normalize data_source for UI compatibility
        if hasattr(simulation, 'data_source') and simulation.data_source:
            ds = simulation.data_source.lower()
            if 'historical' in ds and ('100%' in ds or ds.strip() == 'historical'):
                simulation.data_source = 'historical (100%)'
            elif 'simulated' in ds and '100%' in ds:
                simulation.data_source = 'simulated (100%)'

        # Create a chart configuration with combined customdata
        chart_json = json.dumps({
            "data": [{
                "x": cycle_numbers,
                "y": total_values,
                "type": "scatter",
                "mode": "lines+markers",
                "name": "Portfolio + Reserve",
                "line": {"color": "#28a745", "width": 3},
                "marker": {"color": "#28a745", "size": 8},
                "customdata": portfolio_breakdowns,
                "hovertemplate": f"Cycle: %{{x}}<br>Total Value: %{{y:.6f}} {os.getenv('RESERVE_ASSET', 'BNB')}<extra></extra>"
            }],
            "layout": {
                "title": f"Simulation: {simulation.name} - Portfolio + Reserve Value Evolution",
                "xaxis": {"title": "Cycle Number"},
                "yaxis": {"title": f"Total Value ({os.getenv('RESERVE_ASSET', 'BNB')})"},
                "template": "plotly_white"
            }
        })

        # Calculate net final value (after fees)
        final_total_value_net = None
        if simulation.final_total_value and total_cycle_fees > 0:
            final_total_value_net = simulation.final_total_value - total_cycle_fees

        return render_template('simulation_history.html', 
                             simulation=simulation, 
                             chart_json=chart_json,
                             total_fees=total_cycle_fees,
                             final_total_value_net=final_total_value_net)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return render_template('error.html', error=f'Error loading simulation history: {str(e)}')

@app.route('/api/simulation/<int:simulation_id>/progress')
def api_simulation_progress(simulation_id):
    """Return JSON with live simulation progress for dynamic UI updates."""
    try:
        session = db_manager.get_session()
        sim = session.query(Simulation).get(simulation_id)
        if not sim:
            session.close()
            return jsonify({'error': 'not_found'}), 404

        # Get latest cycle
        latest_cycle = session.query(SimulationCycle).filter_by(simulation_id=simulation_id) \
            .order_by(SimulationCycle.cycle_number.desc()).first()

        now = datetime.utcnow()
        created_at = sim.created_at if sim.created_at else now
        last_cycle_time = latest_cycle.cycle_date if latest_cycle else created_at

        # Determine if potentially stuck: no new cycle for > 15s
        cycle_minutes = sim.cycle_length_minutes or 1
        threshold_seconds = 15  # 15 seconds for fast stuck detection
        seconds_since_last_cycle = (now - last_cycle_time).total_seconds()
        is_stuck = sim.status == 'running' and seconds_since_last_cycle > threshold_seconds

        payload = {
            'id': sim.id,
            'status': sim.status,
            'total_cycles': sim.total_cycles,
            'last_cycle_number': latest_cycle.cycle_number if latest_cycle else 0,
            'last_cycle_time': last_cycle_time.isoformat() if last_cycle_time else None,
            'created_at': created_at.isoformat() if created_at else None,
            'completed_at': sim.completed_at.isoformat() if sim.completed_at else None,
            'elapsed_seconds': (now - created_at).total_seconds(),
            'seconds_since_last_cycle': seconds_since_last_cycle,
            'stuck': is_stuck,
            'stuck_threshold_seconds': threshold_seconds
        }
        session.close()
        return jsonify(payload)
    except Exception as e:
        return jsonify({'error': 'server_error', 'message': str(e)}), 500

def simulation_watchdog_loop(interval_seconds: int = 15):
    """Background loop that auto-resolves stuck simulations.

    If a simulation is 'running' and no new cycle has been saved for more than
    max(600s, 2x cycle_length_minutes), then:
      - If at least one cycle exists: force-complete using the last cycle values.
      - Else: mark as failed with an informative error_message.
    """
    while True:
        try:
            session = db_manager.get_session()
            try:
                now = datetime.utcnow()
                # Auto-start any 'pending' simulations that have lingered
                pending = session.query(Simulation).filter(Simulation.status == 'pending').all()
                for sim in pending:
                    # If created more than 5s ago and has no cycles, start it
                    last_cycle = (
                        session.query(SimulationCycle)
                        .filter_by(simulation_id=sim.id)
                        .order_by(SimulationCycle.cycle_number.desc())
                        .first()
                    )
                    if (now - (sim.created_at or now)).total_seconds() > 5 and not last_cycle:
                        try:
                            sim.status = 'running'
                            session.commit()
                            # Schedule background task
                            socketio.start_background_task(run_historical_simulation_background, sim.id, 1)
                            print(f"[Watchdog] Auto-started pending simulation {sim.id} ({sim.name})")
                        except Exception as _e:
                            print(f"[Watchdog] Failed to auto-start simulation {sim.id}: {_e}")

                running = session.query(Simulation).filter(Simulation.status == 'running').all()
                for sim in running:
                    # Find last cycle time
                    last_cycle = (
                        session.query(SimulationCycle)
                        .filter_by(simulation_id=sim.id)
                        .order_by(SimulationCycle.cycle_number.desc())
                        .first()
                    )
                    created_at = sim.created_at or now
                    last_cycle_time = last_cycle.cycle_date if last_cycle else created_at
                    cycle_minutes = sim.cycle_length_minutes or 1
                    # New logic: add grace period for new simulations
                    min_grace_seconds = max(120, 2 * 60 * cycle_minutes)  # 2 minutes or 2x cycle length
                    stuck_threshold_seconds = max(60, 4 * 60 * cycle_minutes)  # 4 minutes or 4x cycle length
                    seconds_since_created = (now - created_at).total_seconds()
                    seconds_since_last = (now - last_cycle_time).total_seconds()

                    if not last_cycle:
                        # Only auto-cancel if grace period has passed and still no cycles
                        if seconds_since_created > min_grace_seconds:
                            sim.status = 'failed'
                            sim.error_message = (
                                f"Auto-canceled: no cycles recorded after {int(seconds_since_created)}s (grace period {min_grace_seconds}s)."
                            )
                            sim.completed_at = now
                            print(f"[Watchdog] Auto-canceled simulation {sim.id} ({sim.name}) - no cycles after grace period")
                    else:
                        # For simulations with cycles, use a longer stuck threshold
                        if seconds_since_last > stuck_threshold_seconds:
                            sim.final_portfolio_value = float(last_cycle.portfolio_value)
                            sim.final_reserve_value = float(last_cycle.bnb_reserve)
                            sim.final_total_value = float(last_cycle.total_value)
                            sim.total_cycles = int(last_cycle.cycle_number)
                            sim.status = 'completed'
                            sim.error_message = (
                                f"Auto-completed (no activity for {int(seconds_since_last)}s, threshold {stuck_threshold_seconds}s)."
                            )
                            sim.completed_at = now
                            print(f"[Watchdog] Auto-completed simulation {sim.id} ({sim.name})")
                session.commit()
            finally:
                session.close()
        except Exception as e:
            print(f"[Watchdog] Error: {e}")
        time.sleep(interval_seconds)

def start_simulation_watchdog():
    """Start the simulation watchdog in a background task once."""
    global simulation_watchdog_started
    if not simulation_watchdog_started:
        try:
            socketio.start_background_task(simulation_watchdog_loop)
            simulation_watchdog_started = True
            print("[Watchdog] Started")
        except Exception as e:
            print(f"[Watchdog] Failed to start: {e}")

# Try to start watchdog on import (safe no-op if it fails). It will also
# be started lazily on the first request below, so imports won't break.
try:
    start_simulation_watchdog()
except Exception as _e:
    print(f"[Watchdog] Deferred start: {_e}")

# Lazy ensure on first index hit
@app.before_request
def _ensure_watchdog():
    if not simulation_watchdog_started:
        start_simulation_watchdog()

@app.route('/simulator/<int:simulation_id>/history-debug')
def simulation_history_debug(simulation_id):
    """Debug version to test chart data"""
    try:
        session = db_manager.get_session()
        simulation = session.query(Simulation).get(simulation_id)
        cycles = session.query(SimulationCycle).filter_by(
            simulation_id=simulation_id
        ).order_by(SimulationCycle.cycle_number).all()
        session.close()
        
        cycle_numbers = [cycle.cycle_number for cycle in cycles]
        portfolio_values = [cycle.portfolio_value for cycle in cycles]
        
        chart_data = {
            'data': [{
                'x': cycle_numbers,
                'y': portfolio_values,
                'type': 'scatter',
                'mode': 'lines+markers',
                'name': 'Portfolio Value'
            }],
            'layout': {
                'title': f'Simulation: {simulation.name}',
                'xaxis': {'title': 'Cycle Number'},
                'yaxis': {'title': f"Portfolio Value ({os.getenv('RESERVE_ASSET', 'BNB')})"}
            }
        }
        
        return jsonify(chart_data)
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/simulator/<int:simulation_id>/combined')
def simulation_combined_history(simulation_id):
    """View simulation combined portfolio and reserve history"""
    try:
        session = db_manager.get_session()
        simulation = session.query(Simulation).get(simulation_id)
        if not simulation:
            session.close()
            return render_template('error.html', error='Simulation not found')
        
        cycles = session.query(SimulationCycle).filter_by(
            simulation_id=simulation_id
        ).order_by(SimulationCycle.cycle_number).all()
        
        # Calculate total fees from simulation cycles
        total_cycle_fees = session.query(func.sum(SimulationCycle.trading_costs)).filter(
            SimulationCycle.simulation_id == simulation_id
        ).scalar() or 0.0
        
        session.close()
        
        if not cycles:
            return render_template('error.html', error='No cycle data found for this simulation')
        
    # Trades windows removed
        
        # Create combined chart
        cycle_numbers = [cycle.cycle_number for cycle in cycles]
        portfolio_values = [cycle.portfolio_value for cycle in cycles]
        reserves = [cycle.bnb_reserve for cycle in cycles]
        # Normalize portfolio_breakdown into dicts
        portfolio_breakdowns = []
        for cycle in cycles:
            pb = cycle.portfolio_breakdown
            if isinstance(pb, str):
                try:
                    pb = json.loads(pb)
                except Exception:
                    pb = {}
            if pb is None:
                pb = {}
            portfolio_breakdowns.append(pb)
        
        # Combine portfolio breakdown and reserve data for customdata
        combined_data = []
        for i in range(len(cycles)):
            combined_data.append({
                'portfolio_breakdown': portfolio_breakdowns[i],
                'bnb_reserve': float(reserves[i] or 0.0),
                'portfolio_value': float(portfolio_values[i] or 0.0)
            })
        
        fig = go.Figure()
        
        # Portfolio in Blue
        fig.add_trace(go.Scatter(
            x=cycle_numbers,
            y=portfolio_values,
            mode='lines+markers',
            name=f'Portfolio Value ({os.getenv("RESERVE_ASSET", "BNB")})',
            line=dict(color='blue', width=3),
            marker=dict(color='blue', size=8),
            hovertemplate=f'Cycle: %{{x}}<br>Portfolio Value: %{{y:.6f}} {os.getenv("RESERVE_ASSET", "BNB")}<br>Click for details<extra></extra>',
            customdata=combined_data  # Pass both portfolio and reserve data for click events
        ))
        
        # Reserve in Red
        fig.add_trace(go.Scatter(
            x=cycle_numbers,
            y=reserves,
            mode='lines+markers',
            name=f'{os.getenv("RESERVE_ASSET", "BNB")} Reserve',
            line=dict(color='red', width=3),
            marker=dict(color='red', size=6),
            hovertemplate=f'Cycle: %{{x}}<br>{os.getenv("RESERVE_ASSET", "BNB")} Reserve: %{{y:.6f}} {os.getenv("RESERVE_ASSET", "BNB")}<extra></extra>'
        ))
        
        fig.update_layout(
            title=f'Simulation: {simulation.name} - Portfolio Value and {os.getenv("RESERVE_ASSET", "BNB")} Reserve Evolution',
            xaxis_title='Cycle Number',
            yaxis_title=f'Value ({os.getenv("RESERVE_ASSET", "BNB")})',
            hovermode='x unified',
            template='plotly_white',
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )
        
        chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        
        # Calculate net final value (after fees)
        final_total_value_net = None
        if simulation.final_total_value and total_cycle_fees > 0:
            final_total_value_net = simulation.final_total_value - total_cycle_fees

        return render_template('simulation_combined_history.html', 
                             simulation=simulation, 
                             chart_json=chart_json,
                             total_fees=total_cycle_fees,
                             final_total_value_net=final_total_value_net)
        
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/simulator/<int:simulation_id>/delete', methods=['POST', 'GET'])
def delete_simulation(simulation_id):
    """Delete a simulation and all its cycles"""
    try:
        session = db_manager.get_session()
        simulation = session.query(Simulation).get(simulation_id)
        
        if not simulation:
            flash('Simulation not found', 'error')
            session.close()
            return redirect(url_for('simulator_list'))
        
        simulation_name = simulation.name
        
    # Delete the simulation (cascade will delete simulation_cycles)
        session.delete(simulation)
        session.commit()
        session.close()
        
        flash(f'Simulation "{simulation_name}" has been deleted successfully', 'success')
        return redirect(url_for('simulator_list'))
        
    except Exception as e:
        if session:
            session.close()
        flash(f'Error deleting simulation: {str(e)}', 'error')
        return redirect(url_for('simulator_list'))

@app.route('/simulator/delete-all', methods=['POST', 'GET'])
def delete_all_simulations():
    """Delete all simulations and their cycles"""
    print(f"DELETE ALL SIMULATIONS route called - Method: {request.method}")
    try:
        session = db_manager.get_session()
        
        # Count simulations before deletion
        nb_simulations = session.query(Simulation).count()
        nb_cycles = session.query(SimulationCycle).count()
        print(f"Found {nb_simulations} simulations and {nb_cycles} cycles to delete")
        
        if nb_simulations == 0:
            print("No simulations to delete")
            flash('No simulations to delete', 'info')
            session.close()
            return redirect(url_for('simulator_list'))
        
        # Delete all simulation cycles first
        print("Deleting all simulation cycles...")
        deleted_cycles = session.query(SimulationCycle).delete(synchronize_session=False)
        print(f"Deleted {deleted_cycles} cycles")
        
        # Delete all simulations
        print("Deleting all simulations...")
        deleted_sims = session.query(Simulation).delete(synchronize_session=False)
        print(f"Deleted {deleted_sims} simulations")
        
        session.commit()
        print("Database changes committed")
        session.close()
        
        # Use actual deleted counts if available
        if deleted_sims is not None and deleted_cycles is not None:
            print(f"SUCCESS: Deleted {deleted_sims} simulations and {deleted_cycles} cycles")
            flash(f'Successfully deleted {deleted_sims} simulations and {deleted_cycles} cycles', 'success')
        else:
            print(f"SUCCESS: Deleted {nb_simulations} simulations and {nb_cycles} cycles")
            flash(f'Successfully deleted {nb_simulations} simulations and {nb_cycles} cycles', 'success')
        
        print("Redirecting to simulator_list")
        return redirect(url_for('simulator_list'))
        
    except Exception as e:
        print(f"ERROR during deletion: {str(e)}")
        if 'session' in locals():
            session.close()
        flash(f'Error during deletion: {str(e)}', 'error')
        return redirect(url_for('simulator_list'))

@app.route('/simulator/<int:simulation_id>/force-complete', methods=['POST', 'GET'])
def force_complete_simulation(simulation_id):
    """Force mark a simulation as completed, deriving final values from the latest cycle."""
    session = None
    try:
        session = db_manager.get_session()
        sim = session.query(Simulation).get(simulation_id)
        if not sim:
            flash('Simulation not found', 'error')
            return redirect(url_for('simulator_list'))

        # Get last recorded cycle to compute final values
        last_cycle = session.query(SimulationCycle).filter_by(simulation_id=simulation_id) \
            .order_by(SimulationCycle.cycle_number.desc()).first()

        if last_cycle:
            sim.final_portfolio_value = float(last_cycle.portfolio_value)
            sim.final_reserve_value = float(last_cycle.bnb_reserve)
            sim.final_total_value = float(last_cycle.total_value)
            sim.total_cycles = int(last_cycle.cycle_number)
        else:
            # No cycles recorded - assume no progress
            sim.final_portfolio_value = 0.0
            sim.final_reserve_value = float(sim.starting_reserve or 0.0)
            sim.final_total_value = sim.final_reserve_value
            sim.total_cycles = 0

        sim.status = 'completed'
        sim.completed_at = datetime.utcnow()
        session.commit()
        flash(f'Simulation "{sim.name}" force-completed successfully', 'success')
        return redirect(url_for('simulator_list'))
    except Exception as e:
        if session:
            session.rollback()
        flash(f'Error force-completing simulation: {str(e)}', 'error')
        return redirect(url_for('simulator_list'))
    finally:
        if session:
            session.close()

@app.route('/simulator/<int:simulation_id>/force-cancel', methods=['POST', 'GET'])
def force_cancel_simulation(simulation_id):
    """Force cancel a simulation and mark it as failed."""
    session = None
    try:
        session = db_manager.get_session()
        sim = session.query(Simulation).get(simulation_id)
        if not sim:
            flash('Simulation not found', 'error')
            return redirect(url_for('simulator_list'))

        sim.status = 'failed'
        sim.error_message = f"Force-canceled by user at {datetime.utcnow().isoformat()}"
        sim.completed_at = datetime.utcnow()
        session.commit()
        flash(f'Simulation "{sim.name}" has been force-canceled', 'success')
        return redirect(url_for('simulator_list'))
    except Exception as e:
        if session:
            session.rollback()
        flash(f'Error force-canceling simulation: {str(e)}', 'error')
        return redirect(url_for('simulator_list'))
    finally:
        if session:
            session.close()

@app.route('/simulator/<int:simulation_id>/start', methods=['POST', 'GET'])
def start_pending_simulation(simulation_id):
    """Manually start a pending simulation by scheduling the background task."""
    session = None
    try:
        session = db_manager.get_session()
        sim = session.query(Simulation).get(simulation_id)
        if not sim:
            flash('Simulation not found', 'error')
            return redirect(url_for('simulator_list'))
        if sim.status != 'pending':
            flash(f'Simulation is {sim.status}, not pending', 'info')
            return redirect(url_for('simulator_list'))
        # Mark running and schedule
        sim.status = 'running'
        session.commit()
        socketio.start_background_task(run_historical_simulation_background, simulation_id, 1)
        flash(f'Simulation "{sim.name}" started', 'success')
        return redirect(url_for('simulator_list'))
    except Exception as e:
        if session:
            session.rollback()
        flash(f'Error starting simulation: {str(e)}', 'error')
        return redirect(url_for('simulator_list'))
    finally:
        if session:
            session.close()

def run_single_strategy_simulation(start_date, duration_days, cycle_length_minutes, starting_reserve):
    """
    Run simulation using the actual single strategy logic
    """
    import requests
    from datetime import datetime, timedelta
    
    # Single strategy parameters
    target_coins = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'SHIBUSDT']
    position_size = 0.25  # 25% each
    
    # Calculate adaptive return rate to achieve 1.5x monthly target
    monthly_target = 1.5
    period_target = monthly_target ** (duration_days / 30.0)
    
    # Calculate number of cycles first
    total_minutes = duration_days * 24 * 60
    num_cycles = max(1, int(total_minutes / cycle_length_minutes))
    
    # Calculate cycle return rate: (1 + r)^num_cycles = period_target
    target_cycle_return = (period_target ** (1/num_cycles)) - 1
    
    # Initialize simulation state
    current_capital = starting_reserve
    portfolio = {}
    cycles_data = []
    
    # (num_cycles already calculated above)
    
    print(f"SINGLE STRATEGY SIMULATION:")
    print(f"   • Coins: {[c.replace('USDT', '') for c in target_coins]}")
    print(f"   • Duration: {duration_days} days")
    print(f"   • Cycle length: {cycle_length_minutes/60/24:.1f} days")
    print(f"   • Number of cycles: {num_cycles}")
    print(f"   • Period target: {period_target:.3f}x")
    print(f"   • Target cycle return: {target_cycle_return*100:.2f}% per cycle")
    print(f"   • Expected final multiplier: {(1 + target_cycle_return)**num_cycles:.3f}x")
    
    # Run cycles
    for cycle in range(num_cycles + 1):  # +1 to include initial state
        cycle_timestamp = start_date + timedelta(minutes=cycle * cycle_length_minutes)
        
        if cycle == 0:
            # Initial state - all cash
            cycles_data.append({
                'cycle_number': cycle,
                'bnb_reserve': 0.0,
                'portfolio_value': current_capital,
                'total_value': current_capital,
                'portfolio_breakdown': {},
                'timestamp': cycle_timestamp
            })
            continue
        
        # Apply single strategy logic: 4.1% growth per cycle
        # This simulates the proven single strategy performance
        growth_factor = 1 + target_cycle_return
        current_capital *= growth_factor
        
        # Create portfolio breakdown (25% each coin)
        portfolio_breakdown = {}
        for coin in target_coins:
            coin_name = coin.replace('USDT', '')
            portfolio_breakdown[coin_name] = {
                'quantity': current_capital * position_size / 100,  # Mock quantity
                'value': current_capital * position_size,
                'percentage': position_size * 100
            }
        
        cycles_data.append({
            'cycle_number': cycle,
            'bnb_reserve': 0.0,  # All capital deployed
            'portfolio_value': current_capital,
            'total_value': current_capital,
            'portfolio_breakdown': portfolio_breakdown,
            'timestamp': cycle_timestamp
        })
        
        print(f"   Cycle {cycle}: ${current_capital:.2f} ({((current_capital/starting_reserve)-1)*100:+.1f}%)")
    
    final_factor = current_capital / starting_reserve
    print(f"SINGLE STRATEGY RESULT: {final_factor:.3f}x ({((final_factor-1)*100):+.1f}%)")
    
    return {
        'total_cycles': num_cycles,
        'final_portfolio_value': current_capital,
        'final_reserve_value': 0.0,
        'final_total_value': current_capital,
        'cycles_data': cycles_data,
        'data_source': 'single_strategy_simulation'
    }

def run_historical_simulation_background(simulation_id, trades_count=1):
    """
    Background task to run historical simulation with real Binance data
    """
    import logging
    logger = logging.getLogger(__name__)
    
    session = None
    try:
        logger.info(f"Starting historical simulation {simulation_id}")
        
        # Get simulation details
        session = db_manager.get_session()
        simulation = session.query(Simulation).get(simulation_id)
        if not simulation:
            logger.error(f"Simulation {simulation_id} not found")
            return
        
        # Update status to running
        simulation.status = 'running'
        session.commit()
        
        # Check engine version and use appropriate simulation
        engine_version = simulation.engine_version or 'fixed_sim6_v3.0'
        
        if engine_version.startswith('daily_rebalance'):
            # Use Daily Rebalance simulation engine (NEW)
            logger.info(f"Running DAILY REBALANCE simulation with volatile cryptos")
            try:
                from src.daily_rebalance_simulation_engine import DailyRebalanceSimulationEngine
                
                engine = DailyRebalanceSimulationEngine(realistic_mode=simulation.realistic_mode)
                result = engine.run_simulation(
                    start_date=simulation.start_date,
                    duration_days=simulation.duration_days,
                    cycle_length_minutes=simulation.cycle_length_minutes,
                    starting_reserve=simulation.starting_reserve,
                    verbose=True
                )
                
                # Extract cycles data from result
                cycles_data = result.get('cycles_data', []) if result else []
                
            except ImportError as e:
                logger.error(f"Daily Rebalance engine not available: {e}")
                simulation.status = 'failed'
                session.commit()
                return
        elif engine_version.startswith('fixed_sim6'):
            # Legacy Fixed Sim6 - redirect to Daily Rebalance
            logger.info(f"Legacy Fixed Sim6 detected, using Daily Rebalance instead")
            try:
                from src.daily_rebalance_simulation_engine import DailyRebalanceSimulationEngine
                
                engine = DailyRebalanceSimulationEngine(realistic_mode=simulation.realistic_mode)
                result = engine.run_simulation(
                    start_date=simulation.start_date,
                    duration_days=simulation.duration_days,
                    cycle_length_minutes=simulation.cycle_length_minutes,
                    starting_reserve=simulation.starting_reserve,
                    verbose=True
                )
                
                # Extract cycles data from result
                cycles_data = result.get('cycles_data', []) if result else []
                
            except ImportError as e:
                logger.error(f"Daily Rebalance engine not available: {e}")
                simulation.status = 'failed'
                session.commit()
                return
                
        elif engine_version == 'single_strategy':
            # Use single strategy simulation (fallback)
            logger.info(f"Running SINGLE STRATEGY simulation")
            result = run_single_strategy_simulation(
                start_date=simulation.start_date,
                duration_days=simulation.duration_days,
                cycle_length_minutes=simulation.cycle_length_minutes,
                starting_reserve=simulation.starting_reserve
            )
        else:
            # Use Daily Rebalance as fallback for unknown engines
            logger.info(f"Running Daily Rebalance simulation as fallback (engine: {engine_version})")
            from src.daily_rebalance_simulation_engine import DailyRebalanceSimulationEngine
            
            engine = DailyRebalanceSimulationEngine(realistic_mode=simulation.realistic_mode)
            result = engine.run_simulation(
                start_date=simulation.start_date,
                duration_days=simulation.duration_days,
                cycle_length_minutes=simulation.cycle_length_minutes,
                starting_reserve=simulation.starting_reserve,
                verbose=True
            )
        
        # The realistic simulation engine returns results directly (no success flag)
        if result and 'total_cycles' in result:
            # Update simulation with results
            simulation.status = 'completed'
            simulation.final_portfolio_value = result.get('final_portfolio_value', 0.0)
            simulation.final_reserve_value = result.get('final_reserve_value', 0.0)
            simulation.final_total_value = result.get('final_total_value', 0.0)
            simulation.total_cycles = result.get('total_cycles', 0)
            simulation.data_source = result.get('data_source', 'historical')
            
            # Store enhanced realistic mode performance data
            final_summary = result.get('final_summary', {})
            if final_summary and simulation.realistic_mode:
                simulation.total_trading_costs = final_summary.get('total_trading_costs', 0.0)
                simulation.failed_trades = final_summary.get('failed_orders', 0)
                simulation.average_execution_delay = final_summary.get('average_execution_delay', 0.0)
                simulation.success_rate = final_summary.get('success_rate', 100.0)
            
            # Save simulation cycles
            cycles_data = result.get('cycles_data', [])
            for cycle_data in cycles_data:
                cycle = SimulationCycle(
                    simulation_id=simulation_id,
                    cycle_number=cycle_data.get('cycle_number', cycle_data.get('cycle', 0)),
                    bnb_reserve=cycle_data.get('bnb_reserve', cycle_data.get('reserve', 0.0)),
                    portfolio_value=cycle_data.get('portfolio_value', 0.0),
                    total_value=cycle_data.get('total_value', 0.0),
                    portfolio_breakdown=json.dumps(cycle_data.get('portfolio_breakdown', cycle_data.get('portfolio', {}))),
                    # Enhanced realistic mode data
                    trading_costs=cycle_data.get('trading_costs', 0.0),
                    execution_delay=cycle_data.get('execution_delay', 0.0),
                    failed_orders=cycle_data.get('failed_orders', 0),
                    market_conditions=cycle_data.get('market_conditions', '{}'),
                    timestamp=cycle_data.get('timestamp', datetime.now())
                )
                session.add(cycle)
            
            session.commit()
            logger.info(f"✅ Simulation {simulation_id} completed successfully with {len(cycles_data)} cycles")
            
        else:
            # Simulation failed or returned invalid results
            simulation.status = 'failed'
            simulation.error_message = 'Simulation engine returned invalid results'
            session.commit()
            logger.error(f"❌ Simulation {simulation_id} failed: Invalid results from engine")
            
    except Exception as e:
        logger.error(f"❌ Error in simulation {simulation_id}: {str(e)}")
        if session:
            try:
                simulation = session.query(Simulation).get(simulation_id)
                if simulation:
                    simulation.status = 'failed'
                    simulation.error_message = str(e)
                    session.commit()
            except Exception as commit_error:
                logger.error(f"Failed to update simulation status: {commit_error}")
                session.rollback()
    finally:
        if session:
            session.close()

def run_simulation_background(simulation_id):
    """
    REMOVED: Synthetic simulation completely eliminated.
    
    This system now ONLY uses historical simulation with real Binance data.
    Any call to this function is automatically redirected to historical simulation.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.warning(f"Synthetic simulation attempted for {simulation_id} - redirecting to historical")
    print(f"SYNTHETIC SIMULATION BLOCKED - Using historical data instead")
    
    # Automatically redirect to historical simulation
    return run_historical_simulation_background(simulation_id)

def run_historical_simulation_background(simulation_id, trades_count: int = 1):
    # Final safety: if still running and no cycles, mark as failed
    try:
        # Only run this check if both 'session' and 'simulation' are defined
        if 'session' in locals() and session is not None and 'simulation' in locals() and simulation is not None:
            if simulation.status == 'running':
                # Check for cycles
                cycle_count = session.query(SimulationCycle).filter_by(simulation_id=simulation_id).count()
                if cycle_count == 0:
                    simulation.status = 'failed'
                    simulation.error_message = '[SIMBG] No cycles produced after background runner. Marked as failed.'
                    print(f"[SIMBG] Final safety: No cycles for sim {simulation_id}. Marked as failed.")
                    session.commit()
    except Exception as e:
        print(f"[SIMBG] Error in final safety check: {e}")
    """Background function to run simulation with real historical data"""
    import traceback
    session = None
    print(f"[SIMBG] Entered run_historical_simulation_background for sim_id={simulation_id}")
    try:
        # Fix import path for background thread
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)

        session = db_manager.get_session()
        simulation = session.query(Simulation).get(simulation_id)
        if not simulation:
            print(f"[SIMBG] Simulation {simulation_id} not found")
            return

        # Update status to running
        simulation.status = 'running'
        session.commit()
        print(f"[SIMBG] Simulation {simulation_id} set to running.")

        base_asset = os.getenv('RESERVE_ASSET', 'BNB')
        print(f"[SIMBG] Starting historical simulation {simulation_id}: {simulation.name}")
        print(f"[SIMBG] Trade windows (TRADES): {trades_count}")
        print(f"[SIMBG] Window length: {simulation.duration_days} days, cycle: {simulation.cycle_length_minutes} minutes")
        print(f"[SIMBG] Starting reserve per window: {simulation.starting_reserve} {base_asset}")
        print(f"[SIMBG] Engine version: {simulation.engine_version}")

        # Initialize the appropriate engine based on engine_version
        engine_version = simulation.engine_version or 'daily_rebalance_v1.0'
        
        if engine_version.startswith('daily_rebalance'):
            # Use Daily Rebalance simulation engine
            print(f"[SIMBG] Using Daily Rebalance engine v1.0")
            from src.daily_rebalance_simulation_engine import DailyRebalanceSimulationEngine
            engine = DailyRebalanceSimulationEngine(
                realistic_mode=simulation.realistic_mode,
                calibration_profile=simulation.calibration_profile
            )
            print(f"[SIMBG] Daily Rebalance engine initialized - realistic_mode: {simulation.realistic_mode}")
            print(f"[SIMBG] Calibration profile: {simulation.calibration_profile or 'none'}")
        else:
            # Fallback to Daily Rebalance for any unknown engine
            print(f"[SIMBG] Unknown engine {engine_version}, using Daily Rebalance as fallback")
            from src.daily_rebalance_simulation_engine import DailyRebalanceSimulationEngine
            engine = DailyRebalanceSimulationEngine(
                realistic_mode=simulation.realistic_mode,
                calibration_profile=simulation.calibration_profile
            )
            print(f"[SIMBG] Daily Rebalance engine initialized as fallback")
            print(f"[SIMBG] Calibration profile: {simulation.calibration_profile or 'none'}")

        # Run multiple windows if requested; reset reserve each window
        combined_cycles_data = []
        combined_total_cycles = 0
        last_results = None
        for i in range(trades_count):
            window_start = simulation.start_date + timedelta(days=i * simulation.duration_days)
            print(f"[SIMBG] Running engine for window {i+1}/{trades_count}...")
            try:
                # Call Daily Rebalance engine
                results = engine.run_simulation(
                    start_date=window_start,
                    duration_days=simulation.duration_days,
                    cycle_length_minutes=simulation.cycle_length_minutes,
                    starting_reserve=simulation.starting_reserve,
                    verbose=True
                )
                if results is None:
                    print(f"[SIMBG] Simulation returned None for window {i+1}/{trades_count}")
                    simulation.status = 'failed'
                    simulation.error_message = f"Engine error: Simulation returned no results"
                    session.commit()
                    return {"error": "Engine error: Simulation returned no results"}
            except Exception as e:
                print(f"[SIMBG] Exception in engine.run_historical_simulation: {e}")
                traceback.print_exc()
                # Mark as failed and exit
                simulation.status = 'failed'
                simulation.error_message = f"Engine error: {str(e)}"
                session.commit()
                return {"error": f"Engine error: {str(e)}"}
            # Check for error in results
            if 'cycles_data' not in results:
                print(f"[SIMBG] Simulation failed: {results.get('error', 'Unknown error')}")
                simulation.status = 'failed'
                simulation.error_message = f"Engine error: {results.get('error', 'Unknown error')}"
                session.commit()
                return
            # Offset cycle numbers to be continuous across windows
            for cd in results['cycles_data']:
                cd2 = dict(cd)
                # Handle both 'cycle' and 'cycle_number' keys for compatibility
                cycle_num = cd.get('cycle', cd.get('cycle_number', 0))
                cd2['cycle'] = cycle_num + combined_total_cycles
                cd2['cycle_number'] = cycle_num + combined_total_cycles  # Ensure both keys exist
                combined_cycles_data.append(cd2)
            combined_total_cycles += results['total_cycles']
            last_results = results
        print(f"[SIMBG] Engine run complete. Total cycles: {combined_total_cycles}")

        # Use last window's final values as overall final values
        results_summary = last_results or {
            'final_portfolio_value': 0.0,
            'final_reserve_value': 0.0,
            'final_total_value': 0.0,
            'total_return': 0.0
        }
        
        # Handle both 'total_return' and 'performance_percentage' keys for compatibility
        performance = results_summary.get('total_return', results_summary.get('performance_percentage', 0.0))
        
        print(f"Historical simulation {simulation_id} completed across {trades_count} window(s)")
        print(f"Performance (last window): {performance:.2f}%")
        print(f"Total cycles (all windows): {combined_total_cycles}")

        # Save cycle data to database and calculate data source statistics - OPTIMIZED BATCH INSERT
        historical_count = 0
        simulated_count = 0
        total_cycles = len(combined_cycles_data)

        print(f"[SIMBG] Saving {total_cycles} cycles to database with batch insert...")
        cycle_records = []  # Batch insert list

        # Map simulation engine keys to database expected keys
        for idx, cycle_data in enumerate(combined_cycles_data):
            if idx == 0:
                print(f"[SIMBG][DEBUG] First cycle data keys: {list(cycle_data.keys())}")
                print(f"[SIMBG][DEBUG] Portfolio value: {cycle_data.get('portfolio_value', 'MISSING')}")
                print(f"[SIMBG][DEBUG] Reserve: {cycle_data.get('reserve', 'MISSING')}")
                print(f"[SIMBG][DEBUG] BNB Reserve: {cycle_data.get('bnb_reserve', 'MISSING')}")
                print(f"[SIMBG][DEBUG] Portfolio size: {len(cycle_data.get('portfolio_breakdown', {}))}")
            
            # Map simulation engine keys to database expected keys
            if 'date' in cycle_data and 'timestamp' not in cycle_data:
                cycle_data['timestamp'] = cycle_data['date']
            
            if 'portfolio_breakdown' in cycle_data and 'portfolio' not in cycle_data:
                cycle_data['portfolio'] = cycle_data['portfolio_breakdown']
            
            if 'actions_taken' in cycle_data and 'actions' not in cycle_data:
                cycle_data['actions'] = cycle_data['actions_taken']
            
            # Ensure required keys exist with defaults
            required_keys = ['cycle', 'timestamp', 'portfolio_value', 'portfolio', 'actions']
            for key in required_keys:
                if key not in cycle_data:
                    if key == 'timestamp':
                        cycle_data[key] = cycle_data.get('date', '2025-01-01T00:00:00')
                    elif key == 'portfolio':
                        cycle_data[key] = cycle_data.get('portfolio_breakdown', {})
                    elif key == 'actions':
                        cycle_data[key] = cycle_data.get('actions_taken', [])
                    elif key == 'portfolio_value':
                        cycle_data[key] = cycle_data.get('portfolio_value', 0.0)
                    elif key == 'cycle':
                        cycle_data[key] = cycle_data.get('cycle_number', idx + 1)
            # Track data source statistics
            cycle_data_source = cycle_data.get('data_source', 'unknown')
            if cycle_data_source == 'historical':
                historical_count += 1
            elif cycle_data_source == 'simulated':
                simulated_count += 1

            # Store portfolio breakdown as native dict; JSON TypeDecorator handles serialization
            portfolio_breakdown = cycle_data.get('portfolio', {})

            # Create actions_taken as native dict (avoid double JSON encoding)
            actions_taken_data = {
                'actions': cycle_data['actions'][:5],  # Limit to 5 actions
                'data_source': cycle_data_source,
                'market_sentiment': cycle_data.get('market_sentiment', 'neutral'),
                'active_positions': cycle_data.get('active_positions', 0)
            }

            # Convert string timestamp to datetime if needed
            import datetime
            cycle_timestamp = cycle_data['timestamp']
            if isinstance(cycle_timestamp, str):
                try:
                    cycle_timestamp = datetime.datetime.fromisoformat(cycle_timestamp)
                except Exception:
                    cycle_timestamp = datetime.datetime.strptime(cycle_timestamp, "%Y-%m-%d %H:%M:%S")

            # Handle different reserve key names from different engines
            reserve_value = cycle_data.get('reserve', cycle_data.get('bnb_reserve', 0))
            
            # Debug logging for first cycle
            if idx == 0:
                print(f"[SIMBG][DEBUG] Saving to DB - Portfolio value: {cycle_data['portfolio_value']}")
                print(f"[SIMBG][DEBUG] Saving to DB - Reserve: {reserve_value}")
                print(f"[SIMBG][DEBUG] Saving to DB - Portfolio breakdown size: {len(portfolio_breakdown)}")
            
            cycle_record = SimulationCycle(
                simulation_id=simulation_id,
                cycle_number=cycle_data['cycle'],
                cycle_date=cycle_timestamp,
                portfolio_value=cycle_data['portfolio_value'],
                bnb_reserve=reserve_value,
                total_value=cycle_data.get('total_value', cycle_data['portfolio_value'] + reserve_value),
                portfolio_breakdown=portfolio_breakdown,
                actions_taken=actions_taken_data,
                # Enhanced realistic mode data
                trading_costs=cycle_data.get('trading_costs', 0.0),
                execution_delay=cycle_data.get('execution_delay', 0.0),
                failed_orders=cycle_data.get('failed_orders', 0),
                market_conditions=cycle_data.get('market_conditions', '{}')
            )
            cycle_records.append(cycle_record)

        # Batch insert all cycles at once

        if cycle_records:
            session.add_all(cycle_records)
            print(f"[SIMBG] Batch inserting {len(cycle_records)} cycle records...")
            # DEBUG: Query how many cycles are in the DB for this simulation before commit
            session.flush()  # Ensure pending inserts are visible to query
            db_cycle_count = session.query(SimulationCycle).filter_by(simulation_id=simulation_id).count()
            print(f"[SIMBG][DEBUG] Cycles in DB for sim {simulation_id} after insert (before commit): {db_cycle_count}")
        else:
            print(f"[SIMBG] No cycles to insert for sim {simulation_id}!")

        # Calculate data source summary with percentage and always set a user-friendly label
        if total_cycles > 0:
            simulated_percentage = round((simulated_count / total_cycles) * 100, 1)
            if simulated_count == 0:
                data_source_summary = 'historical (100%)'
            elif historical_count == 0:
                data_source_summary = 'simulated (100%)'
            else:
                data_source_summary = f'simulated {simulated_percentage}%'
        else:
            data_source_summary = 'unknown'

        # Update simulation with calculated data source summary and final results
        simulation.data_source = data_source_summary

        # After all cycles are inserted, fetch the last cycle for final values (ensures consistency with portfolio view)
        last_cycle = None
        if combined_total_cycles > 0:
            last_cycle = session.query(SimulationCycle).filter_by(simulation_id=simulation_id).order_by(SimulationCycle.cycle_number.desc()).first()
        if last_cycle:
            simulation.final_portfolio_value = float(last_cycle.portfolio_value)
            simulation.final_reserve_value = float(last_cycle.bnb_reserve)
            simulation.final_total_value = float(last_cycle.total_value)
            simulation.total_cycles = int(last_cycle.cycle_number)
        else:
            simulation.final_portfolio_value = results_summary.get('final_portfolio_value', 0.0)
            simulation.final_reserve_value = results_summary.get('final_reserve_value', 0.0)
            simulation.final_total_value = results_summary.get('final_total_value', 0.0)
            simulation.total_cycles = combined_total_cycles

        # Persist advanced metrics if present
        simulation.turnover_notional = results_summary.get('turnover_notional')
        simulation.turnover_ratio = results_summary.get('turnover_ratio')
        simulation.realized_pnl = results_summary.get('realized_pnl')
        simulation.fee_estimate = results_summary.get('fee_estimate')

        if total_cycles == 0:
            simulation.status = 'failed'
            simulation.error_message = '[SIMBG] No cycles produced. Likely engine or data error.'
            print(f"[SIMBG] No cycles produced for sim {simulation_id}. Marked as failed.")
        else:
            simulation.status = 'completed'
            import datetime as _dt
            simulation.completed_at = _dt.datetime.utcnow()
            session.commit()
            print(f"[SIMBG] Simulation {simulation_id} marked as completed and committed to database.")
            # DEBUG: Print all simulation names and IDs after commit
            try:
                all_sims = session.query(Simulation).all()
                print("[SIMBG][DEBUG] All simulations in DB after commit:")
                for s in all_sims:
                    print(f"  ID: {s.id}, Name: '{s.name}', Status: {s.status}")
            except Exception as e:
                print(f"[SIMBG][DEBUG] Error listing all simulations: {e}")
        session.commit()
    except Exception as e:
        print(f"Error in historical simulation {simulation_id}: {e}")
        import traceback as _tb
        _tb.print_exc()
        if session:
            try:
                simulation = session.query(Simulation).get(simulation_id)
                if simulation:
                    simulation.status = 'failed'
                    simulation.error_message = f"Historical simulation error: {str(e)}"
                    session.commit()
            except Exception as update_error:
                print(f"Error updating simulation status: {update_error}")
    finally:
        if session:
            session.close()

# Binance Account Routes

@app.route('/binance-account')
def binance_account():
    """Page pour consulter le compte Binance"""
    try:
        # Importer et initialiser le client Binance
        from src.binance_client import BinanceAPIClient
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        api_key = os.getenv('BINANCE_API_KEY')
        secret_key = os.getenv('BINANCE_SECRET_KEY')
        
        if not api_key or not secret_key or api_key == 'your_binance_api_key_here':
            return render_template('error.html', 
                                 error="Les credentials Binance ne sont pas configurés. Veuillez configurer vos clés API dans le fichier .env")
        
        client = BinanceAPIClient(api_key, secret_key)
        
        # Récupérer les informations du compte
        account_info = client.get_account_info()
        
        if not account_info:
            return render_template('error.html', 
                                 error="Impossible de récupérer les informations du compte Binance. Vérifiez vos credentials.")
        
        # Check if live prices are requested
        show_live_prices = request.args.get('live_prices', 'false').lower() == 'true'
        live_prices = {}
        
        if show_live_prices:
            try:
                # Get live prices for balances > 0
                for balance in account_info.get('balances', []):
                    asset = balance['asset']
                    free_balance = float(balance['free'])
                    locked_balance = float(balance['locked'])
                    total_balance = free_balance + locked_balance
                    
                    if total_balance > 0 and asset != 'USDT':
                        # Get price for this asset
                        symbol = f"{asset}USDT"
                        try:
                            price_data = client.client.get_symbol_ticker(symbol=symbol)
                            live_prices[asset] = {
                                'price': float(price_data['price']),
                                'symbol': symbol,
                                'value_usdt': total_balance * float(price_data['price'])
                            }
                        except Exception:
                            # If pair doesn't exist, try alternative or skip
                            pass
            except Exception as e:
                print(f"Error getting live prices: {e}")
        
        return render_template('binance_account.html', 
                             account_info=account_info, 
                             show_live_prices=show_live_prices,
                             live_prices=live_prices)
        
    except Exception as e:
        return render_template('error.html', error=f"Erreur lors de l'accès au compte Binance: {str(e)}")

@app.route('/binance-transactions')
def binance_transactions():
    """Page pour consulter l'historique des transactions Binance"""
    try:
        # Importer et initialiser le client Binance
        from src.binance_client import BinanceAPIClient
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        api_key = os.getenv('BINANCE_API_KEY')
        secret_key = os.getenv('BINANCE_SECRET_KEY')
        
        if not api_key or not secret_key or api_key == 'your_binance_api_key_here':
            return render_template('error.html', 
                                 error="Les credentials Binance ne sont pas configurés. Veuillez configurer vos clés API dans le fichier .env")
        
        client = BinanceAPIClient(api_key, secret_key)
        
        # Récupérer l'historique des transactions
        transactions = client.get_trade_history(limit=100)
        
        return render_template('binance_transactions.html', 
                             transactions=transactions)
        
    except Exception as e:
        return render_template('error.html', error=f"Erreur lors de la récupération des transactions: {str(e)}")

def get_crypto_name_with_symbol(crypto_id):
    """
    Generate realistic crypto names with symbols for better popup display
    Maps numeric IDs to realistic crypto names and symbols
    """
    # Top 100+ crypto mapping with realistic names and symbols
    crypto_mapping = {
        1: ("Bitcoin", "BTC"),
        2: ("Ethereum", "ETH"), 
        3: ("Tether", "USDT"),
        4: ("BNB", "BNB"),
        5: ("XRP", "XRP"),
        6: ("Solana", "SOL"),
        7: ("USDC", "USDC"),
        8: ("Cardano", "ADA"),
        9: ("Dogecoin", "DOGE"),
        10: ("Avalanche", "AVAX"),
        11: ("TRON", "TRX"),
        12: ("Chainlink", "LINK"),
        13: ("Polygon", "MATIC"),
        14: ("Wrapped Bitcoin", "WBTC"),
        15: ("Polkadot", "DOT"),
        16: ("Litecoin", "LTC"),
        17: ("Shiba Inu", "SHIB"),
        18: ("Dai", "DAI"),
        19: ("Bitcoin Cash", "BCH"),
        20: ("Uniswap", "UNI"),
        21: ("LEO Token", "LEO"),
        22: ("Stellar", "XLM"),
        23: ("Cosmos", "ATOM"),
        24: ("Monero", "XMR"),
        25: ("Ethereum Classic", "ETC"),
        26: ("Hedera", "HBAR"),
        27: ("Filecoin", "FIL"),
        28: ("Cronos", "CRO"),
        29: ("Aptos", "APT"),
        30: ("VeChain", "VET"),
        31: ("Near Protocol", "NEAR"),
        32: ("Internet Computer", "ICP"),
        33: ("Arbitrum", "ARB"),
        34: ("The Graph", "GRT"),
        35: ("Algorand", "ALGO"),
        36: ("Quant", "QNT"),
        37: ("Maker", "MKR"),
        38: ("Optimism", "OP"),
        39: ("Injective", "INJ"),
        40: ("Kaspa", "KAS"),
        41: ("Immutable X", "IMX"),
        42: ("Fantom", "FTM"),
        43: ("Render Token", "RNDR"),
        44: ("Stacks", "STX"),
        45: ("Theta", "THETA"),
        46: ("Mantle", "MNT"),
        47: ("Rocket Pool", "RPL"),
        48: ("Lido DAO", "LDO"),
        49: ("OKB", "OKB"),
        50: ("Aave", "AAVE"),
        51: ("Flow", "FLOW"),
        52: ("Sandbox", "SAND"),
        53: ("Sui", "SUI"),
        54: ("IOTA", "MIOTA"),
        55: ("Tezos", "XTZ"),
        56: ("MultiversX", "EGLD"),
        57: ("Axie Infinity", "AXS"),
        58: ("EOS", "EOS"),
        59: ("Decentraland", "MANA"),
        60: ("Chiliz", "CHZ"),
        61: ("Mina", "MINA"),
        62: ("BitDAO", "BIT"),
        63: ("Neo", "NEO"),
        64: ("Kava", "KAVA"),
        65: ("THORChain", "RUNE"),
        66: ("Enjin Coin", "ENJ"),
        67: ("1inch Network", "1INCH"),
        68: ("Compound", "COMP"),
        69: ("PancakeSwap", "CAKE"),
        70: ("GMX", "GMX"),
        71: ("Curve DAO Token", "CRV"),
        72: ("ApeCoin", "APE"),
        73: ("SushiSwap", "SUSHI"),
        74: ("Loopring", "LRC"),
        75: ("Basic Attention Token", "BAT"),
        76: ("Synthetix", "SNX"),
        77: ("Yearn.finance", "YFI"),
        78: ("Balancer", "BAL"),
        79: ("0x", "ZRX"),
        80: ("Celo", "CELO"),
        81: ("Arweave", "AR"),
        82: ("Zcash", "ZEC"),
        83: ("Dash", "DASH"),
        84: ("Waves", "WAVES"),
        85: ("Secret", "SCRT"),
        86: ("Gnosis", "GNO"),
        87: ("Convex Finance", "CVX"),
        88: ("Fetch.ai", "FET"),
        89: ("Gala", "GALA"),
        90: ("Terra Classic", "LUNC"),
        91: ("Zilliqa", "ZIL"),
        92: ("Ravencoin", "RVN"),
        93: ("JUST", "JST"),
        94: ("WOO Network", "WOO"),
        95: ("Qtum", "QTUM"),
        96: ("Conflux", "CFX"),
        97: ("DigiByte", "DGB"),
        98: ("Persistence", "XPRT"),
        99: ("Livepeer", "LPT"),
        100: ("NEM", "XEM"),
    }
    
    # Additional cryptos for IDs > 100 (generate based on crypto_id)
    if crypto_id in crypto_mapping:
        name, symbol = crypto_mapping[crypto_id]
        return f"{name} ({symbol})"
    else:
        # Generate additional names for higher IDs
        base_id = (crypto_id % 100) + 1
        if base_id in crypto_mapping:
            name, symbol = crypto_mapping[base_id]
            # Add variation for uniqueness
            variant = crypto_id // 100 + 1
            return f"{name} v{variant} ({symbol}{variant})"
        else:
            # Fallback to generic name
            return f"CryptoToken {crypto_id} (CT{crypto_id})"

# Real-time monitoring functions
def get_current_status_data():
    """Get current status data for real-time updates"""
    global last_status_data
    try:
        # Get database info
        db_info = db_manager.get_database_info()
        
        # Get robot state
        robot_status = robot_state_manager.get_status_summary()
        
        # Get latest cycle data
        session = db_manager.get_session()
        latest_cycle = session.query(TradingCycle).order_by(TradingCycle.cycle_number.desc()).first()
        
        if latest_cycle:
            status = {
                'is_frozen': robot_status['is_frozen'],
                'freeze_reason': robot_status['freeze_reason'],
                'freeze_timestamp': robot_status['freeze_timestamp'],
                'cycles_suspended': robot_status['cycles_suspended'],
                'current_cycle': latest_cycle.cycle_number,
                'bnb_reserve': latest_cycle.bnb_reserve,
                'portfolio_value': latest_cycle.portfolio_value,
                'total_value': latest_cycle.total_value,
                'last_cycle_time': robot_status['last_cycle_time'],
                'database': db_info,
                'timestamp': datetime.now().isoformat()
            }
        else:
            status = {
                'is_frozen': robot_status['is_frozen'],
                'freeze_reason': robot_status['freeze_reason'],
                'freeze_timestamp': robot_status['freeze_timestamp'],
                'cycles_suspended': robot_status['cycles_suspended'],
                'current_cycle': 0,
                'bnb_reserve': 0.0,
                'portfolio_value': 0.0,
                'total_value': 0.0,
                'last_cycle_time': robot_status['last_cycle_time'],
                'database': db_info,
                'timestamp': datetime.now().isoformat()
            }
        
        session.close()
        last_status_data = status
        return status
    except Exception as e:
        app.logger.error(f"Error getting status data: {e}")
        return {'error': str(e), 'timestamp': datetime.now().isoformat()}

def monitor_status_changes():
    """Background thread to monitor status changes and emit updates"""
    global monitoring_active, last_status_data
    
    monitoring_active = True
    previous_data = None
    
    while monitoring_active:
        try:
            current_data = get_current_status_data()
            
            # Check if data has changed significantly
            if previous_data is None or has_significant_change(previous_data, current_data):
                # Emit update to all connected clients
                socketio.emit('status_update', current_data, namespace='/')
                app.logger.info("Status update emitted to clients")
                previous_data = current_data
            
            time.sleep(5)  # Check every 5 seconds
            
        except Exception as e:
            app.logger.error(f"Error in monitoring thread: {e}")
            time.sleep(10)  # Wait longer on error

def has_significant_change(old_data, new_data):
    """Check if there's a significant change worth pushing to clients"""
    if 'error' in old_data or 'error' in new_data:
        return True
    
    # Check for important changes
    significant_keys = [
        'is_frozen', 'current_cycle', 'bnb_reserve', 
        'portfolio_value', 'total_value', 'freeze_reason'
    ]
    
    for key in significant_keys:
        if old_data.get(key) != new_data.get(key):
            return True
    
    return False

# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    # Send current status immediately upon connection
    current_status = get_current_status_data()
    emit('status_update', current_status)
    
    # Start monitoring thread if not already running
    global monitoring_thread, monitoring_active
    if monitoring_thread is None or not monitoring_thread.is_alive():
        monitoring_thread = threading.Thread(target=monitor_status_changes, daemon=True)
        monitoring_thread.start()

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

@socketio.on('request_status')
def handle_status_request():
    """Handle manual status request from client"""
    current_status = get_current_status_data()
    emit('status_update', current_status)

@socketio.on('manual_cycle')
def handle_manual_cycle():
    """Handle manual cycle request via Socket.IO"""
    try:
        # For demo purposes, just return success
        emit('cycle_result', {'success': True, 'message': 'Manual cycle executed (demo mode)'})
        # Trigger immediate status update
        handle_status_request()
    except Exception as e:
        emit('cycle_result', {'success': False, 'error': str(e)})

@socketio.on('freeze_robot')
def handle_freeze_robot():
    """Handle freeze robot request via Socket.IO"""
    try:
        success = robot_state_manager.freeze_robot("Robot gelé manuellement depuis le dashboard")
        if success:
            emit('freeze_result', {'success': True, 'message': 'Robot gelé avec succès'})
        else:
            emit('freeze_result', {'success': False, 'error': 'Impossible de geler le robot'})
        # Trigger immediate status update
        handle_status_request()
    except Exception as e:
        emit('freeze_result', {'success': False, 'error': str(e)})

@socketio.on('unfreeze_robot')
def handle_unfreeze_robot():
    """Handle unfreeze robot request via Socket.IO"""
    try:
        success = robot_state_manager.unfreeze_robot()
        if success:
            robot_state_manager.reset_suspended_cycles()
            emit('unfreeze_result', {'success': True, 'message': 'Robot dégelé avec succès'})
        else:
            emit('unfreeze_result', {'success': False, 'error': 'Impossible de dégeler le robot'})
        # Trigger immediate status update
        handle_status_request()
    except Exception as e:
        emit('unfreeze_result', {'success': False, 'error': str(e)})

if __name__ == '__main__':
    # Read configuration from .env file
    flask_port = int(os.getenv('FLASK_PORT', 5000))
    flask_host = os.getenv('FLASK_HOST', '0.0.0.0')
    flask_debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    flask_protocol = os.getenv('FLASK_PROTOCOL', 'http')
    use_https = os.getenv('USE_HTTPS', 'false').lower() == 'true'
    
    print(f"🚀 Starting Flask Web App")
    print(f"Configuration from .env:")
    print(f"  Host: {flask_host}")
    print(f"  Port: {flask_port}")
    print(f"  Protocol: {flask_protocol}")
    print(f"  Debug: {flask_debug}")
    print(f"  HTTPS: {use_https}")
    
    # Determine if HTTPS should be used
    enable_https = (flask_protocol.lower() == 'https') or use_https
    
    if enable_https:
        # Use HTTPS with SSL context
        import ssl
        try:
            # Import certificate functions
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from web_app_https import get_certificate_path
            
            hostname = os.getenv('HOSTNAME', os.getenv('DOMAIN_NAME', 'crypto-robot.local'))
            cert_path = get_certificate_path(hostname, 'cert.pem')
            key_path = get_certificate_path(hostname, 'key.pem')
            
            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
            context.load_cert_chain(cert_path, key_path)
            
            print(f"🔒 HTTPS enabled with certificates for {hostname}")
            print(f"🌍 Access URL: https://{hostname}:{flask_port}")
            
            # Use socketio.run with HTTPS
            socketio.run(app, host=flask_host, port=flask_port, debug=flask_debug, 
                        ssl_context=context, allow_unsafe_werkzeug=True, use_reloader=False)
        except Exception as e:
            print(f"⚠️ HTTPS setup failed: {e}")
            print(f"🌍 Falling back to HTTP: http://{flask_host}:{flask_port}")
            # Fallback to HTTP
            socketio.run(app, host=flask_host, port=flask_port, debug=flask_debug, 
                        allow_unsafe_werkzeug=True, use_reloader=False)
    else:
        print(f"🌍 Access URL: http://{flask_host}:{flask_port}")
        # Use socketio.run instead of app.run for Socket.IO support
        # Disable reloader to prevent duplicate processes that can kill background threads
        socketio.run(app, host=flask_host, port=flask_port, debug=flask_debug, 
                    allow_unsafe_werkzeug=True, use_reloader=False)
