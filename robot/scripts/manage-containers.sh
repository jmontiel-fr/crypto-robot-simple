#!/bin/bash

# Docker container management script for crypto-robot
# This script provides comprehensive container lifecycle management
# Usage: ./scripts/manage-containers.sh <command> [options]

set -e  # Exit on any error

# Configuration
DEFAULT_IMAGE="jmontiel/crypto-robot:latest"
DEFAULT_CERTIFICATE="jack.crypto-robot-itechsource.com"
DEFAULT_ENV_FILE="robot/.env"
APP_DIR="/opt/crypto-robot"

# Container names
ROBOT_CONTAINER="crypto-robot-app"
WEBAPP_CONTAINER="crypto-robot-webapp"
COMBINED_CONTAINER="crypto-robot-combined"

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
    echo "  start-robot      - Start trading robot container"
    echo "  start-webapp     - Start web application container"
    echo "  start-combined   - Start combined robot+webapp container"
    echo "  stop-robot       - Stop trading robot container"
    echo "  stop-webapp      - Stop web application container"
    echo "  stop-all         - Stop all crypto-robot containers"
    echo "  restart-robot    - Restart trading robot container"
    echo "  restart-webapp   - Restart web application container"
    echo "  status           - Show status of all containers"
    echo "  logs-robot       - Show robot container logs"
    echo "  logs-webapp      - Show webapp container logs"
    echo "  update-image     - Pull latest Docker image"
    echo "  cleanup          - Remove stopped containers and unused images"
    echo "  help             - Show this help message"
    echo ""
    echo "Options:"
    echo "  --image IMAGE    - Docker image to use (default: $DEFAULT_IMAGE)"
    echo "  --cert CERT      - Certificate hostname (default: $DEFAULT_CERTIFICATE)"
    echo "  --env-file FILE  - Environment file (default: $DEFAULT_ENV_FILE)"
    echo "  --port PORT      - Override port mapping"
    echo "  --detach         - Run in detached mode (default)"
    echo "  --interactive    - Run in interactive mode"
    echo ""
    echo "Examples:"
    echo "  $0 start-robot                           # Start robot with defaults"
    echo "  $0 start-webapp --cert crypto-robot.local  # Start webapp with local cert"
    echo "  $0 status                                # Show all container status"
    echo "  $0 logs-robot                           # Show robot logs"
    echo "  $0 update-image                         # Update to latest image"
}

# Function to parse command line arguments
parse_args() {
    COMMAND=""
    IMAGE="$DEFAULT_IMAGE"
    CERTIFICATE="$DEFAULT_CERTIFICATE"
    ENV_FILE="$DEFAULT_ENV_FILE"
    PORT_OVERRIDE=""
    RUN_MODE="detached"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --image)
                IMAGE="$2"
                shift 2
                ;;
            --cert)
                CERTIFICATE="$2"
                shift 2
                ;;
            --env-file)
                ENV_FILE="$2"
                shift 2
                ;;
            --port)
                PORT_OVERRIDE="$2"
                shift 2
                ;;
            --detach)
                RUN_MODE="detached"
                shift
                ;;
            --interactive)
                RUN_MODE="interactive"
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

# Function to get port from .env file
get_port_from_env() {
    local env_file="$1"
    
    if [ -f "$env_file" ]; then
        local port=$(grep "^FLASK_PORT=" "$env_file" | cut -d'=' -f2 | tr -d '"' | tr -d "'" || echo "")
        if [ -n "$port" ]; then
            echo "$port"
            return 0
        fi
    fi
    
    # Default ports based on certificate
    case "$CERTIFICATE" in
        "crypto-robot.local")
            echo "5000"
            ;;
        *)
            echo "5443"
            ;;
    esac
}

# Function to check if container exists
container_exists() {
    local container_name="$1"
    docker ps -a --format '{{.Names}}' | grep -q "^${container_name}$"
}

# Function to check if container is running
container_running() {
    local container_name="$1"
    docker ps --format '{{.Names}}' | grep -q "^${container_name}$"
}

