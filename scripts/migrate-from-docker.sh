#!/bin/bash
# Crypto Robot Docker to Python Migration Script
# Migrates from Docker-based deployment to direct Python execution

set -e

echo "🔄 Crypto Robot Docker to Python Migration"
echo "=========================================="

# Configuration
APP_PATH="/opt/crypto-robot"
BACKUP_DIR="/opt/crypto-robot-migration-backup-$(date +%Y%m%d-%H%M%S)"
MIGRATION_LOG="/tmp/migration-$(date +%Y%m%d-%H%M%S).log"

# Migration status tracking
MIGRATION_STEPS=0
COMPLETED_STEPS=0
FAILED_STEPS=0

# Function to log messages
log_message() {
    local message="$1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $message" | tee -a "$MIGRATION_LOG"
}

# Function to run migration step
run_migration_step() {
    local step_name="$1"
    local step_function="$2"
    local is_critical="${3:-true}"
    
    MIGRATION_STEPS=$((MIGRATION_STEPS + 1))
    
    log_message "🔄 Step $MIGRATION_STEPS: $step_name"
    
    if $step_function; then
        log_message "✅ Completed: $step_name"
        COMPLETED_STEPS=$((COMPLETED_STEPS + 1))
        return 0
    else
        if [ "$is_critical" = "true" ]; then
            log_message "❌ Failed: $step_name"
            FAILED_STEPS=$((FAILED_STEPS + 1))
            return 1
        else
            log_message "⚠️  Warning: $step_name"
            return 0
        fi
    fi
}

# Function to check if Docker is installed and containers exist
check_docker_environment() {
    log_message "Checking Docker environment"
    
    if ! command -v docker &> /dev/null; then
        log_message "Docker not found - assuming clean installation"
        return 0
    fi
    
    # Check for existing containers
    local containers=$(docker ps -a --filter "name=crypto-robot" --format "{{.Names}}" 2>/dev/null || true)
    
    if [ -n "$containers" ]; then
        log_message "Found existing Docker containers:"
        echo "$containers" | while read -r container; do
            log_message "  - $container"
        done
        return 0
    else
        log_message "No existing crypto-robot containers found"
        return 0
    fi
}

# Function to backup Docker data
backup_docker_data() {
    log_message "Backing up Docker container data"
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    
    # Check for running containers and backup their data
    local containers=$(docker ps -a --filter "name=crypto-robot" --format "{{.Names}}" 2>/dev/null || true)
    
    if [ -n "$containers" ]; then
        echo "$containers" | while read -r container; do
            log_message "Backing up data from container: $container"
            
            # Backup database
            if docker exec "$container" test -d /opt/crypto-robot/database 2>/dev/null; then
                docker cp "$container:/opt/crypto-robot/database" "$BACKUP_DIR/database-$container" 2>/dev/null || true
                log_message "Database backed up from $container"
            fi
            
            # Backup logs
            if docker exec "$container" test -d /opt/crypto-robot/logs 2>/dev/null; then
                docker cp "$container:/opt/crypto-robot/logs" "$BACKUP_DIR/logs-$container" 2>/dev/null || true
                log_message "Logs backed up from $container"
            fi
            
            # Backup .env file
            if docker exec "$container" test -f /opt/crypto-robot/.env 2>/dev/null; then
                docker cp "$container:/opt/crypto-robot/.env" "$BACKUP_DIR/.env-$container" 2>/dev/null || true
                log_message "Environment file backed up from $container"
            fi
        done
    else
        log_message "No containers found to backup"
    fi
    
    # Backup any host-mounted data
    if [ -d "/opt/crypto-robot/database" ]; then
        cp -r /opt/crypto-robot/database "$BACKUP_DIR/host-database" 2>/dev/null || true
        log_message "Host database directory backed up"
    fi
    
    if [ -f "/opt/crypto-robot/.env" ]; then
        cp /opt/crypto-robot/.env "$BACKUP_DIR/host-.env" 2>/dev/null || true
        log_message "Host .env file backed up"
    fi
    
    return 0
}

