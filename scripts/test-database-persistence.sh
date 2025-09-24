#!/bin/bash

# Database Persistence Test Script
# Tests SQLite3 database persistence across container lifecycle
# Usage: ./scripts/test-database-persistence.sh

set -e

# Configuration
TEST_DIR="$(pwd)/test-database-persistence"
TEST_ENV_FILE="$TEST_DIR/.env"
TEST_DATABASE_DIR="$TEST_DATABASE_DIR/database"
CONTAINER_NAME="crypto-robot-persistence-test"
IMAGE="jmontiel/crypto-robot:latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

# Function to cleanup test environment
cleanup_test() {
    print_status "Cleaning up test environment..."
    
    # Stop and remove test container
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        docker stop "$CONTAINER_NAME" 2>/dev/null || true
        docker rm "$CONTAINER_NAME" 2>/dev/null || true
    fi
    
    # Remove test directory
    if [ -d "$TEST_DIR" ]; then
        rm -rf "$TEST_DIR"
    fi
    
    print_status "Test cleanup completed"
}

# Function to setup test environment
setup_test() {
    print_status "Setting up test environment..."
    
    # Create test directory
    mkdir -p "$TEST_DIR"
    mkdir -p "$TEST_DATABASE_DIR"
    
    # Create test .env file with database persistence configuration
    cat > "$TEST_ENV_FILE" << EOF
# Test environment configuration for database persistence
DATABASE_TYPE=sqlite
DATABASE_PATH=/opt/crypto-robot/database
DATABASE_FILE=test_crypto_robot.db

# Flask Configuration
FLASK_PORT=5000
FLASK_HOST=0.0.0.0
FLASK_PROTOCOL=http

# Domain Configuration
DOMAIN_NAME=crypto-robot.local
USE_HTTPS=false

# Binance Configuration (test keys)
BINANCE_API_KEY=test_api_key
BINANCE_SECRET_KEY=test_secret_key
BINANCE_TESTNET=true

# Robot Configuration
ROBOT_DRY_RUN=true
STARTING_CAPITAL=100
MIN_BALANCE_REQUIRED=10.0
EOF

    print_success "Test environment setup completed"
    print_status "Test directory: $TEST_DIR"
    print_status "Database directory: $TEST_DATABASE_DIR"
}

# Function to start test container
start_test_container() {
    print_status "Starting test container with database persistence..."
    
    # Stop existing container if running
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        docker stop "$CONTAINER_NAME"
    fi
    
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        docker rm "$CONTAINER_NAME"
    fi
    
    # Create base64 encoded env content
    local env_content=$(base64 -w 0 "$TEST_ENV_FILE")
    
    # Start container with database volume mount
    docker run -d \
        --name "$CONTAINER_NAME" \
        -e ENV_CONTENT="$env_content" \
        -e CERTIFICATE="crypto-robot.local" \
        -e MODE="webapp" \
        -v "$TEST_DATABASE_DIR:/opt/crypto-robot/database" \
        -p 5001:5000 \
        "$IMAGE"
    
    # Wait for container to start
    sleep 10
    
    # Check if container is running
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        print_success "Test container started successfully"
        return 0
    else
        print_error "Test container failed to start"
        docker logs "$CONTAINER_NAME"
        return 1
    fi
}

# Function to stop test container
stop_test_container() {
    print_status "Stopping test container..."
    
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        docker stop "$CONTAINER_NAME"
        print_success "Test container stopped"
    else
        print_warning "Test container was not running"
    fi
}

# Function to create test data in database
create_test_data() {
    print_status "Creating test data in database..."
    
    # Execute Python script inside container to create test data
    docker exec "$CONTAINER_NAME" python -c "
import sys
sys.path.append('/opt/crypto-robot/app')
sys.path.append('/opt/crypto-robot/app/src')

from database import get_db_manager, Portfolio, Position
from datetime import datetime

# Initialize database
db_manager = get_db_manager()
db_manager.create_tables()

# Create test portfolio
session = db_manager.get_session()
try:
    # Create a test portfolio
    portfolio = Portfolio(
        bnb_reserve=50.0,
        current_cycle=1,
        is_frozen=False
    )
    session.add(portfolio)
    session.commit()
    
    # Create test positions
    positions = [
        Position(
            portfolio_id=portfolio.id,
            symbol='BTCUSDT',
            quantity=0.001,
            entry_price=45000.0,
            current_price=46000.0,
            entry_date=datetime.now(),
            is_active=True
        ),
        Position(
            portfolio_id=portfolio.id,
            symbol='ETHUSDT',
            quantity=0.1,
            entry_price=3000.0,
            current_price=3100.0,
            entry_date=datetime.now(),
            is_active=True
        )
    ]
    
    for position in positions:
        session.add(position)
    
    session.commit()
    
    print(f'Test data created: Portfolio ID {portfolio.id} with {len(positions)} positions')
    
except Exception as e:
    session.rollback()
    print(f'Error creating test data: {e}')
    raise
finally:
    session.close()
"
    
    if [ $? -eq 0 ]; then
        print_success "Test data created successfully"
    else
        print_error "Failed to create test data"
        return 1
    fi
}