# Function to stop and remove container if it exists
stop_and_remove_container() {
    local container_name="$1"
    
    if container_running "$container_name"; then
        print_status "Stopping running container: $container_name"
        docker stop "$container_name"
    fi
    
    if container_exists "$container_name"; then
        print_status "Removing existing container: $container_name"
        docker rm "$container_name"
    fi
}

# Function to start robot container
start_robot() {
    print_status "Starting trading robot container..."
    
    # Stop existing container if running
    stop_and_remove_container "$ROBOT_CONTAINER"
    
    # Get port configuration
    local port=$(get_port_from_env "$ENV_FILE")
    if [ -n "$PORT_OVERRIDE" ]; then
        port="$PORT_OVERRIDE"
    fi
    
    # Validate environment file
    if [ ! -f "$ENV_FILE" ]; then
        print_error "Environment file not found: $ENV_FILE"
        print_error "Please run ./scripts/create-env.sh first"
        exit 1
    fi
    
    # Ensure database directory exists
    if [ ! -d "database" ]; then
        print_status "Creating database directory for persistence..."
        mkdir -p database
    fi
    
    # Create base64 encoded env content
    local env_content=$(base64 -w 0 "$ENV_FILE")
    
    # Build docker run command
    local docker_cmd="docker run"
    
    if [ "$RUN_MODE" = "detached" ]; then
        docker_cmd="$docker_cmd -d"
    else
        docker_cmd="$docker_cmd -it"
    fi
    
    docker_cmd="$docker_cmd --name $ROBOT_CONTAINER"
    docker_cmd="$docker_cmd -e ENV_CONTENT=\"$env_content\""
    docker_cmd="$docker_cmd -e CERTIFICATE=\"$CERTIFICATE\""
    docker_cmd="$docker_cmd -e MODE=\"robot\""
    docker_cmd="$docker_cmd -v \$(pwd)/database:/opt/crypto-robot/database"
    docker_cmd="$docker_cmd --restart unless-stopped"
    docker_cmd="$docker_cmd -p $port:$port"
    docker_cmd="$docker_cmd $IMAGE"
    
    print_status "Executing: $docker_cmd"
    eval "$docker_cmd"
    
    print_success "Trading robot container started successfully!"
    print_status "Container name: $ROBOT_CONTAINER"
    print_status "Port mapping: $port:$port"
    print_status "Certificate: $CERTIFICATE"
    print_status "Image: $IMAGE"
}

# Function to start webapp container
start_webapp() {
    print_status "Starting web application container..."
    
    # Stop existing container if running
    stop_and_remove_container "$WEBAPP_CONTAINER"
    
    # Get port configuration
    local port=$(get_port_from_env "$ENV_FILE")
    if [ -n "$PORT_OVERRIDE" ]; then
        port="$PORT_OVERRIDE"
    fi
    
    # Validate environment file
    if [ ! -f "$ENV_FILE" ]; then
        print_error "Environment file not found: $ENV_FILE"
        print_error "Please run ./scripts/create-env.sh first"
        exit 1
    fi
    
    # Ensure database directory exists
    if [ ! -d "database" ]; then
        print_status "Creating database directory for persistence..."
        mkdir -p database
    fi
    
    # Create base64 encoded env content
    local env_content=$(base64 -w 0 "$ENV_FILE")
    
    # Build docker run command
    local docker_cmd="docker run"
    
    if [ "$RUN_MODE" = "detached" ]; then
        docker_cmd="$docker_cmd -d"
    else
        docker_cmd="$docker_cmd -it"
    fi
    
    docker_cmd="$docker_cmd --name $WEBAPP_CONTAINER"
    docker_cmd="$docker_cmd -e ENV_CONTENT=\"$env_content\""
    docker_cmd="$docker_cmd -e CERTIFICATE=\"$CERTIFICATE\""
    docker_cmd="$docker_cmd -e MODE=\"webapp\""
    docker_cmd="$docker_cmd -v \$(pwd)/database:/opt/crypto-robot/database"
    docker_cmd="$docker_cmd --restart unless-stopped"
    docker_cmd="$docker_cmd -p $port:$port"
    docker_cmd="$docker_cmd $IMAGE"
    
    print_status "Executing: $docker_cmd"
    eval "$docker_cmd"
    
    print_success "Web application container started successfully!"
    print_status "Container name: $WEBAPP_CONTAINER"
    print_status "Port mapping: $port:$port"
    print_status "Certificate: $CERTIFICATE"
    print_status "Image: $IMAGE"
}