# Function to stop and remove Docker containers
stop_docker_containers() {
    log_message "Stopping and removing Docker containers"
    
    local containers=$(docker ps -a --filter "name=crypto-robot" --format "{{.Names}}" 2>/dev/null || true)
    
    if [ -n "$containers" ]; then
        echo "$containers" | while read -r container; do
            log_message "Stopping container: $container"
            docker stop "$container" 2>/dev/null || true
            
            log_message "Removing container: $container"
            docker rm "$container" 2>/dev/null || true
        done
    fi
    
    # Remove Docker images (optional)
    local images=$(docker images --filter "reference=*crypto-robot*" --format "{{.Repository}}:{{.Tag}}" 2>/dev/null || true)
    
    if [ -n "$images" ]; then
        log_message "Found crypto-robot Docker images:"
        echo "$images" | while read -r image; do
            log_message "  - $image"
        done
        
        read -p "Remove Docker images? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "$images" | while read -r image; do
                log_message "Removing image: $image"
                docker rmi "$image" 2>/dev/null || true
            done
        fi
    fi
    
    return 0
}

# Function to setup Python environment
setup_python_environment() {
    log_message "Setting up Python environment"
    
    # Ensure we're in the correct directory
    cd "$APP_PATH"
    
    # Run Python environment setup
    if [ -f "scripts/setup-python-env.sh" ]; then
        chmod +x scripts/setup-python-env.sh
        ./scripts/setup-python-env.sh
        log_message "Python environment setup completed"
    else
        log_message "Python environment setup script not found"
        return 1
    fi
    
    return 0
}

# Function to migrate configuration
migrate_configuration() {
    log_message "Migrating configuration"
    
    # Look for backed up .env files
    local env_files=$(find "$BACKUP_DIR" -name ".env-*" -o -name "host-.env" 2>/dev/null || true)
    
    if [ -n "$env_files" ]; then
        # Use the first .env file found
        local source_env=$(echo "$env_files" | head -n1)
        log_message "Found environment file: $source_env"
        
        # Create .env from template if it doesn't exist
        if [ ! -f "$APP_PATH/.env" ]; then
            if [ -f "$APP_PATH/robot/.env.template" ]; then
                cp "$APP_PATH/robot/.env.template" "$APP_PATH/.env"
                log_message "Created .env from template"
            fi
        fi
        
        # Merge configurations
        if [ -f "$APP_PATH/scripts/manage-env.sh" ]; then
            chmod +x "$APP_PATH/scripts/manage-env.sh"
            "$APP_PATH/scripts/manage-env.sh" merge "$source_env"
            log_message "Configuration merged from Docker backup"
        fi
    else
        log_message "No Docker environment files found to migrate"
        
        # Create from template
        if [ -f "$APP_PATH/robot/.env.template" ] && [ ! -f "$APP_PATH/.env" ]; then
            cp "$APP_PATH/robot/.env.template" "$APP_PATH/.env"
            log_message "Created .env from template"
        fi
    fi
    
    # Update paths for direct Python deployment
    if [ -f "$APP_PATH/.env" ]; then
        # Update database paths
        sed -i 's|DATABASE_PATH=data|DATABASE_PATH=/opt/crypto-robot/database|g' "$APP_PATH/.env"
        sed -i 's|DATABASE_PATH=./database|DATABASE_PATH=/opt/crypto-robot/database|g' "$APP_PATH/.env"
        
        # Update SSL certificate paths
        sed -i 's|SSL_CERT_PATH=certs/|SSL_CERT_PATH=/opt/crypto-robot/certificates/|g' "$APP_PATH/.env"
        sed -i 's|SSL_KEY_PATH=certs/|SSL_KEY_PATH=/opt/crypto-robot/certificates/|g' "$APP_PATH/.env"
        
        log_message "Updated configuration paths for Python deployment"
    fi
    
    return 0
}

