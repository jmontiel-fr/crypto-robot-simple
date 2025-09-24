#!/bin/bash
# Crypto Robot Deployment Validation Tests
# Validates Python environment setup, API key injection, and service startup

set -e

echo "🧪 Crypto Robot Deployment Validation Tests"
echo "==========================================="

# Configuration
APP_PATH="/opt/crypto-robot"
VENV_PATH="/opt/crypto-robot/venv"
TEST_RESULTS_FILE="/tmp/deployment-test-results.txt"

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"
    local is_critical="${3:-true}"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo -n "🔍 Testing: $test_name... "
    
    if eval "$test_command" >/dev/null 2>&1; then
        echo "✅ PASS"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        echo "PASS: $test_name" >> "$TEST_RESULTS_FILE"
        return 0
    else
        if [ "$is_critical" = "true" ]; then
            echo "❌ FAIL"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            echo "FAIL: $test_name" >> "$TEST_RESULTS_FILE"
        else
            echo "⚠️  WARN"
            echo "WARN: $test_name" >> "$TEST_RESULTS_FILE"
        fi
        return 1
    fi
}

# Function to test Python environment setup
test_python_environment() {
    echo "🐍 Testing Python Environment Setup"
    echo "==================================="
    
    run_test "Virtual environment directory exists" "[ -d '$VENV_PATH' ]"
    run_test "Virtual environment activation script exists" "[ -f '$VENV_PATH/bin/activate' ]"
    
    if [ -f "$VENV_PATH/bin/activate" ]; then
        source "$VENV_PATH/bin/activate"
        
        run_test "Python executable in virtual environment" "command -v python >/dev/null"
        run_test "Pip executable in virtual environment" "command -v pip >/dev/null"
        
        # Test critical packages
        local packages=("flask" "requests" "pandas" "numpy" "python-dotenv" "binance")
        for package in "${packages[@]}"; do
            run_test "Package $package installed" "python -c 'import ${package//-/_}' 2>/dev/null"
        done
        
        # Test package versions
        run_test "Flask version compatible" "python -c 'import flask; assert flask.__version__ >= \"3.0.0\"'"
        run_test "Requests version compatible" "python -c 'import requests; assert requests.__version__ >= \"2.31.0\"'"
        
        deactivate 2>/dev/null || true
    else
        echo "❌ Cannot test packages - virtual environment not available"
        FAILED_TESTS=$((FAILED_TESTS + 5))
        TOTAL_TESTS=$((TOTAL_TESTS + 5))
    fi
    
    echo ""
}

# Function to test API key injection functionality
test_api_key_injection() {
    echo "🔑 Testing API Key Injection"
    echo "============================"
    
    # Create test environment
    local test_env_file="/tmp/test-env-$$.env"
    local test_hostname="test-robot.example.com"
    
    # Create test .env file
    cat > "$test_env_file" << 'EOF'
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_key_here
FLASK_PORT=5000
FLASK_HOST=0.0.0.0
EOF
    
    run_test "Test environment file created" "[ -f '$test_env_file' ]"
    
    # Test API key injection script exists
    run_test "API key injection script exists" "[ -f '$APP_PATH/scripts/inject-api-keys.sh' ]"
    run_test "API key injection script executable" "[ -x '$APP_PATH/scripts/inject-api-keys.sh' ]"
    
    # Test environment management script
    run_test "Environment management script exists" "[ -f '$APP_PATH/scripts/manage-env.sh' ]"
    run_test "Environment management script executable" "[ -x '$APP_PATH/scripts/manage-env.sh' ]"
    
    # Test validation functionality
    if [ -f "$APP_PATH/scripts/manage-env.sh" ]; then
        # Test with the test environment file
        run_test "Environment validation works" "cd '$APP_PATH' && ENV_FILE='$test_env_file' ./scripts/manage-env.sh validate" false
    fi
    
    # Cleanup
    rm -f "$test_env_file"
    
    echo ""
}

# Function to test service startup configuration
test_service_startup() {
    echo "🚀 Testing Service Startup Configuration"
    echo "========================================"
    
    # Test startup scripts
    run_test "Robot startup script exists" "[ -f '$APP_PATH/scripts/start-robot-direct.sh' ]"
    run_test "WebApp startup script exists" "[ -f '$APP_PATH/scripts/start-webapp-direct.sh' ]"
    run_test "Robot stop script exists" "[ -f '$APP_PATH/scripts/stop-robot-direct.sh' ]"
    run_test "WebApp stop script exists" "[ -f '$APP_PATH/scripts/stop-webapp-direct.sh' ]"
    
    # Test script permissions
    run_test "Robot startup script executable" "[ -x '$APP_PATH/scripts/start-robot-direct.sh' ]"
    run_test "WebApp startup script executable" "[ -x '$APP_PATH/scripts/start-webapp-direct.sh' ]"
    run_test "Robot stop script executable" "[ -x '$APP_PATH/scripts/stop-robot-direct.sh' ]"
    run_test "WebApp stop script executable" "[ -x '$APP_PATH/scripts/stop-webapp-direct.sh' ]"
    
    # Test systemd service files
    run_test "Robot systemd service file exists" "[ -f '$APP_PATH/scripts/systemd/crypto-robot.service' ]"
    run_test "WebApp systemd service file exists" "[ -f '$APP_PATH/scripts/systemd/crypto-webapp.service' ]"
    run_test "Systemd installer script exists" "[ -f '$APP_PATH/scripts/install-systemd-services.sh' ]"
    
    # Test service control script
    run_test "Service control script exists" "[ -f '$APP_PATH/scripts/service-control.sh' ]"
    run_test "Service control script executable" "[ -x '$APP_PATH/scripts/service-control.sh' ]"
    
    echo ""
}

# Function to test application code
test_application_code() {
    echo "📱 Testing Application Code"
    echo "=========================="
    
    # Test main application files
    run_test "Main robot application exists" "[ -f '$APP_PATH/main.py' ]"
    run_test "WebApp application exists" "[ -f '$APP_PATH/app.py' ]"
    run_test "Requirements file exists" "[ -f '$APP_PATH/requirements.txt' ]"
    run_test "Environment template exists" "[ -f '$APP_PATH/robot/.env.template' ]"
    
    # Test Python syntax
    if [ -f "$VENV_PATH/bin/activate" ]; then
        source "$VENV_PATH/bin/activate"
        
        run_test "Main.py syntax valid" "python -m py_compile '$APP_PATH/main.py'"
        run_test "App.py syntax valid" "python -m py_compile '$APP_PATH/app.py'"
        
        # Test imports (basic)
        run_test "Main.py imports work" "cd '$APP_PATH' && python -c 'import main'" false
        run_test "App.py imports work" "cd '$APP_PATH' && python -c 'import app'" false
        
        deactivate 2>/dev/null || true
    fi
    
    echo ""
}

# Function to test configuration management
test_configuration_management() {
    echo "⚙️  Testing Configuration Management"
    echo "==================================="
    
    # Test environment template
    run_test "Environment template readable" "[ -r '$APP_PATH/robot/.env.template' ]"
    
    # Test configuration scripts
    run_test "Environment management script works" "cd '$APP_PATH' && ./scripts/manage-env.sh --help >/dev/null" false
    
    # Test certificate management
    run_test "Certificate configuration script exists" "[ -f '$APP_PATH/scripts/configure-certificates.sh' ]"
    run_test "Certificate configuration script executable" "[ -x '$APP_PATH/scripts/configure-certificates.sh' ]"
    
    # Test health check script
    run_test "Health check script exists" "[ -f '$APP_PATH/scripts/health-check.sh' ]"
    run_test "Health check script executable" "[ -x '$APP_PATH/scripts/health-check.sh' ]"
    
    echo ""
}

# Function to test directory structure and permissions
test_directory_structure() {
    echo "📁 Testing Directory Structure and Permissions"
    echo "=============================================="
    
    # Test directory structure
    run_test "Application directory exists" "[ -d '$APP_PATH' ]"
    run_test "Scripts directory exists" "[ -d '$APP_PATH/scripts' ]"
    run_test "Robot source directory exists" "[ -d '$APP_PATH/robot' ]"
    
    # Test directory permissions
    run_test "Application directory readable" "[ -r '$APP_PATH' ]"
    run_test "Scripts directory executable" "[ -x '$APP_PATH/scripts' ]"
    
    # Test ownership (if running as ec2-user)
    if [ "$(whoami)" = "ec2-user" ]; then
        run_test "Application directory owned by ec2-user" "[ \$(stat -c '%U' '$APP_PATH') = 'ec2-user' ]"
    fi
    
    # Test log directory
    run_test "Log directory exists or can be created" "mkdir -p '$APP_PATH/logs' && [ -d '$APP_PATH/logs' ]"
    run_test "Log directory writable" "[ -w '$APP_PATH/logs' ]"
    
    # Test database directory
    run_test "Database directory exists or can be created" "mkdir -p '$APP_PATH/database' && [ -d '$APP_PATH/database' ]"
    run_test "Database directory writable" "[ -w '$APP_PATH/database' ]"
    
    echo ""
}

# Function to test network connectivity
test_network_connectivity() {
    echo "🌐 Testing Network Connectivity"
    echo "=============================="
    
    run_test "Internet connectivity" "ping -c 1 8.8.8.8 >/dev/null" false
    run_test "DNS resolution works" "nslookup google.com >/dev/null" false
    run_test "HTTPS connectivity" "curl -s --connect-timeout 5 https://httpbin.org/get >/dev/null" false
    run_test "Binance API reachable" "curl -s --connect-timeout 5 https://api.binance.com/api/v3/ping >/dev/null" false
    
    echo ""
}

# Function to run performance tests
test_performance() {
    echo "⚡ Testing Performance Requirements"
    echo "=================================="
    
    # Test system resources
    local available_memory=$(free -m | awk 'NR==2{print $7}')
    local available_disk=$(df /opt/crypto-robot | awk 'NR==2 {print $4}')
    
    run_test "Sufficient memory available (>1GB)" "[ '$available_memory' -gt 1024 ]" false
    run_test "Sufficient disk space (>5GB)" "[ '$available_disk' -gt 5242880 ]" false
    
    # Test Python startup time
    if [ -f "$VENV_PATH/bin/activate" ]; then
        source "$VENV_PATH/bin/activate"
        
        local start_time=$(date +%s%N)
        python -c "import sys; print('Python startup test')" >/dev/null 2>&1
        local end_time=$(date +%s%N)
        local startup_time=$(( (end_time - start_time) / 1000000 ))  # Convert to milliseconds
        
        run_test "Python startup time reasonable (<2000ms)" "[ '$startup_time' -lt 2000 ]" false
        
        deactivate 2>/dev/null || true
    fi
    
    echo ""
}

# Function to display test summary
display_test_summary() {
    echo "📊 Test Summary"
    echo "==============="
    echo "Total Tests: $TOTAL_TESTS"
    echo "Passed: $PASSED_TESTS"
    echo "Failed: $FAILED_TESTS"
    echo ""
    
    local success_rate=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    
    if [ $FAILED_TESTS -eq 0 ]; then
        echo "🎉 All tests passed! ($success_rate% success rate)"
        echo "✅ Deployment validation successful"
        return 0
    else
        echo "❌ $FAILED_TESTS tests failed ($success_rate% success rate)"
        echo "🔧 Please address the failed tests before proceeding"
        
        echo ""
        echo "📋 Failed Tests:"
        grep "FAIL:" "$TEST_RESULTS_FILE" | sed 's/FAIL: /  - /'
        
        return 1
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --quick         Run only critical tests"
    echo "  --full          Run all tests including performance (default)"
    echo "  --python-only   Test only Python environment"
    echo "  --config-only   Test only configuration management"
    echo "  --network-only  Test only network connectivity"
    echo "  --verbose       Show detailed output"
    echo "  --help          Show this help message"
    echo ""
}

# Parse command line arguments
QUICK_MODE=false
PYTHON_ONLY=false
CONFIG_ONLY=false
NETWORK_ONLY=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            QUICK_MODE=true
            shift
            ;;
        --full)
            # Default mode
            shift
            ;;
        --python-only)
            PYTHON_ONLY=true
            shift
            ;;
        --config-only)
            CONFIG_ONLY=true
            shift
            ;;
        --network-only)
            NETWORK_ONLY=true
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
    echo "🚀 Starting deployment validation tests..."
    echo "Timestamp: $(date)"
    echo ""
    
    # Initialize test results file
    echo "Deployment Validation Test Results - $(date)" > "$TEST_RESULTS_FILE"
    echo "=============================================" >> "$TEST_RESULTS_FILE"
    
    # Run tests based on options
    if [ "$PYTHON_ONLY" = "true" ]; then
        test_python_environment
    elif [ "$CONFIG_ONLY" = "true" ]; then
        test_configuration_management
    elif [ "$NETWORK_ONLY" = "true" ]; then
        test_network_connectivity
    else
        # Run all tests
        test_directory_structure
        test_python_environment
        test_api_key_injection
        test_service_startup
        test_application_code
        test_configuration_management
        
        if [ "$QUICK_MODE" = "false" ]; then
            test_network_connectivity
            test_performance
        fi
    fi
    
    display_test_summary
    
    echo ""
    echo "📄 Detailed results saved to: $TEST_RESULTS_FILE"
}

# Execute main function
main "$@"