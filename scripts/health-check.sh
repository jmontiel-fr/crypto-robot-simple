#!/bin/bash
# Crypto Robot Deployment Health Check Script
# Validates successful deployment and application health

set -e

echo "🏥 Crypto Robot Deployment Health Check"
echo "======================================="

# Configuration
APP_PATH="/opt/crypto-robot"
VENV_PATH="/opt/crypto-robot/venv"
LOG_PATH="/opt/crypto-robot/logs"
ENV_FILE="/opt/crypto-robot/.env"

# Health check results
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNINGS=0

# Function to run a health check
run_check() {
    local check_name="$1"
    local check_command="$2"
    local is_critical="${3:-true}"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    echo -n "🔍 $check_name... "
    
    if eval "$check_command" >/dev/null 2>&1; then
        echo "✅ PASS"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        if [ "$is_critical" = "true" ]; then
            echo "❌ FAIL"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
        else
            echo "⚠️  WARN"
            WARNINGS=$((WARNINGS + 1))
        fi
        return 1
    fi
}

# Function to check directory structure
check_directory_structure() {
    echo "📁 Checking Directory Structure"
    echo "==============================="
    
    run_check "Application directory exists" "[ -d '$APP_PATH' ]"
    run_check "Virtual environment exists" "[ -d '$VENV_PATH' ]"
    run_check "Log directory exists" "[ -d '$LOG_PATH' ]"
    run_check "Scripts directory exists" "[ -d '$APP_PATH/scripts' ]"
    run_check "Robot source code exists" "[ -f '$APP_PATH/main.py' ]"
    run_check "WebApp source code exists" "[ -f '$APP_PATH/app.py' ]"
    run_check "Requirements file exists" "[ -f '$APP_PATH/requirements.txt' ]"
    
    echo ""
}

# Function to check file permissions
check_file_permissions() {
    echo "🔒 Checking File Permissions"
    echo "============================"
    
    run_check "Application directory ownership" "[ \$(stat -c '%U' '$APP_PATH') = 'ec2-user' ]"
    
    if [ -f "$ENV_FILE" ]; then
        run_check "Environment file permissions" "[ \$(stat -c '%a' '$ENV_FILE') = '600' ]"
        run_check "Environment file ownership" "[ \$(stat -c '%U' '$ENV_FILE') = 'ec2-user' ]"
    else
        echo "⚠️  Environment file not found - skipping permission checks"
        WARNINGS=$((WARNINGS + 1))
    fi
    
    run_check "Scripts are executable" "[ -x '$APP_PATH/scripts/start-robot-direct.sh' ]"
    
    echo ""
}

# Function to check Python environment
check_python_environment() {
    echo "🐍 Checking Python Environment"
    echo "=============================="
    
    run_check "Virtual environment activation script exists" "[ -f '$VENV_PATH/bin/activate' ]"
    
    if [ -f "$VENV_PATH/bin/activate" ]; then
        # Activate virtual environment for checks
        source "$VENV_PATH/bin/activate"
        
        run_check "Python executable in venv" "command -v python >/dev/null"
        run_check "Pip executable in venv" "command -v pip >/dev/null"
        
        # Check critical Python packages
        local critical_packages=("flask" "requests" "pandas" "numpy" "python-dotenv")
        
        for package in "${critical_packages[@]}"; do
            run_check "Package $package installed" "python -c 'import ${package//-/_}' 2>/dev/null"
        done
        
        # Check Binance package specifically
        run_check "Binance package installed" "python -c 'import binance' 2>/dev/null"
        
        deactivate 2>/dev/null || true
    else
        echo "❌ Cannot activate virtual environment - skipping Python checks"
        FAILED_CHECKS=$((FAILED_CHECKS + 5))
        TOTAL_CHECKS=$((TOTAL_CHECKS + 5))
    fi
    
    echo ""
}