# Function to migrate database
migrate_database() {
    log_message "Migrating database"
    
    # Create database directory
    mkdir -p "$APP_PATH/database"
    
    # Look for backed up databases
    local db_dirs=$(find "$BACKUP_DIR" -type d -name "database-*" -o -name "host-database" 2>/dev/null || true)
    
    if [ -n "$db_dirs" ]; then
        # Use the first database found
        local source_db=$(echo "$db_dirs" | head -n1)
        log_message "Found database backup: $source_db"
        
        # Copy database files
        if [ -d "$source_db" ]; then
            cp -r "$source_db"/* "$APP_PATH/database/" 2>/dev/null || true
            log_message "Database files copied to $APP_PATH/database/"
            
            # Set proper permissions
            chown -R ec2-user:ec2-user "$APP_PATH/database" 2>/dev/null || true
            chmod -R 644 "$APP_PATH/database"/*.db 2>/dev/null || true
        fi
    else
        log_message "No database backup found - will start with fresh database"
    fi
    
    return 0
}

# Function to migrate logs
migrate_logs() {
    log_message "Migrating logs"
    
    # Create logs directory
    mkdir -p "$APP_PATH/logs"
    
    # Look for backed up logs
    local log_dirs=$(find "$BACKUP_DIR" -type d -name "logs-*" 2>/dev/null || true)
    
    if [ -n "$log_dirs" ]; then
        echo "$log_dirs" | while read -r log_dir; do
            if [ -d "$log_dir" ]; then
                # Copy log files with timestamp prefix
                local container_name=$(basename "$log_dir" | sed 's/logs-//')
                find "$log_dir" -name "*.log" -exec cp {} "$APP_PATH/logs/migrated-$container_name-$(basename {})" \; 2>/dev/null || true
            fi
        done
        log_message "Log files migrated to $APP_PATH/logs/"
    else
        log_message "No log backups found"
    fi
    
    # Set proper permissions
    chown -R ec2-user:ec2-user "$APP_PATH/logs" 2>/dev/null || true
    chmod -R 644 "$APP_PATH/logs"/*.log 2>/dev/null || true
    
    return 0
}

# Function to install systemd services
install_systemd_services() {
    log_message "Installing systemd services"
    
    if [ -f "$APP_PATH/scripts/install-systemd-services.sh" ]; then
        chmod +x "$APP_PATH/scripts/install-systemd-services.sh"
        sudo "$APP_PATH/scripts/install-systemd-services.sh"
        log_message "Systemd services installed"
    else
        log_message "Systemd service installer not found"
        return 1
    fi
    
    return 0
}

# Function to validate migration
validate_migration() {
    log_message "Validating migration"
    
    # Run health check
    if [ -f "$APP_PATH/scripts/health-check.sh" ]; then
        chmod +x "$APP_PATH/scripts/health-check.sh"
        if "$APP_PATH/scripts/health-check.sh" --quick; then
            log_message "Health check passed"
        else
            log_message "Health check failed - manual review required"
            return 1
        fi
    fi
    
    # Run deployment tests
    if [ -f "$APP_PATH/scripts/test-deployment.sh" ]; then
        chmod +x "$APP_PATH/scripts/test-deployment.sh"
        if "$APP_PATH/scripts/test-deployment.sh" --quick; then
            log_message "Deployment tests passed"
        else
            log_message "Deployment tests failed - manual review required"
            return 1
        fi
    fi
    
    return 0
}

# Function to display migration summary
display_migration_summary() {
    echo ""
    log_message "📊 Migration Summary"
    log_message "==================="
    log_message "Total Steps: $MIGRATION_STEPS"
    log_message "Completed: $COMPLETED_STEPS"
    log_message "Failed: $FAILED_STEPS"
    log_message "Backup Location: $BACKUP_DIR"
    log_message "Migration Log: $MIGRATION_LOG"
    
    echo ""
    echo "📊 Migration Summary"
    echo "==================="
    echo "Total Steps: $MIGRATION_STEPS"
    echo "Completed: $COMPLETED_STEPS"
    echo "Failed: $FAILED_STEPS"
    echo ""
    
    if [ $FAILED_STEPS -eq 0 ]; then
        echo "🎉 Migration completed successfully!"
        echo "✅ Your crypto robot is now running with direct Python deployment"
        echo ""
        echo "📋 Next Steps:"
        echo "1. Start services: sudo ./scripts/service-control.sh start-all"
        echo "2. Check status: ./scripts/service-control.sh status"
        echo "3. Monitor logs: ./scripts/service-control.sh logs robot"
        echo ""
        echo "📁 Backup Location: $BACKUP_DIR"
        echo "📝 Migration Log: $MIGRATION_LOG"
        return 0
    else
        echo "❌ Migration completed with $FAILED_STEPS failed steps"
        echo "🔧 Please review the migration log and address any issues"
        echo ""
        echo "📁 Backup Location: $BACKUP_DIR"
        echo "📝 Migration Log: $MIGRATION_LOG"
        return 1
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --dry-run       Show what would be done without making changes"
    echo "  --skip-docker   Skip Docker container operations"
    echo "  --keep-images   Keep Docker images after migration"
    echo "  --backup-only   Only create backup, don't migrate"
    echo "  --help          Show this help message"
    echo ""
    echo "This script migrates from Docker-based deployment to direct Python execution."
    echo "It will:"
    echo "1. Backup existing Docker container data"
    echo "2. Stop and remove Docker containers"
    echo "3. Setup Python virtual environment"
    echo "4. Migrate configuration and data"
    echo "5. Install systemd services"
    echo "6. Validate the migration"
    echo ""
}

# Parse command line arguments
DRY_RUN=false
SKIP_DOCKER=false
KEEP_IMAGES=true
BACKUP_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --skip-docker)
            SKIP_DOCKER=true
            shift
            ;;
        --keep-images)
            KEEP_IMAGES=true
            shift
            ;;
        --backup-only)
            BACKUP_ONLY=true
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
    log_message "🚀 Starting Docker to Python migration"
    log_message "Timestamp: $(date)"
    log_message "Backup directory: $BACKUP_DIR"
    
    echo "🚀 Starting Docker to Python migration..."
    echo "📝 Migration log: $MIGRATION_LOG"
    echo "💾 Backup directory: $BACKUP_DIR"
    echo ""
    
    if [ "$DRY_RUN" = "true" ]; then
        echo "🔍 DRY RUN MODE - No changes will be made"
        echo ""
    fi
    
    # Confirm migration
    if [ "$DRY_RUN" = "false" ]; then
        echo "⚠️  This will migrate your crypto robot from Docker to Python deployment."
        echo "📁 All data will be backed up to: $BACKUP_DIR"
        echo ""
        read -p "Continue with migration? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Migration cancelled"
            exit 0
        fi
    fi
    
    # Run migration steps
    run_migration_step "Check Docker Environment" check_docker_environment false
    run_migration_step "Backup Docker Data" backup_docker_data
    
    if [ "$BACKUP_ONLY" = "true" ]; then
        log_message "Backup-only mode - stopping here"
        echo "✅ Backup completed: $BACKUP_DIR"
        exit 0
    fi
    
    if [ "$SKIP_DOCKER" = "false" ] && [ "$DRY_RUN" = "false" ]; then
        run_migration_step "Stop Docker Containers" stop_docker_containers
    fi
    
    if [ "$DRY_RUN" = "false" ]; then
        run_migration_step "Setup Python Environment" setup_python_environment
        run_migration_step "Migrate Configuration" migrate_configuration
        run_migration_step "Migrate Database" migrate_database
        run_migration_step "Migrate Logs" migrate_logs false
        run_migration_step "Install Systemd Services" install_systemd_services false
        run_migration_step "Validate Migration" validate_migration
    fi
    
    display_migration_summary
}

# Execute main function
main "$@"