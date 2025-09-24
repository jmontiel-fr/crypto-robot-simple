#!/bin/bash

# Portfolio management integration script for crypto-robot
# This script provides portfolio management functionality for both direct and containerized execution
# Usage: ./scripts/portfolio-manager.sh <command> [options]

set -e  # Exit on any error

# Configuration
APP_DIR="/opt/crypto-robot"
PYTHON_CMD="python3"
CONTAINER_NAME="crypto-robot-app"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  create-fresh         - Create fresh portfolio (comprehensive cleanup)"
    echo "  create-fresh-fast    - Create fresh portfolio (fast mode)"
    echo "  cleanup-only         - Only perform cleanup without portfolio creation"
    echo "  status               - Show portfolio status"
    echo "  validate             - Validate portfolio configuration"
    echo "  help                 - Show this help message"
    echo ""
    echo "Options:"
    echo "  --container          - Execute in running container"
    echo "  --direct             - Execute directly (default)"
    echo "  --starting-capital N - Set starting capital amount"
    echo "  --full-cleanup       - Force comprehensive cleanup"
    echo "  --fast               - Use fast mode"
    echo ""
    echo "Examples:"
    echo "  $0 create-fresh                           # Create fresh portfolio directly"
    echo "  $0 create-fresh --container              # Create fresh portfolio in container"
    echo "  $0 create-fresh-fast --starting-capital 200  # Fast mode with custom capital"
    echo "  $0 cleanup-only                         # Only cleanup simulation data"
    echo "  $0 status --container                   # Check portfolio status in container"
    echo ""
    echo "Environment Variables:"
    echo "  STARTING_CAPITAL     - Starting capital amount (default: 100)"
    echo "  FULL_CLEANUP         - Enable comprehensive cleanup (true/false)"
    echo "  DEFAULT_CALIBRATION_PROFILE - Calibration profile (default: moderate_realistic)"
}

# Function to parse command line arguments
parse_args() {
    COMMAND=""
    EXECUTION_MODE="direct"
    STARTING_CAPITAL=""
    CLEANUP_MODE=""
    FAST_MODE=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --container)
                EXECUTION_MODE="container"
                shift
                ;;
            --direct)
                EXECUTION_MODE="direct"
                shift
                ;;
            --starting-capital)
                STARTING_CAPITAL="$2"
                shift 2
                ;;
            --full-cleanup)
                CLEANUP_MODE="full"
                shift
                ;;
            --fast)
                FAST_MODE="true"
                shift
                ;;
            help|-h|--help)
                show_usage
                exit 0
                ;;
            *)
                if [ -z "$COMMAND" ]; then
                    COMMAND="$1"
                else
                    print_error "Unknown option: $1"
                    show_usage
                    exit 1
                fi
                shift
                ;;
        esac
    done
    
    if [ -z "$COMMAND" ]; then
        print_error "No command specified"
        show_usage
        exit 1
    fi
}

# Function to check if container is running
container_running() {
    docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"
}

# Function to execute command in container
execute_in_container() {
    local python_cmd="$1"
    
    if ! container_running; then
        print_error "Container '$CONTAINER_NAME' is not running"
        print_error "Please start the robot container first:"
        print_error "  ./scripts/start-robot.sh"
        exit 1
    fi
    
    print_status "Executing in container: $CONTAINER_NAME"
    docker exec -it "$CONTAINER_NAME" bash -c "cd /opt/crypto-robot/app && $python_cmd"
}

# Function to execute command directly
execute_directly() {
    local python_cmd="$1"
    
    # Change to app directory if it exists and we're not already there
    if [ -d "$APP_DIR" ] && [ "$(pwd)" != "$APP_DIR" ]; then
        print_status "Changing to application directory: $APP_DIR"
        cd "$APP_DIR"
    fi
    
    # Check if we're in the robot7 directory
    if [ -d "robot7" ]; then
        cd robot7
        print_status "Changed to robot7 directory: $(pwd)"
    elif [ -f "start_fresh_portfolio.py" ]; then
        print_status "Already in correct directory: $(pwd)"
    else
        print_error "Cannot find robot7 directory or start_fresh_portfolio.py"
        print_error "Please run this script from the correct location"
        exit 1
    fi
    
    print_status "Executing directly"
    eval "$python_cmd"
}