# Function to verify test data exists
verify_test_data() {
    local expected_portfolios="$1"
    local expected_positions="$2"
    
    print_status "Verifying test data persistence..."
    
    # Execute Python script inside container to verify data
    local result=$(docker exec "$CONTAINER_NAME" python -c "
import sys
sys.path.append('/opt/crypto-robot/app')
sys.path.append('/opt/crypto-robot/app/src')

from database import get_db_manager, Portfolio, Position

try:
    # Get database manager
    db_manager = get_db_manager()
    session = db_manager.get_session()
    
    # Count portfolios and positions
    portfolio_count = session.query(Portfolio).count()
    position_count = session.query(Position).count()
    
    print(f'{portfolio_count},{position_count}')
    
    # Get portfolio details
    portfolios = session.query(Portfolio).all()
    for portfolio in portfolios:
        print(f'Portfolio {portfolio.id}: BNB Reserve={portfolio.bnb_reserve}, Cycle={portfolio.current_cycle}')
    
    # Get position details
    positions = session.query(Position).all()
    for position in positions:
        print(f'Position {position.id}: {position.symbol} - Qty={position.quantity}, Entry=${position.entry_price}')
    
    session.close()
    
except Exception as e:
    print(f'Error verifying data: {e}')
    print('0,0')
" 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        local counts=$(echo "$result" | head -n 1)
        local portfolios=$(echo "$counts" | cut -d',' -f1)
        local positions=$(echo "$counts" | cut -d',' -f2)
        
        print_status "Found $portfolios portfolios and $positions positions"
        
        if [ "$portfolios" = "$expected_portfolios" ] && [ "$positions" = "$expected_positions" ]; then
            print_success "Data verification passed: Expected $expected_portfolios portfolios and $expected_positions positions"
            return 0
        else
            print_error "Data verification failed: Expected $expected_portfolios portfolios and $expected_positions positions, found $portfolios portfolios and $positions positions"
            return 1
        fi
    else
        print_error "Failed to verify test data"
        return 1
    fi
}

# Function to check database file persistence on host
check_database_file() {
    print_status "Checking database file on host filesystem..."
    
    local db_file="$TEST_DATABASE_DIR/test_crypto_robot.db"
    
    if [ -f "$db_file" ]; then
        local file_size=$(stat -f%z "$db_file" 2>/dev/null || stat -c%s "$db_file" 2>/dev/null || echo "unknown")
        print_success "Database file exists on host: $db_file (size: $file_size bytes)"
        
        # Check if file is readable
        if [ -r "$db_file" ]; then
            print_success "Database file is readable"
        else
            print_error "Database file is not readable"
            return 1
        fi
        
        return 0
    else
        print_error "Database file not found on host: $db_file"
        return 1
    fi
}

# Function to run complete persistence test
run_persistence_test() {
    print_status "Running complete database persistence test..."
    echo "=============================================="
    
    local test_passed=true
    
    # Test 1: Initial container start and data creation
    print_status "Test 1: Initial container start and data creation"
    if start_test_container && create_test_data && verify_test_data "1" "2" && check_database_file; then
        print_success "Test 1 passed: Initial data creation successful"
    else
        print_error "Test 1 failed: Initial data creation failed"
        test_passed=false
    fi
    
    echo ""
    
    # Test 2: Container restart and data persistence
    print_status "Test 2: Container restart and data persistence"
    stop_test_container
    sleep 2
    
    if start_test_container && verify_test_data "1" "2" && check_database_file; then
        print_success "Test 2 passed: Data persisted after container restart"
    else
        print_error "Test 2 failed: Data lost after container restart"
        test_passed=false
    fi
    
    echo ""
    
    # Test 3: Container removal and data persistence
    print_status "Test 3: Container removal and data persistence"
    docker stop "$CONTAINER_NAME"
    docker rm "$CONTAINER_NAME"
    sleep 2
    
    if start_test_container && verify_test_data "1" "2" && check_database_file; then
        print_success "Test 3 passed: Data persisted after container removal"
    else
        print_error "Test 3 failed: Data lost after container removal"
        test_passed=false
    fi
    
    echo ""
    
    # Test 4: Database file permissions and access
    print_status "Test 4: Database file permissions and access"
    local db_file="$TEST_DATABASE_DIR/test_crypto_robot.db"
    
    if [ -f "$db_file" ] && [ -r "$db_file" ] && [ -w "$db_file" ]; then
        print_success "Test 4 passed: Database file has correct permissions"
    else
        print_error "Test 4 failed: Database file permissions incorrect"
        test_passed=false
    fi
    
    echo ""
    echo "=============================================="
    
    if [ "$test_passed" = true ]; then
        print_success "ALL TESTS PASSED: Database persistence is working correctly"
        return 0
    else
        print_error "SOME TESTS FAILED: Database persistence has issues"
        return 1
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  test     - Run complete database persistence test (default)"
    echo "  setup    - Setup test environment only"
    echo "  cleanup  - Cleanup test environment"
    echo "  help     - Show this help message"
    echo ""
    echo "This script tests SQLite3 database persistence across container lifecycle:"
    echo "1. Creates a test container with database volume mount"
    echo "2. Creates test data in the database"
    echo "3. Restarts the container and verifies data persistence"
    echo "4. Removes the container and verifies data persistence"
    echo "5. Checks database file permissions and access"
}

# Main function
main() {
    local command="${1:-test}"
    
    case "$command" in
        "test")
            print_status "Starting database persistence test..."
            setup_test
            
            if run_persistence_test; then
                print_success "Database persistence test completed successfully!"
                cleanup_test
                exit 0
            else
                print_error "Database persistence test failed!"
                cleanup_test
                exit 1
            fi
            ;;
        "setup")
            setup_test
            print_success "Test environment setup completed"
            ;;
        "cleanup")
            cleanup_test
            print_success "Test environment cleanup completed"
            ;;
        "help"|"-h"|"--help")
            show_usage
            ;;
        *)
            print_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

# Trap to cleanup on exit
trap cleanup_test EXIT

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi