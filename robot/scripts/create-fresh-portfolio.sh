#!/bin/bash

# Create fresh portfolio script
# This is a convenience wrapper for portfolio management
# Usage: ./scripts/create-fresh-portfolio.sh [options]

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default to container execution if we're likely in a container environment
if [ -f "/.dockerenv" ] || [ -n "$CONTAINER" ]; then
    # We're in a container, execute directly
    exec "$SCRIPT_DIR/portfolio-manager.sh" create-fresh-fast --direct "$@"
else
    # We're not in a container, check if container is available
    if docker ps --format '{{.Names}}' | grep -q "^crypto-robot-app$"; then
        # Container is running, use it
        exec "$SCRIPT_DIR/portfolio-manager.sh" create-fresh-fast --container "$@"
    else
        # No container, execute directly
        exec "$SCRIPT_DIR/portfolio-manager.sh" create-fresh-fast --direct "$@"
    fi
fi