# Function to execute command based on mode
execute_command() {
    local python_cmd="$1"
    
    case "$EXECUTION_MODE" in
        "container")
            execute_in_container "$python_cmd"
            ;;
        "direct")
            execute_directly "$python_cmd"
            ;;
        *)
            print_error "Unknown execution mode: $EXECUTION_MODE"
            exit 1
            ;;
    esac
}

# Function to create fresh portfolio
create_fresh_portfolio() {
    print_status "Creating fresh portfolio..."
    
    # Build command with options
    local cmd="$PYTHON_CMD start_fresh_portfolio.py"
    
    # Add starting capital if specified
    if [ -n "$STARTING_CAPITAL" ]; then
        cmd="$cmd --starting-capital $STARTING_CAPITAL"
        print_status "Using starting capital: $STARTING_CAPITAL"
    fi
    
    # Add cleanup mode
    if [ "$CLEANUP_MODE" = "full" ]; then
        cmd="$cmd --full-cleanup"
        print_status "Using comprehensive cleanup mode"
    elif [ "$FAST_MODE" = "true" ]; then
        cmd="$cmd --fast"
        print_status "Using fast mode"
    fi
    
    execute_command "$cmd"
}

# Function to create fresh portfolio (fast mode)
create_fresh_portfolio_fast() {
    print_status "Creating fresh portfolio (fast mode)..."
    
    # Build command with fast mode
    local cmd="$PYTHON_CMD start_fresh_portfolio.py --fast"
    
    # Add starting capital if specified
    if [ -n "$STARTING_CAPITAL" ]; then
        cmd="$cmd --starting-capital $STARTING_CAPITAL"
        print_status "Using starting capital: $STARTING_CAPITAL"
    fi
    
    execute_command "$cmd"
}

# Function to cleanup only
cleanup_only() {
    print_status "Performing cleanup only..."
    
    local cmd="$PYTHON_CMD start_fresh_portfolio.py --cleanup-only"
    
    # Add cleanup mode
    if [ "$CLEANUP_MODE" = "full" ]; then
        cmd="$cmd --full-cleanup"
        print_status "Using comprehensive cleanup mode"
    fi
    
    execute_command "$cmd"
}

# Function to show portfolio status
show_portfolio_status() {
    print_status "Checking portfolio status..."
    
    # Create a Python script to check portfolio status
    local status_cmd="$PYTHON_CMD -c \"
import sys
sys.path.append('src')

try:
    from src.database import get_db_manager, Simulation, SimulationCycle, TradingCycle
    import os
    
    print('📊 PORTFOLIO STATUS')
    print('=' * 50)
    
    # Check database
    db_manager = get_db_manager()
    session = db_manager.get_session()
    
    sim_count = session.query(Simulation).count()
    cycle_count = session.query(SimulationCycle).count()
    trading_count = session.query(TradingCycle).count()
    
    print(f'Database Records:')
    print(f'  • Simulations: {sim_count}')
    print(f'  • Simulation Cycles: {cycle_count}')
    print(f'  • Trading Cycles: {trading_count}')
    
    # Check environment configuration
    print(f'\\nEnvironment Configuration:')
    print(f'  • Starting Capital: {os.getenv(\\\"STARTING_CAPITAL\\\", \\\"100\\\")} BNB')
    print(f'  • Calibration Profile: {os.getenv(\\\"DEFAULT_CALIBRATION_PROFILE\\\", \\\"moderate_realistic\\\")}')
    print(f'  • Full Cleanup Mode: {os.getenv(\\\"FULL_CLEANUP\\\", \\\"false\\\")}')
    
    # Check if portfolio is ready
    if sim_count == 0 and cycle_count == 0:
        print(f'\\n✅ Portfolio Status: Clean and ready for fresh start')
    else:
        print(f'\\n📊 Portfolio Status: Contains existing data')
        
        # Show latest simulation if exists
        latest_sim = session.query(Simulation).order_by(Simulation.id.desc()).first()
        if latest_sim:
            print(f'  • Latest Simulation: {latest_sim.name} (ID: {latest_sim.id})')
            print(f'  • Created: {latest_sim.created_at}')
    
    session.close()
    
    print(f'\\n🚀 Available Actions:')
    print(f'  • Create fresh portfolio: ./scripts/portfolio-manager.sh create-fresh')
    print(f'  • Fast portfolio setup: ./scripts/portfolio-manager.sh create-fresh-fast')
    print(f'  • Cleanup only: ./scripts/portfolio-manager.sh cleanup-only')
    
except Exception as e:
    print(f'❌ Error checking portfolio status: {e}')
    sys.exit(1)
\""
    
    execute_command "$status_cmd"
}

