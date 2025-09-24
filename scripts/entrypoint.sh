#!/bin/bash
# Crypto Robot Container Entry Point
# Handles container initialization and startup

set -e

echo "🐳 Crypto Robot Container Starting..."
echo "📅 $(date)"
echo "🏠 Working Directory: $(pwd)"
echo "👤 User: $(whoami)"

# Function to decode and recreate .env file from ENV_CONTENT
recreate_env_file() {
    if [ -n "$ENV_CONTENT" ]; then
        echo "📝 Recreating .env file from ENV_CONTENT..."
        
        # Decode base64 content and write to .env file
        echo "$ENV_CONTENT" | base64 -d > .env
        
        if [ $? -eq 0 ]; then
            echo "✅ .env file recreated successfully"
            echo "📊 .env file size: $(wc -l < .env) lines"
        else
            echo "❌ Failed to decode ENV_CONTENT"
            exit 1
        fi
    else
        echo "⚠️  ENV_CONTENT not provided, checking for existing .env file..."
        
        if [ -f ".env" ]; then
            echo "✅ Using existing .env file"
        else
            echo "❌ No .env file found and ENV_CONTENT not provided"
            echo "💡 Please provide ENV_CONTENT environment variable with base64 encoded .env content"
            exit 1
        fi
    fi
}

# Function to select and configure certificates
configure_certificates() {
    local cert_hostname="${CERTIFICATE:-crypto-robot.local}"
    local cert_dir="/opt/crypto-robot/certificates/${cert_hostname}"
    
    echo "🔒 Configuring certificates for hostname: ${cert_hostname}"
    
    if [ -d "$cert_dir" ]; then
        echo "✅ Certificate directory found: $cert_dir"
        
        # Check if certificate files exist
        if [ -f "$cert_dir/cert.pem" ] && [ -f "$cert_dir/key.pem" ]; then
            echo "✅ Certificate files found:"
            echo "   📄 Certificate: $cert_dir/cert.pem"
            echo "   🔑 Private Key: $cert_dir/key.pem"
            
            # Update .env file with certificate paths
            if [ -f ".env" ]; then
                # Update SSL certificate paths in .env
                sed -i "s|^SSL_CERT_PATH=.*|SSL_CERT_PATH=$cert_dir/cert.pem|" .env
                sed -i "s|^SSL_KEY_PATH=.*|SSL_KEY_PATH=$cert_dir/key.pem|" .env
                
                # Update hostname in .env
                sed -i "s|^DOMAIN_NAME=.*|DOMAIN_NAME=$cert_hostname|" .env
                
                echo "✅ Updated .env with certificate configuration"
            fi
        else
            echo "❌ Certificate files not found in $cert_dir"
            echo "💡 Available certificates:"
            ls -la /opt/crypto-robot/certificates/
            exit 1
        fi
    else
        echo "❌ Certificate directory not found: $cert_dir"
        echo "💡 Available certificate directories:"
        ls -la /opt/crypto-robot/certificates/
        exit 1
    fi
}

# Function to configure database persistence
configure_database() {
    echo "🗄️  Configuring database persistence..."
    
    # Read database configuration from .env file
    local database_path=""
    local database_file=""
    
    if [ -f ".env" ]; then
        database_path=$(grep "^DATABASE_PATH=" .env | cut -d'=' -f2 || echo "/opt/crypto-robot/database")
        database_file=$(grep "^DATABASE_FILE=" .env | cut -d'=' -f2 || echo "crypto_robot.db")
    else
        database_path="/opt/crypto-robot/database"
        database_file="crypto_robot.db"
    fi
    
    echo "📁 Database Path: $database_path"
    echo "📄 Database File: $database_file"
    
    # Ensure database directory exists and has proper permissions
    if [ ! -d "$database_path" ]; then
        echo "⚠️  Database directory does not exist, creating: $database_path"
        mkdir -p "$database_path"
        
        if [ $? -eq 0 ]; then
            echo "✅ Database directory created successfully"
        else
            echo "❌ Failed to create database directory: $database_path"
            exit 1
        fi
    else
        echo "✅ Database directory exists: $database_path"
    fi
    
    # Check if database directory is writable
    if [ -w "$database_path" ]; then
        echo "✅ Database directory is writable"
    else
        echo "❌ Database directory is not writable: $database_path"
        echo "💡 Please ensure the host directory has proper permissions"
        exit 1
    fi
    
    # Check if database file exists, create if not
    local full_db_path="$database_path/$database_file"
    if [ ! -f "$full_db_path" ]; then
        echo "⚠️  Database file does not exist, will be created on first use: $full_db_path"
    else
        echo "✅ Database file exists: $full_db_path"
        echo "📊 Database file size: $(du -h "$full_db_path" | cut -f1)"
    fi
    
    # Update .env file with database configuration if needed
    if [ -f ".env" ]; then
        # Ensure DATABASE_PATH is set correctly
        if ! grep -q "^DATABASE_PATH=" .env; then
            echo "DATABASE_PATH=$database_path" >> .env
            echo "✅ Added DATABASE_PATH to .env file"
        fi
        
        # Ensure DATABASE_FILE is set correctly
        if ! grep -q "^DATABASE_FILE=" .env; then
            echo "DATABASE_FILE=$database_file" >> .env
            echo "✅ Added DATABASE_FILE to .env file"
        fi
        
        # Set DATABASE_URL for SQLAlchemy
        local database_url="sqlite:///$full_db_path"
        if grep -q "^DATABASE_URL=" .env; then
            sed -i "s|^DATABASE_URL=.*|DATABASE_URL=$database_url|" .env
        else
            echo "DATABASE_URL=$database_url" >> .env
        fi
        echo "✅ Updated DATABASE_URL in .env file"
    fi
}

