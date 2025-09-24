#!/bin/bash

# Container status script
# This is a convenience wrapper around manage-containers.sh
# Usage: ./scripts/container-status.sh [options]

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Call the main container management script
exec "$SCRIPT_DIR/manage-containers.sh" status "$@"