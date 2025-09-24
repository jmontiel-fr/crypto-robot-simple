#!/bin/bash

# Stop trading robot container script
# This is a convenience wrapper around manage-containers.sh
# Usage: ./scripts/stop-robot.sh [options]

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Call the main container management script
exec "$SCRIPT_DIR/manage-containers.sh" stop-robot "$@"