# Function to display configuration summary
display_config_summary() {
    echo ""
    echo "📋 Container Configuration Summary:"
    echo "=================================="
    
    if [ -f ".env" ]; then
        # Extract key configuration values
        local flask_port=$(grep "^FLASK_PORT=" .env | cut -d'=' -f2 || echo "5000")
        local flask_protocol=$(grep "^FLASK_PROTOCOL=" .env | cut -d'=' -f2 || echo "http")
        local flask_host=$(grep "^FLASK_HOST=" .env | cut -d'=' -f2 || echo "0.0.0.0")
        local domain_name=$(grep "^DOMAIN_NAME=" .env | cut -d'=' -f2 || echo "crypto-robot.local")
        local use_https=$(grep "^USE_HTTPS=" .env | cut -d'=' -f2 || echo "false")
        local database_path=$(grep "^DATABASE_PATH=" .env | cut -d'=' -f2 || echo "/opt/crypto-robot/database")
        local database_file=$(grep "^DATABASE_FILE=" .env | cut -d'=' -f2 || echo "crypto_robot.db")
        
        echo "🌐 Flask Host: $flask_host"
        echo "🔌 Flask Port: $flask_port"
        echo "🔒 HTTPS Enabled: $use_https"
        echo "🏷️  Domain Name: $domain_name"
        echo "📁 Certificate: ${CERTIFICATE:-crypto-robot.local}"
        echo "🎯 Mode: ${MODE:-webapp}"
        echo "🗄️  Database Path: $database_path"
        echo "📄 Database File: $database_file"
    fi
    
    echo "=================================="
    echo ""
}

# Function to start the appropriate service based on MODE
start_service() {
    local mode="${MODE:-webapp}"
    
    echo "🚀 Starting service in mode: $mode"
    
    case "$mode" in
        "webapp")
            echo "🌐 Starting Flask Web Application..."
            exec ./scripts/start-webapp.sh
            ;;
        "robot")
            echo "🤖 Starting Trading Robot..."
            exec ./scripts/start-robot.sh
            ;;
        "both")
            echo "🔄 Starting both Web Application and Trading Robot..."
            # Start webapp in background and robot in foreground
            ./scripts/start-webapp.sh &
            WEBAPP_PID=$!
            echo "🌐 Web Application started with PID: $WEBAPP_PID"
            
            # Wait a moment for webapp to start
            sleep 5
            
            echo "🤖 Starting Trading Robot..."
            ./scripts/start-robot.sh &
            ROBOT_PID=$!
            echo "🤖 Trading Robot started with PID: $ROBOT_PID"
            
            # Wait for either process to exit
            wait -n
            echo "⚠️  One of the services exited, stopping container..."
            kill $WEBAPP_PID $ROBOT_PID 2>/dev/null || true
            exit 1
            ;;
        *)
            echo "❌ Unknown mode: $mode"
            echo "💡 Valid modes: webapp, robot, both"
            exit 1
            ;;
    esac
}

# Function to handle shutdown signals
cleanup() {
    echo ""
    echo "🛑 Received shutdown signal, cleaning up..."
    
    # Kill any background processes
    jobs -p | xargs -r kill 2>/dev/null || true
    
    echo "✅ Cleanup completed"
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Main execution flow
main() {
    echo "🔧 Initializing container..."
    
    # Step 1: Recreate .env file from ENV_CONTENT
    recreate_env_file
    
    # Step 2: Configure certificates
    configure_certificates
    
    # Step 3: Configure database persistence
    configure_database
    
    # Step 4: Display configuration summary
    display_config_summary
    
    # Step 5: Start the appropriate service
    start_service
}

# Execute main function
main "$@"