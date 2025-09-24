#!/bin/bash
# Crypto Robot Docker Cleanup Script
# Removes Docker containers, images, and volumes after migration to Python deployment

set -e

echo "🧹 Crypto Robot Docker Cleanup"
echo "=============================="

# Configuration
CLEANUP_LOG="/tmp/docker-cleanup-$(date +%Y%m%d-%H%M%S).log"

# Cleanup counters
CONTAINERS_REMOVED=0
IMAGES_REMOVED=0
VOLUMES_REMOVED=0
NETWORKS_REMOVED=0

# Function to log messages
log_message() {
    local message="$1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $message" | tee -a "$CLEANUP_LOG"
}

# Function to check if Docker is available
check_docker_available() {
    if ! command -v docker &> /dev/null; then
        log_message "Docker not found on system"
        echo "⚠️  Docker not found - nothing to cleanup"
        exit 0
    fi
    
    if ! docker info &> /dev/null; then
        log_message "Docker daemon not running"
        echo "⚠️  Docker daemon not running - cannot perform cleanup"
        exit 1
    fi
    
    log_message "Docker is available and running"
}

# Function to list crypto-robot related Docker artifacts
list_docker_artifacts() {
    echo "🔍 Scanning for crypto-robot Docker artifacts..."
    log_message "Scanning for crypto-robot Docker artifacts"
    
    # List containers
    local containers=$(docker ps -a --filter "name=crypto-robot" --format "{{.Names}}" 2>/dev/null || true)
    if [ -n "$containers" ]; then
        echo ""
        echo "📦 Found containers:"
        echo "$containers" | while read -r container; do
            local status=$(docker ps -a --filter "name=$container" --format "{{.Status}}")
            echo "  - $container ($status)"
            log_message "Found container: $container ($status)"
        done
    else
        echo "  No crypto-robot containers found"
        log_message "No crypto-robot containers found"
    fi
    
    # List images
    local images=$(docker images --filter "reference=*crypto-robot*" --format "{{.Repository}}:{{.Tag}}" 2>/dev/null || true)
    if [ -n "$images" ]; then
        echo ""
        echo "🖼️  Found images:"
        echo "$images" | while read -r image; do
            local size=$(docker images --filter "reference=$image" --format "{{.Size}}")
            echo "  - $image ($size)"
            log_message "Found image: $image ($size)"
        done
    else
        echo "  No crypto-robot images found"
        log_message "No crypto-robot images found"
    fi
    
    # List volumes
    local volumes=$(docker volume ls --filter "name=crypto-robot" --format "{{.Name}}" 2>/dev/null || true)
    if [ -n "$volumes" ]; then
        echo ""
        echo "💾 Found volumes:"
        echo "$volumes" | while read -r volume; do
            echo "  - $volume"
            log_message "Found volume: $volume"
        done
    else
        echo "  No crypto-robot volumes found"
        log_message "No crypto-robot volumes found"
    fi
    
    # List networks
    local networks=$(docker network ls --filter "name=crypto-robot" --format "{{.Name}}" 2>/dev/null || true)
    if [ -n "$networks" ]; then
        echo ""
        echo "🌐 Found networks:"
        echo "$networks" | while read -r network; do
            echo "  - $network"
            log_message "Found network: $network"
        done
    else
        echo "  No crypto-robot networks found"
        log_message "No crypto-robot networks found"
    fi
    
    echo ""
}

# Function to stop and remove containers
cleanup_containers() {
    log_message "Starting container cleanup"
    
    local containers=$(docker ps -a --filter "name=crypto-robot" --format "{{.Names}}" 2>/dev/null || true)
    
    if [ -n "$containers" ]; then
        echo "🛑 Stopping and removing containers..."
        
        echo "$containers" | while read -r container; do
            # Stop container if running
            if docker ps --filter "name=$container" --format "{{.Names}}" | grep -q "$container"; then
                echo "  Stopping: $container"
                log_message "Stopping container: $container"
                docker stop "$container" >/dev/null 2>&1 || true
            fi
            
            # Remove container
            echo "  Removing: $container"
            log_message "Removing container: $container"
            if docker rm "$container" >/dev/null 2>&1; then
                CONTAINERS_REMOVED=$((CONTAINERS_REMOVED + 1))
                log_message "Successfully removed container: $container"
            else
                log_message "Failed to remove container: $container"
            fi
        done
        
        echo "✅ Container cleanup completed ($CONTAINERS_REMOVED removed)"
    else
        echo "  No containers to remove"
        log_message "No containers to remove"
    fi
}

# Function to remove images
cleanup_images() {
    log_message "Starting image cleanup"
    
    local images=$(docker images --filter "reference=*crypto-robot*" --format "{{.Repository}}:{{.Tag}}" 2>/dev/null || true)
    
    if [ -n "$images" ]; then
        echo "🖼️  Removing images..."
        
        echo "$images" | while read -r image; do
            echo "  Removing: $image"
            log_message "Removing image: $image"
            if docker rmi "$image" >/dev/null 2>&1; then
                IMAGES_REMOVED=$((IMAGES_REMOVED + 1))
                log_message "Successfully removed image: $image"
            else
                log_message "Failed to remove image: $image (may be in use)"
            fi
        done
        
        echo "✅ Image cleanup completed ($IMAGES_REMOVED removed)"
    else
        echo "  No images to remove"
        log_message "No images to remove"
    fi
}

# Function to remove volumes
cleanup_volumes() {
    log_message "Starting volume cleanup"
    
    local volumes=$(docker volume ls --filter "name=crypto-robot" --format "{{.Name}}" 2>/dev/null || true)
    
    if [ -n "$volumes" ]; then
        echo "💾 Removing volumes..."
        
        echo "$volumes" | while read -r volume; do
            echo "  Removing: $volume"
            log_message "Removing volume: $volume"
            if docker volume rm "$volume" >/dev/null 2>&1; then
                VOLUMES_REMOVED=$((VOLUMES_REMOVED + 1))
                log_message "Successfully removed volume: $volume"
            else
                log_message "Failed to remove volume: $volume (may be in use)"
            fi
        done
        
        echo "✅ Volume cleanup completed ($VOLUMES_REMOVED removed)"
    else
        echo "  No volumes to remove"
        log_message "No volumes to remove"
    fi
}

# Function to remove networks
cleanup_networks() {
    log_message "Starting network cleanup"
    
    local networks=$(docker network ls --filter "name=crypto-robot" --format "{{.Name}}" 2>/dev/null | grep -v "bridge\|host\|none" || true)
    
    if [ -n "$networks" ]; then
        echo "🌐 Removing networks..."
        
        echo "$networks" | while read -r network; do
            echo "  Removing: $network"
            log_message "Removing network: $network"
            if docker network rm "$network" >/dev/null 2>&1; then
                NETWORKS_REMOVED=$((NETWORKS_REMOVED + 1))
                log_message "Successfully removed network: $network"
            else
                log_message "Failed to remove network: $network (may be in use)"
            fi
        done
        
        echo "✅ Network cleanup completed ($NETWORKS_REMOVED removed)"
    else
        echo "  No networks to remove"
        log_message "No networks to remove"
    fi
}

# Function to cleanup dangling resources
cleanup_dangling_resources() {
    log_message "Cleaning up dangling Docker resources"
    
    echo "🧹 Cleaning up dangling resources..."
    
    # Remove dangling images
    local dangling_images=$(docker images -f "dangling=true" -q 2>/dev/null || true)
    if [ -n "$dangling_images" ]; then
        echo "  Removing dangling images..."
        echo "$dangling_images" | xargs docker rmi >/dev/null 2>&1 || true
        log_message "Removed dangling images"
    fi
    
    # Remove unused volumes
    echo "  Removing unused volumes..."
    docker volume prune -f >/dev/null 2>&1 || true
    log_message "Removed unused volumes"
    
    # Remove unused networks
    echo "  Removing unused networks..."
    docker network prune -f >/dev/null 2>&1 || true
    log_message "Removed unused networks"
    
    echo "✅ Dangling resource cleanup completed"
}

# Function to verify cleanup
verify_cleanup() {
    log_message "Verifying cleanup completion"
    
    echo "🔍 Verifying cleanup..."
    
    # Check for remaining containers
    local remaining_containers=$(docker ps -a --filter "name=crypto-robot" --format "{{.Names}}" 2>/dev/null || true)
    if [ -n "$remaining_containers" ]; then
        echo "⚠️  Warning: Some containers still exist:"
        echo "$remaining_containers" | sed 's/^/  - /'
        log_message "Warning: Remaining containers found"
    else
        echo "✅ No crypto-robot containers remaining"
        log_message "No crypto-robot containers remaining"
    fi
    
    # Check for remaining images
    local remaining_images=$(docker images --filter "reference=*crypto-robot*" --format "{{.Repository}}:{{.Tag}}" 2>/dev/null || true)
    if [ -n "$remaining_images" ]; then
        echo "⚠️  Warning: Some images still exist:"
        echo "$remaining_images" | sed 's/^/  - /'
        log_message "Warning: Remaining images found"
    else
        echo "✅ No crypto-robot images remaining"
        log_message "No crypto-robot images remaining"
    fi
    
    # Check for remaining volumes
    local remaining_volumes=$(docker volume ls --filter "name=crypto-robot" --format "{{.Name}}" 2>/dev/null || true)
    if [ -n "$remaining_volumes" ]; then
        echo "⚠️  Warning: Some volumes still exist:"
        echo "$remaining_volumes" | sed 's/^/  - /'
        log_message "Warning: Remaining volumes found"
    else
        echo "✅ No crypto-robot volumes remaining"
        log_message "No crypto-robot volumes remaining"
    fi
}

# Function to display cleanup summary
display_cleanup_summary() {
    echo ""
    log_message "📊 Cleanup Summary"
    log_message "=================="
    log_message "Containers removed: $CONTAINERS_REMOVED"
    log_message "Images removed: $IMAGES_REMOVED"
    log_message "Volumes removed: $VOLUMES_REMOVED"
    log_message "Networks removed: $NETWORKS_REMOVED"
    log_message "Cleanup log: $CLEANUP_LOG"
    
    echo "📊 Cleanup Summary"
    echo "=================="
    echo "Containers removed: $CONTAINERS_REMOVED"
    echo "Images removed: $IMAGES_REMOVED"
    echo "Volumes removed: $VOLUMES_REMOVED"
    echo "Networks removed: $NETWORKS_REMOVED"
    echo ""
    
    local total_removed=$((CONTAINERS_REMOVED + IMAGES_REMOVED + VOLUMES_REMOVED + NETWORKS_REMOVED))
    
    if [ $total_removed -gt 0 ]; then
        echo "🎉 Docker cleanup completed successfully!"
        echo "✅ Removed $total_removed Docker artifacts"
    else
        echo "ℹ️  No Docker artifacts found to remove"
        echo "✅ System is already clean"
    fi
    
    echo ""
    echo "📝 Detailed log: $CLEANUP_LOG"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --dry-run       Show what would be removed without making changes"
    echo "  --containers    Remove only containers"
    echo "  --images        Remove only images"
    echo "  --volumes       Remove only volumes"
    echo "  --networks      Remove only networks"
    echo "  --all           Remove all crypto-robot Docker artifacts (default)"
    echo "  --force         Skip confirmation prompts"
    echo "  --help          Show this help message"
    echo ""
    echo "This script removes Docker artifacts related to crypto-robot after"
    echo "migration to Python deployment. It will remove:"
    echo "- Containers (crypto-robot-*)"
    echo "- Images (*crypto-robot*)"
    echo "- Volumes (crypto-robot-*)"
    echo "- Networks (crypto-robot-*)"
    echo ""
}

# Parse command line arguments
DRY_RUN=false
CONTAINERS_ONLY=false
IMAGES_ONLY=false
VOLUMES_ONLY=false
NETWORKS_ONLY=false
FORCE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --containers)
            CONTAINERS_ONLY=true
            shift
            ;;
        --images)
            IMAGES_ONLY=true
            shift
            ;;
        --volumes)
            VOLUMES_ONLY=true
            shift
            ;;
        --networks)
            NETWORKS_ONLY=true
            shift
            ;;
        --all)
            # Default behavior
            shift
            ;;
        --force)
            FORCE=true
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
    log_message "🚀 Starting Docker cleanup"
    log_message "Timestamp: $(date)"
    
    echo "🚀 Starting Docker cleanup..."
    echo "📝 Cleanup log: $CLEANUP_LOG"
    echo ""
    
    if [ "$DRY_RUN" = "true" ]; then
        echo "🔍 DRY RUN MODE - No changes will be made"
        echo ""
    fi
    
    # Check Docker availability
    check_docker_available
    
    # List artifacts
    list_docker_artifacts
    
    # Confirm cleanup
    if [ "$DRY_RUN" = "false" ] && [ "$FORCE" = "false" ]; then
        echo "⚠️  This will permanently remove crypto-robot Docker artifacts."
        echo ""
        read -p "Continue with cleanup? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Cleanup cancelled"
            exit 0
        fi
        echo ""
    fi
    
    if [ "$DRY_RUN" = "false" ]; then
        # Perform cleanup based on options
        if [ "$CONTAINERS_ONLY" = "true" ]; then
            cleanup_containers
        elif [ "$IMAGES_ONLY" = "true" ]; then
            cleanup_images
        elif [ "$VOLUMES_ONLY" = "true" ]; then
            cleanup_volumes
        elif [ "$NETWORKS_ONLY" = "true" ]; then
            cleanup_networks
        else
            # Clean up everything
            cleanup_containers
            cleanup_images
            cleanup_volumes
            cleanup_networks
            cleanup_dangling_resources
        fi
        
        # Verify cleanup
        verify_cleanup
    else
        echo "🔍 DRY RUN - Would remove the artifacts listed above"
    fi
    
    display_cleanup_summary
}

# Execute main function
main "$@"