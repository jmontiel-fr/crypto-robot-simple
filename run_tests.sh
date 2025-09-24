#!/bin/bash

# Comprehensive test runner for crypto-robot dockerization
# Usage: ./run_tests.sh [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

show_usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --quick              Run quick validation only"
    echo "  --execution-modes    Run execution modes tests only"
    echo "  --certificates       Run certificate tests only"
    echo "  --docker             Run Docker tests only"
    echo "  --verbose            Enable verbose output"
    echo "  --help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                   # Run all tests"
    echo "  $0 --quick           # Quick validation"
    echo "  $0 --docker          # Docker tests only"
}

# Parse arguments
QUICK_MODE=false
TEST_CATEGORIES=""
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            QUICK_MODE=true
            shift
            ;;
        --execution-modes)
            TEST_CATEGORIES="$TEST_CATEGORIES execution_modes"
            shift
            ;;
        --certificates)
            TEST_CATEGORIES="$TEST_CATEGORIES certificate"
            shift
            ;;
        --docker)
            TEST_CATEGORIES="$TEST_CATEGORIES docker"
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
print_status "Starting crypto-robot dockerization tests..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not found"
    exit 1
fi

# Build command
CMD="python3 tests/run_all_tests.py"

if [ "$QUICK_MODE" = true ]; then
    CMD="$CMD --quick"
fi

if [ -n "$TEST_CATEGORIES" ]; then
    CMD="$CMD --categories $TEST_CATEGORIES"
fi

if [ "$VERBOSE" = true ]; then
    CMD="$CMD --verbose"
fi

# Execute tests
print_status "Executing: $CMD"
eval "$CMD"

# Check result
if [ $? -eq 0 ]; then
    print_success "All tests completed successfully!"
else
    print_error "Some tests failed. Please check the output above."
    exit 1
fi