# Function to check environment configuration
check_environment_configuration() {
    echo "⚙️  Checking Environment Configuration"
    echo "====================================="
    
    if [ ! -f "$ENV_FILE" ]; then
        echo "❌ Environment file not found: $ENV_FILE"
        FAILED_CHECKS=$((FAILED_CHECKS + 5))
        TOTAL_CHECKS=$((TOTAL_CHECKS + 5))
        return 1
    fi
    
    # Load environment variables
    source "$ENV_FILE"
    
    # Check required variables
    local required_vars=(
        "BINANCE_API_KEY"
        "BINANCE_SECRET_KEY"
        "STARTING_CAPITAL"
        "FLASK_PORT"
        "FLASK_HOST"
        "DATABASE_TYPE"
    )
    
    for var in "${required_vars[@]}"; do
        run_check "Environment variable $var set" "[ -n \"\${$var}\" ]"
    done
    
    # Check API keys are not placeholder values
    run_check "Binance API key configured" "[ \"\$BINANCE_API_KEY\" != 'your_binance_api_key_here' ]"
    run_check "Binance secret key configured" "[ \"\$BINANCE_SECRET_KEY\" != 'your_binance_secret_key_here' ]"
    
    # Check configuration consistency
    if [ "${USE_HTTPS:-false}" = "true" ] || [ "${FLASK_PROTOCOL:-http}" = "https" ]; then
        run_check "SSL certificate path configured" "[ -n \"\$SSL_CERT_PATH\" ]" false
        run_check "SSL key path configured" "[ -n \"\$SSL_KEY_PATH\" ]" false
        
        if [ -n "$SSL_CERT_PATH" ] && [ -n "$SSL_KEY_PATH" ]; then
            run_check "SSL certificate file exists" "[ -f \"\$SSL_CERT_PATH\" ]" false
            run_check "SSL key file exists" "[ -f \"\$SSL_KEY_PATH\" ]" false
        fi
    fi
    
    echo ""
}

# Function to check systemd services
check_systemd_services() {
    echo "⚙️  Checking Systemd Services"
    echo "============================"
    
    local services=("crypto-robot" "crypto-webapp")
    
    for service in "${services[@]}"; do
        run_check "Service $service installed" "systemctl list-unit-files | grep -q '$service.service'" false
        
        if systemctl list-unit-files | grep -q "$service.service"; then
            run_check "Service $service enabled" "systemctl is-enabled --quiet '$service'" false
            run_check "Service $service active" "systemctl is-active --quiet '$service'" false
        fi
    done
    
    echo ""
}

# Function to check running processes
check_running_processes() {
    echo "🔄 Checking Running Processes"
    echo "============================="
    
    run_check "Robot process running" "pgrep -f 'python.*main.py' >/dev/null" false
    run_check "WebApp process running" "pgrep -f 'python.*app.py' >/dev/null" false
    
    # Check PID files
    run_check "Robot PID file exists" "[ -f '$APP_PATH/robot.pid' ]" false
    run_check "WebApp PID file exists" "[ -f '$APP_PATH/webapp.pid' ]" false
    
    # Validate PID files if they exist
    if [ -f "$APP_PATH/robot.pid" ]; then
        local robot_pid=$(cat "$APP_PATH/robot.pid")
        run_check "Robot PID valid" "ps -p '$robot_pid' >/dev/null" false
    fi
    
    if [ -f "$APP_PATH/webapp.pid" ]; then
        local webapp_pid=$(cat "$APP_PATH/webapp.pid")
        run_check "WebApp PID valid" "ps -p '$webapp_pid' >/dev/null" false
    fi
    
    echo ""
}

# Function to check network connectivity
check_network_connectivity() {
    echo "🌐 Checking Network Connectivity"
    echo "==============================="
    
    run_check "Internet connectivity" "ping -c 1 8.8.8.8 >/dev/null" false
    run_check "Binance API reachable" "curl -s --connect-timeout 5 https://api.binance.com/api/v3/ping >/dev/null" false
    
    # Check if Flask port is listening
    if [ -n "${FLASK_PORT:-}" ]; then
        run_check "Flask port $FLASK_PORT listening" "netstat -tuln | grep -q ':$FLASK_PORT '" false
    fi
    
    echo ""
}

# Function to check log files
check_log_files() {
    echo "📝 Checking Log Files"
    echo "===================="
    
    run_check "Log directory writable" "[ -w '$LOG_PATH' ]"
    
    # Check for recent log activity
    local recent_logs=$(find "$LOG_PATH" -name "*.log" -mmin -60 2>/dev/null | wc -l)
    run_check "Recent log activity" "[ '$recent_logs' -gt 0 ]" false
    
    # Check log file sizes (warn if too large)
    local large_logs=$(find "$LOG_PATH" -name "*.log" -size +100M 2>/dev/null | wc -l)
    run_check "Log files not too large" "[ '$large_logs' -eq 0 ]" false
    
    echo ""
}

# Function to test API connectivity
test_api_connectivity() {
    echo "🔑 Testing API Connectivity"
    echo "==========================="
    
    if [ ! -f "$ENV_FILE" ]; then
        echo "❌ Cannot test API - environment file not found"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
        return 1
    fi
    
    # Load environment and test Binance API
    source "$ENV_FILE"
    
    if [ "$BINANCE_API_KEY" = "your_binance_api_key_here" ] || [ -z "$BINANCE_API_KEY" ]; then
        echo "⚠️  Binance API keys not configured - skipping API tests"
        WARNINGS=$((WARNINGS + 1))
        return 0
    fi
    
    # Activate virtual environment
    if [ -f "$VENV_PATH/bin/activate" ]; then
        source "$VENV_PATH/bin/activate"
        
        # Test API connectivity using Python
        local api_test_result=$(python -c "
import os
from binance.client import Client
try:
    client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_SECRET_KEY'))
    status = client.get_account_status()
    print('SUCCESS')
except Exception as e:
    print(f'ERROR: {e}')
" 2>/dev/null)
        
        if [[ "$api_test_result" == "SUCCESS" ]]; then
            run_check "Binance API authentication" "true"
        else
            run_check "Binance API authentication" "false" false
            echo "  API Error: $api_test_result"
        fi
        
        deactivate 2>/dev/null || true
    else
        echo "❌ Cannot test API - virtual environment not available"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    fi
    
    echo ""
}

# Function to display summary
display_summary() {
    echo "📊 Health Check Summary"
    echo "======================"
    echo "Total Checks: $TOTAL_CHECKS"
    echo "Passed: $PASSED_CHECKS"
    echo "Failed: $FAILED_CHECKS"
    echo "Warnings: $WARNINGS"
    echo ""
    
    local success_rate=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
    
    if [ $FAILED_CHECKS -eq 0 ]; then
        echo "🎉 All critical checks passed! ($success_rate% success rate)"
        if [ $WARNINGS -gt 0 ]; then
            echo "⚠️  $WARNINGS warnings detected - review recommended"
        fi
        return 0
    else
        echo "❌ $FAILED_CHECKS critical checks failed ($success_rate% success rate)"
        echo "🔧 Please address the failed checks before proceeding"
        return 1
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --quick         Run only critical checks (faster)"
    echo "  --full          Run all checks including API tests (default)"
    echo "  --api-only      Run only API connectivity tests"
    echo "  --no-api        Skip API connectivity tests"
    echo "  --verbose       Show detailed output for each check"
    echo "  --help          Show this help message"
    echo ""
}

# Parse command line arguments
QUICK_MODE=false
API_ONLY=false
NO_API=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            QUICK_MODE=true
            shift
            ;;
        --full)
            # Default mode, no action needed
            shift
            ;;
        --api-only)
            API_ONLY=true
            shift
            ;;
        --no-api)
            NO_API=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            echo "❌ Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    echo "🚀 Starting health check..."
    echo "Timestamp: $(date)"
    echo ""
    
    if [ "$API_ONLY" = "true" ]; then
        test_api_connectivity
    else
        check_directory_structure
        check_file_permissions
        check_python_environment
        check_environment_configuration
        
        if [ "$QUICK_MODE" = "false" ]; then
            check_systemd_services
            check_running_processes
            check_network_connectivity
            check_log_files
            
            if [ "$NO_API" = "false" ]; then
                test_api_connectivity
            fi
        fi
    fi
    
    display_summary
}

# Execute main function
main "$@"