# Function to validate portfolio configuration
validate_portfolio() {
    print_status "Validating portfolio configuration..."
    
    local validate_cmd="$PYTHON_CMD -c \"
import sys
sys.path.append('src')

try:
    import os
    from pathlib import Path
    
    print('🔍 PORTFOLIO CONFIGURATION VALIDATION')
    print('=' * 50)
    
    validation_results = {
        'files_found': 0,
        'files_missing': 0,
        'config_valid': True,
        'errors': []
    }
    
    # Check required files
    required_files = [
        'start_fresh_portfolio.py',
        'src/database.py',
        'src/portfolio_manager.py',
        'main.py'
    ]
    
    print('📁 Checking required files:')
    for file_path in required_files:
        if Path(file_path).exists():
            print(f'  ✅ {file_path}')
            validation_results['files_found'] += 1
        else:
            print(f'  ❌ {file_path} - MISSING')
            validation_results['files_missing'] += 1
            validation_results['errors'].append(f'Missing file: {file_path}')
    
    # Check environment variables
    print(f'\\n🔧 Environment Configuration:')
    env_vars = {
        'STARTING_CAPITAL': os.getenv('STARTING_CAPITAL', '100'),
        'DEFAULT_CALIBRATION_PROFILE': os.getenv('DEFAULT_CALIBRATION_PROFILE', 'moderate_realistic'),
        'FULL_CLEANUP': os.getenv('FULL_CLEANUP', 'false'),
        'ENABLE_CALIBRATION': os.getenv('ENABLE_CALIBRATION', 'true')
    }
    
    for var, value in env_vars.items():
        print(f'  • {var}: {value}')
    
    # Check database connectivity
    print(f'\\n🗄️  Database Connectivity:')
    try:
        from src.database import get_db_manager
        db_manager = get_db_manager()
        session = db_manager.get_session()
        session.close()
        print(f'  ✅ Database connection successful')
    except Exception as db_error:
        print(f'  ❌ Database connection failed: {db_error}')
        validation_results['config_valid'] = False
        validation_results['errors'].append(f'Database error: {db_error}')
    
    # Summary
    print(f'\\n📊 VALIDATION SUMMARY:')
    print(f'  • Files found: {validation_results[\\\"files_found\\\"]}')
    print(f'  • Files missing: {validation_results[\\\"files_missing\\\"]}')
    print(f'  • Configuration valid: {validation_results[\\\"config_valid\\\"]}')
    print(f'  • Errors: {len(validation_results[\\\"errors\\\"])}')
    
    if validation_results['errors']:
        print(f'\\n⚠️  ERRORS FOUND:')
        for error in validation_results['errors']:
            print(f'  • {error}')
    
    if validation_results['files_missing'] == 0 and validation_results['config_valid']:
        print(f'\\n✅ VALIDATION PASSED - Portfolio system ready')
    else:
        print(f'\\n❌ VALIDATION FAILED - Please fix errors before proceeding')
        sys.exit(1)
        
except Exception as e:
    print(f'❌ Validation error: {e}')
    sys.exit(1)
\""
    
    execute_command "$validate_cmd"
}

# Main function
main() {
    # Parse arguments
    parse_args "$@"
    
    print_status "Portfolio management command: $COMMAND"
    print_status "Execution mode: $EXECUTION_MODE"
    
    # Set environment variables if specified
    if [ -n "$STARTING_CAPITAL" ]; then
        export STARTING_CAPITAL="$STARTING_CAPITAL"
    fi
    
    if [ "$CLEANUP_MODE" = "full" ]; then
        export FULL_CLEANUP="true"
    elif [ "$FAST_MODE" = "true" ]; then
        export FULL_CLEANUP="false"
    fi
    
    # Execute command
    case "$COMMAND" in
        "create-fresh")
            create_fresh_portfolio
            ;;
        "create-fresh-fast")
            create_fresh_portfolio_fast
            ;;
        "cleanup-only")
            cleanup_only
            ;;
        "status")
            show_portfolio_status
            ;;
        "validate")
            validate_portfolio
            ;;
        *)
            print_error "Unknown command: $COMMAND"
            show_usage
            exit 1
            ;;
    esac
    
    print_success "Portfolio management operation completed!"
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi