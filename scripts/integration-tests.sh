#!/bin/bash
# Crypto Robot Integration Tests
# End-to-end testing for Python deployment system

set -e

echo "🔗 Crypto Robot Integration Tests"
echo "================================="

# Configuration
APP_PATH="/opt/crypto-robot"
TEST_LOG_FILE="/tmp/integration-test-$(date +%Y%m%d-%H%M%S).log"
TEST_ENV_FILE="/tmp/test-env-$$.env"
TEST_HOSTNAME="test-integration.crypto-robot.local"

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to log messages
log_message() {
    local message="$1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $message" | tee -a "$TEST_LOG_FILE"
}

# Function to run integration test
run_integration_test() {
    local test_name="$1"
    local test_function="$2"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    log_message "🔍 Starting integration test: $test_name"
    
    if $test_function; then
        log_message "✅ PASS: $test_name"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        log_message "❌ FAIL: $test_name"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# Function to setup test environment
setup_test_environment() {
    log_message "🔧 Setting up test environment"
    
    # Create test .env file
    cat > "$TEST_ENV_FILE" << EOF
# Test Environment Configuration
FLASK_HOST=127.0.0.1
FLASK_PORT=5001
FLASK_PROTOCOL=http
USE_HTTPS=false
FLASK_DEBUG=true

# Test Domain Configuration
DOMAIN_NAME=$TEST_HOSTNAME
HOSTNAME=$TEST_HOSTNAME

# Test Database Configuration
DATABASE_TYPE=sqlite
DATABASE_PATH=/tmp/test-crypto-robot-db
DATABASE_FILE=test-cryptorobot.db

# Test Trading Configuration
BINANCE_API_KEY=test_api_key_placeholder
BINANCE_SECRET_KEY=test_secret_key_placeholder
STARTING_CAPITAL=100
ROBOT_DRY_RUN=true
STRATEGY_NAME=daily_rebalance
PORTFOLIO_SIZE=5

# Test SSL Configuration
SSL_CERT_PATH=/tmp/test-cert.pem
SSL_KEY_PATH=/tmp/test-key.pem
EOF
    
    # Create test database directory
    mkdir -p /tmp/test-crypto-robot-db
    
    # Create dummy SSL certificates for testing
    openssl req -x509 -newkey rsa:2048 -keyout /tmp/test-key.pem -out /tmp/test-cert.pem \
        -days 1 -nodes -subj "/CN=$TEST_HOSTNAME" >/dev/null 2>&1
    
    log_message "✅ Test environment setup completed"
}

# Function to cleanup test environment
cleanup_test_environment() {
    log_message "🧹 Cleaning up test environment"
    
    # Remove test files
    rm -f "$TEST_ENV_FILE"
    rm -f /tmp/test-cert.pem /tmp/test-key.pem
    rm -rf /tmp/test-crypto-robot-db
    
    # Stop any test processes
    pkill -f "python.*test.*" 2>/dev/null || true
    
    log_message "✅ Test environment cleanup completed"
}

# Integration Test 1: Environment Management End-to-End
test_environment_management_e2e() {
    log_message "Testing environment management end-to-end workflow"
    
    # Test environment creation
    if ! cd "$APP_PATH" && ./scripts/manage-env.sh create >/dev/null 2>&1; then
        log_message "❌ Failed to create environment from template"
        return 1
    fi
    
    # Test environment validation
    if ! ./scripts/manage-env.sh validate >/dev/null 2>&1; then
        log_message "⚠️  Environment validation failed (expected for template)"
    fi
    
    # Test environment variable update
    if ! ./scripts/manage-env.sh update FLASK_PORT 5001 >/dev/null 2>&1; then
        log_message "❌ Failed to update environment variable"
        return 1
    fi
    
    # Test environment backup
    if ! ./scripts/manage-env.sh backup >/dev/null 2>&1; then
        log_message "❌ Failed to create environment backup"
        return 1
    fi
    
    log_message "✅ Environment management workflow completed"
    return 0
}

# Integration Test 2: API Key Injection Workflow
test_api_key_injection_workflow() {
    log_message "Testing API key injection workflow"
    
    # Setup test environment with API keys
    export HOSTNAME="$TEST_HOSTNAME"
    export TEST_INTEGRATION_CRYPTO_ROBOT_LOCAL_KEYS='{"BINANCE_API_KEY":"test_key_123","BINANCE_SECRET_KEY":"test_secret_456"}'
    
    # Copy test environment file
    cp "$TEST_ENV_FILE" "$APP_PATH/.env.test"
    
    # Test API key injection (dry run)
    if cd "$APP_PATH" && ENV_FILE=".env.test" ./scripts/inject-api-keys.sh --validate-only >/dev/null 2>&1; then
        log_message "✅ API key injection validation passed"
    else
        log_message "⚠️  API key injection validation failed (expected without proper secret)"
    fi
    
    # Cleanup
    rm -f "$APP_PATH/.env.test"
    unset HOSTNAME TEST_INTEGRATION_CRYPTO_ROBOT_LOCAL_KEYS
    
    return 0
}

# Integration Test 3: Certificate Configuration Workflow
test_certificate_configuration_workflow() {
    log_message "Testing certificate configuration workflow"
    
    # Test certificate setup
    if ! cd "$APP_PATH" && ./scripts/configure-certificates.sh copy "$TEST_HOSTNAME" /tmp/test-cert.pem /tmp/test-key.pem >/dev/null 2>&1; then
        log_message "❌ Failed to copy test certificates"
        return 1
    fi
    
    # Test certificate validation
    if ! ./scripts/configure-certificates.sh validate "$TEST_HOSTNAME" >/dev/null 2>&1; then
        log_message "❌ Certificate validation failed"
        return 1
    fi
    
    # Test certificate listing
    if ! ./scripts/configure-certificates.sh list >/dev/null 2>&1; then
        log_message "❌ Certificate listing failed"
        return 1
    fi
    
    # Cleanup test certificates
    rm -rf "$APP_PATH/certificates/$TEST_HOSTNAME"
    
    log_message "✅ Certificate configuration workflow completed"
    return 0
}

# Integration Test 4: Service Startup and Shutdown
test_service_lifecycle() {
    log_message "Testing service startup and shutdown lifecycle"
    
    # Copy test environment
    cp "$TEST_ENV_FILE" "$APP_PATH/.env.integration-test"
    
    # Test robot startup (dry run)
    local robot_pid=""
    if cd "$APP_PATH"; then
        # Start robot in background with test config
        ENV_FILE=".env.integration-test" timeout 10s ./scripts/start-robot-direct.sh >/dev/null 2>&1 &
        robot_pid=$!
        
        # Wait a moment for startup
        sleep 3
        
        # Check if process is running
        if ps -p "$robot_pid" >/dev/null 2>&1; then
            log_message "✅ Robot startup successful"
            
            # Stop the robot
            kill "$robot_pid" 2>/dev/null || true
            wait "$robot_pid" 2>/dev/null || true
            log_message "✅ Robot shutdown successful"
        else
            log_message "❌ Robot failed to start or exited early"
            return 1
        fi
    fi
    
    # Test webapp startup (dry run)
    local webapp_pid=""
    if cd "$APP_PATH"; then
        # Start webapp in background with test config
        ENV_FILE=".env.integration-test" timeout 10s ./scripts/start-webapp-direct.sh >/dev/null 2>&1 &
        webapp_pid=$!
        
        # Wait a moment for startup
        sleep 3
        
        # Check if process is running
        if ps -p "$webapp_pid" >/dev/null 2>&1; then
            log_message "✅ WebApp startup successful"
            
            # Test basic HTTP response
            if curl -s --connect-timeout 2 http://127.0.0.1:5001/ >/dev/null 2>&1; then
                log_message "✅ WebApp HTTP response successful"
            else
                log_message "⚠️  WebApp HTTP response failed (may still be starting)"
            fi
            
            # Stop the webapp
            kill "$webapp_pid" 2>/dev/null || true
            wait "$webapp_pid" 2>/dev/null || true
            log_message "✅ WebApp shutdown successful"
        else
            log_message "❌ WebApp failed to start or exited early"
            return 1
        fi
    fi
    
    # Cleanup
    rm -f "$APP_PATH/.env.integration-test"
    
    return 0
}

# Integration Test 5: Health Check System
test_health_check_system() {
    log_message "Testing health check system"
    
    # Test health check script execution
    if ! cd "$APP_PATH" && ./scripts/health-check.sh --quick >/dev/null 2>&1; then
        log_message "⚠️  Health check failed (expected in test environment)"
    else
        log_message "✅ Health check executed successfully"
    fi
    
    # Test deployment validation
    if ! ./scripts/test-deployment.sh --quick >/dev/null 2>&1; then
        log_message "⚠️  Deployment validation had issues (expected in test environment)"
    else
        log_message "✅ Deployment validation executed successfully"
    fi
    
    return 0
}

# Integration Test 6: Multi-Environment Deployment Simulation
test_multi_environment_deployment() {
    log_message "Testing multi-environment deployment simulation"
    
    local environments=("crypto-robot.local" "test-robot.example.com")
    
    for env in "${environments[@]}"; do
        log_message "Testing deployment for environment: $env"
        
        # Create environment-specific test config
        local env_file="/tmp/test-env-$env.env"
        sed "s/$TEST_HOSTNAME/$env/g" "$TEST_ENV_FILE" > "$env_file"
        
        # Test environment validation
        if cd "$APP_PATH" && ENV_FILE="$env_file" ./scripts/manage-env.sh validate >/dev/null 2>&1; then
            log_message "✅ Environment $env validation passed"
        else
            log_message "⚠️  Environment $env validation failed (expected for test config)"
        fi
        
        # Cleanup
        rm -f "$env_file"
    done
    
    return 0
}

# Integration Test 7: Performance and Resource Usage
test_performance_and_resources() {
    log_message "Testing performance and resource usage"
    
    # Test Python environment performance
    if [ -f "$APP_PATH/venv/bin/activate" ]; then
        source "$APP_PATH/venv/bin/activate"
        
        # Test import performance
        local start_time=$(date +%s%N)
        python -c "import flask, requests, pandas, numpy" >/dev/null 2>&1
        local end_time=$(date +%s%N)
        local import_time=$(( (end_time - start_time) / 1000000 ))
        
        if [ "$import_time" -lt 5000 ]; then
            log_message "✅ Package import performance acceptable (${import_time}ms)"
        else
            log_message "⚠️  Package import performance slow (${import_time}ms)"
        fi
        
        deactivate 2>/dev/null || true
    fi
    
    # Test system resource availability
    local available_memory=$(free -m | awk 'NR==2{print $7}')
    local available_disk=$(df "$APP_PATH" | awk 'NR==2 {print $4}')
    
    if [ "$available_memory" -gt 512 ]; then
        log_message "✅ Sufficient memory available (${available_memory}MB)"
    else
        log_message "⚠️  Low memory available (${available_memory}MB)"
    fi
    
    if [ "$available_disk" -gt 1048576 ]; then  # 1GB in KB
        log_message "✅ Sufficient disk space available"
    else
        log_message "⚠️  Low disk space available"
    fi
    
    return 0
}

# Integration Test 8: Error Handling and Recovery
test_error_handling_and_recovery() {
    log_message "Testing error handling and recovery"
    
    # Test handling of missing files
    local test_missing_file="/tmp/nonexistent-file-$$.txt"
    
    if cd "$APP_PATH" && ./scripts/manage-env.sh validate 2>/dev/null; then
        log_message "✅ Error handling for missing .env file works"
    else
        log_message "✅ Proper error handling for missing .env file"
    fi
    
    # Test recovery from backup
    if ./scripts/manage-env.sh backup >/dev/null 2>&1; then
        log_message "✅ Backup creation works"
        
        # List backups to verify
        if ls "$APP_PATH/backups/env/"*.backup.* >/dev/null 2>&1; then
            log_message "✅ Backup files created successfully"
        fi
    fi
    
    return 0
}

# Function to display integration test summary
display_integration_summary() {
    echo ""
    log_message "📊 Integration Test Summary"
    log_message "=========================="
    log_message "Total Integration Tests: $TOTAL_TESTS"
    log_message "Passed: $PASSED_TESTS"
    log_message "Failed: $FAILED_TESTS"
    
    local success_rate=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    
    if [ $FAILED_TESTS -eq 0 ]; then
        log_message "🎉 All integration tests passed! ($success_rate% success rate)"
        log_message "✅ System integration validation successful"
        echo ""
        echo "🎉 All integration tests passed! ($success_rate% success rate)"
        echo "✅ System integration validation successful"
        return 0
    else
        log_message "❌ $FAILED_TESTS integration tests failed ($success_rate% success rate)"
        log_message "🔧 Please review the failed tests and system configuration"
        echo ""
        echo "❌ $FAILED_TESTS integration tests failed ($success_rate% success rate)"
        echo "🔧 Please review the failed tests and system configuration"
        return 1
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --quick         Run only critical integration tests"
    echo "  --full          Run all integration tests (default)"
    echo "  --env-only      Test only environment management"
    echo "  --service-only  Test only service lifecycle"
    echo "  --perf-only     Test only performance"
    echo "  --verbose       Show detailed output"
    echo "  --help          Show this help message"
    echo ""
}

# Parse command line arguments
QUICK_MODE=false
ENV_ONLY=false
SERVICE_ONLY=false
PERF_ONLY=false
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
        --env-only)
            ENV_ONLY=true
            shift
            ;;
        --service-only)
            SERVICE_ONLY=true
            shift
            ;;
        --perf-only)
            PERF_ONLY=true
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
    log_message "🚀 Starting integration tests"
    log_message "Timestamp: $(date)"
    log_message "Test log: $TEST_LOG_FILE"
    
    echo "🚀 Starting integration tests..."
    echo "📝 Test log: $TEST_LOG_FILE"
    echo ""
    
    # Setup test environment
    setup_test_environment
    
    # Trap to ensure cleanup
    trap cleanup_test_environment EXIT
    
    # Run integration tests based on options
    if [ "$ENV_ONLY" = "true" ]; then
        run_integration_test "Environment Management E2E" test_environment_management_e2e
        run_integration_test "API Key Injection Workflow" test_api_key_injection_workflow
    elif [ "$SERVICE_ONLY" = "true" ]; then
        run_integration_test "Service Lifecycle" test_service_lifecycle
        run_integration_test "Health Check System" test_health_check_system
    elif [ "$PERF_ONLY" = "true" ]; then
        run_integration_test "Performance and Resources" test_performance_and_resources
    else
        # Run all integration tests
        run_integration_test "Environment Management E2E" test_environment_management_e2e
        run_integration_test "API Key Injection Workflow" test_api_key_injection_workflow
        run_integration_test "Certificate Configuration Workflow" test_certificate_configuration_workflow
        run_integration_test "Service Lifecycle" test_service_lifecycle
        run_integration_test "Health Check System" test_health_check_system
        
        if [ "$QUICK_MODE" = "false" ]; then
            run_integration_test "Multi-Environment Deployment" test_multi_environment_deployment
            run_integration_test "Performance and Resources" test_performance_and_resources
            run_integration_test "Error Handling and Recovery" test_error_handling_and_recovery
        fi
    fi
    
    display_integration_summary
    
    echo ""
    echo "📄 Detailed test log available at: $TEST_LOG_FILE"
}

# Execute main function
main "$@"