# Function to start combined container
start_combined() {
    print_status "Starting combined robot+webapp container..."
    
    # Stop existing container if running
    stop_and_remove_container "$COMBINED_CONTAINER"
    
    # Get port configuration
    local port=$(get_port_from_env "$ENV_FILE")
    if [ -n "$PORT_OVERRIDE" ]; then
        port="$PORT_OVERRIDE"
    fi
    
    # Validate environment file
    if [ ! -f "$ENV_FILE" ]; then
        print_error "Environment file not found: $ENV_FILE"
        print_error "Please run ./scripts/create-env.sh first"
        exit 1
    fi
    
    # Ensure database directory exists
    if [ ! -d "database" ]; then
        print_status "Creating database directory for persistence..."
        mkdir -p database
    fi
    
    # Create base64 encoded env content
    local env_content=$(base64 -w 0 "$ENV_FILE")
    
    # Build docker run command
    local docker_cmd="docker run"
    
    if [ "$RUN_MODE" = "detached" ]; then
        docker_cmd="$docker_cmd -d"
    else
        docker_cmd="$docker_cmd -it"
    fi
    
    docker_cmd="$docker_cmd --name $COMBINED_CONTAINER"
    docker_cmd="$docker_cmd -e ENV_CONTENT=\"$env_content\""
    docker_cmd="$docker_cmd -e CERTIFICATE=\"$CERTIFICATE\""
    docker_cmd="$docker_cmd -e MODE=\"both\""
    docker_cmd="$docker_cmd -v \$(pwd)/database:/opt/crypto-robot/database"
    docker_cmd="$docker_cmd --restart unless-stopped"
    docker_cmd="$docker_cmd -p $port:$port"
    docker_cmd="$docker_cmd $IMAGE"
    
    print_status "Executing: $docker_cmd"
    eval "$docker_cmd"
    
    print_success "Combined container started successfully!"
    print_status "Container name: $COMBINED_CONTAINER"
    print_status "Port mapping: $port:$port"
    print_status "Certificate: $CERTIFICATE"
    print_status "Image: $IMAGE"
}

# Function to stop containers
stop_container() {
    local container_name="$1"
    local service_name="$2"
    
    if container_running "$container_name"; then
        print_status "Stopping $service_name container: $container_name"
        docker stop "$container_name"
        print_success "$service_name container stopped successfully!"
    else
        print_warning "$service_name container is not running: $container_name"
    fi
}

# Function to show container status
show_status() {
    print_status "Crypto Robot Container Status:"
    echo "=================================="
    
    # Check each container
    local containers=("$ROBOT_CONTAINER:Trading Robot" "$WEBAPP_CONTAINER:Web Application" "$COMBINED_CONTAINER:Combined Service")
    
    for container_info in "${containers[@]}"; do
        IFS=':' read -r container_name service_name <<< "$container_info"
        
        echo ""
        echo "$service_name ($container_name):"
        
        if container_running "$container_name"; then
            echo "  Status: ✅ Running"
            
            # Get container details
            local image=$(docker inspect "$container_name" --format '{{.Config.Image}}' 2>/dev/null || echo "unknown")
            local created=$(docker inspect "$container_name" --format '{{.Created}}' 2>/dev/null || echo "unknown")
            local ports=$(docker port "$container_name" 2>/dev/null || echo "none")
            
            echo "  Image: $image"
            echo "  Created: $created"
            echo "  Ports: $ports"
            
        elif container_exists "$container_name"; then
            echo "  Status: ⏹️ Stopped"
            local image=$(docker inspect "$container_name" --format '{{.Config.Image}}' 2>/dev/null || echo "unknown")
            echo "  Image: $image"
        else
            echo "  Status: ❌ Not found"
        fi
    done
    
    echo ""
    echo "=================================="
    
    # Show Docker images
    print_status "Available Images:"
    docker images jmontiel/crypto-robot --format "table {{.Repository}}\t{{.Tag}}\t{{.CreatedAt}}\t{{.Size}}" || true
    
    echo ""
    
    # Show system resources
    print_status "Docker System Info:"
    echo "Running containers: $(docker ps -q | wc -l)"
    echo "Total containers: $(docker ps -a -q | wc -l)"
    echo "Images: $(docker images -q | wc -l)"
}

# Function to show logs
show_logs() {
    local container_name="$1"
    local service_name="$2"
    
    if container_exists "$container_name"; then
        print_status "Showing logs for $service_name container: $container_name"
        echo "=================================="
        docker logs --tail 50 -f "$container_name"
    else
        print_error "$service_name container not found: $container_name"
        exit 1
    fi
}

# Function to update image
update_image() {
    print_status "Updating Docker image: $IMAGE"
    docker pull "$IMAGE"
    print_success "Image updated successfully!"
    
    print_status "Updated image details:"
    docker images "$IMAGE" --format "table {{.Repository}}\t{{.Tag}}\t{{.CreatedAt}}\t{{.Size}}"
}

# Function to cleanup
cleanup() {
    print_status "Cleaning up Docker resources..."
    
    # Remove stopped containers
    local stopped_containers=$(docker ps -a -q --filter "status=exited" --filter "name=crypto-robot" 2>/dev/null || true)
    if [ -n "$stopped_containers" ]; then
        print_status "Removing stopped crypto-robot containers..."
        docker rm $stopped_containers
        print_success "Stopped containers removed"
    else
        print_status "No stopped crypto-robot containers to remove"
    fi
    
    # Remove unused images
    print_status "Removing unused images..."
    docker image prune -f
    
    # Show cleanup results
    print_success "Cleanup completed!"
    show_status
}

# Main function
main() {
    # Change to app directory if it exists and we're not already there
    if [ -d "$APP_DIR" ] && [ "$(pwd)" != "$APP_DIR" ]; then
        print_status "Changing to application directory: $APP_DIR"
        cd "$APP_DIR"
    fi
    
    # Parse arguments
    parse_args "$@"
    
    print_status "Container management command: $COMMAND"
    print_status "Working directory: $(pwd)"
    
    # Execute command
    case "$COMMAND" in
        "start-robot")
            start_robot
            ;;
        "start-webapp")
            start_webapp
            ;;
        "start-combined")
            start_combined
            ;;
        "stop-robot")
            stop_container "$ROBOT_CONTAINER" "Trading Robot"
            ;;
        "stop-webapp")
            stop_container "$WEBAPP_CONTAINER" "Web Application"
            ;;
        "stop-all")
            stop_container "$ROBOT_CONTAINER" "Trading Robot"
            stop_container "$WEBAPP_CONTAINER" "Web Application"
            stop_container "$COMBINED_CONTAINER" "Combined Service"
            ;;
        "restart-robot")
            stop_container "$ROBOT_CONTAINER" "Trading Robot"
            sleep 2
            start_robot
            ;;
        "restart-webapp")
            stop_container "$WEBAPP_CONTAINER" "Web Application"
            sleep 2
            start_webapp
            ;;
        "status")
            show_status
            ;;
        "logs-robot")
            show_logs "$ROBOT_CONTAINER" "Trading Robot"
            ;;
        "logs-webapp")
            show_logs "$WEBAPP_CONTAINER" "Web Application"
            ;;
        "update-image")
            update_image
            ;;
        "cleanup")
            cleanup
            ;;
        *)
            print_error "Unknown command: $COMMAND"
            show_usage
            exit 1
            ;;
    esac
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi