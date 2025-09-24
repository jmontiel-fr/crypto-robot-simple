#!/bin/bash
# Crypto Robot Python Environment Setup Script
# Creates and configures Python virtual environment for direct deployment

set -e

echo "🐍 Setting up Python Environment for Crypto Robot"
echo "=================================================="

# Configuration
PYTHON_VERSION="3.11"
VENV_PATH="/opt/crypto-robot/venv"
APP_PATH="/opt/crypto-robot"
REQUIREMENTS_FILE="$APP_PATH/requirements.txt"

# Function to check Python version
check_python_version() {
    echo "🔍 Checking Python installation..."
    
    # Check if python3 is available
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python3 not found. Installing Python..."
        sudo yum update -y
        sudo yum install -y python3 python3-pip python3-venv
    fi
    
    # Get Python version
    INSTALLED_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    echo "✅ Python version: $INSTALLED_VERSION"
    
    # Check if version is compatible (3.8+)
    if [[ $(echo "$INSTALLED_VERSION 3.8" | tr ' ' '\n' | sort -V | head -n1) != "3.8" ]]; then
        echo "⚠️  Python version $INSTALLED_VERSION detected. Recommended: 3.8+"
    fi
}

# Function to create virtual environment
create_virtual_environment() {
    echo "🏗️  Creating Python virtual environment..."
    
    # Remove existing virtual environment if it exists
    if [ -d "$VENV_PATH" ]; then
        echo "⚠️  Existing virtual environment found. Removing..."
        rm -rf "$VENV_PATH"
    fi
    
    # Create new virtual environment
    python3 -m venv "$VENV_PATH"
    
    if [ $? -eq 0 ]; then
        echo "✅ Virtual environment created at: $VENV_PATH"
    else
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
}

# Function to activate virtual environment
activate_virtual_environment() {
    echo "🔄 Activating virtual environment..."
    
    # Check if activation script exists
    if [ ! -f "$VENV_PATH/bin/activate" ]; then
        echo "❌ Virtual environment activation script not found"
        exit 1
    fi
    
    # Activate virtual environment
    source "$VENV_PATH/bin/activate"
    echo "✅ Virtual environment activated"
    
    # Verify activation
    which python
    python --version
}

# Function to upgrade pip
upgrade_pip() {
    echo "📦 Upgrading pip..."
    
    python -m pip install --upgrade pip
    
    if [ $? -eq 0 ]; then
        echo "✅ Pip upgraded successfully"
        pip --version
    else
        echo "❌ Failed to upgrade pip"
        exit 1
    fi
}

# Function to install dependencies
install_dependencies() {
    echo "📚 Installing Python dependencies..."
    
    # Check if requirements file exists
    if [ ! -f "$REQUIREMENTS_FILE" ]; then
        echo "❌ Requirements file not found: $REQUIREMENTS_FILE"
        exit 1
    fi
    
    echo "📄 Using requirements file: $REQUIREMENTS_FILE"
    
    # Install dependencies
    pip install -r "$REQUIREMENTS_FILE"
    
    if [ $? -eq 0 ]; then
        echo "✅ Dependencies installed successfully"
    else
        echo "❌ Failed to install dependencies"
        exit 1
    fi
}

# Function to validate installation
validate_installation() {
    echo "🔍 Validating installation..."
    
    # Check critical packages
    critical_packages=("flask" "python-binance" "requests" "pandas" "numpy")
    
    for package in "${critical_packages[@]}"; do
        if python -c "import ${package//-/_}" 2>/dev/null; then
            echo "✅ $package: OK"
        else
            echo "❌ $package: MISSING"
            return 1
        fi
    done
    
    echo "✅ All critical packages validated"
}

# Function to create activation helper script
create_activation_script() {
    echo "📝 Creating activation helper script..."
    
    cat > "$APP_PATH/activate-env.sh" << 'EOF'
#!/bin/bash
# Crypto Robot Environment Activation Helper
source /opt/crypto-robot/venv/bin/activate
echo "🐍 Crypto Robot Python environment activated"
echo "📍 Virtual environment: $VIRTUAL_ENV"
echo "🐍 Python: $(which python)"
echo "📦 Pip: $(which pip)"
EOF
    
    chmod +x "$APP_PATH/activate-env.sh"
    echo "✅ Activation script created: $APP_PATH/activate-env.sh"
}

# Function to set proper permissions
set_permissions() {
    echo "🔒 Setting proper permissions..."
    
    # Set ownership to ec2-user
    sudo chown -R ec2-user:ec2-user "$APP_PATH"
    
    # Set directory permissions
    find "$APP_PATH" -type d -exec chmod 755 {} \;
    
    # Set file permissions
    find "$APP_PATH" -type f -exec chmod 644 {} \;
    
    # Set executable permissions for scripts
    find "$APP_PATH" -name "*.sh" -exec chmod +x {} \;
    find "$APP_PATH" -name "*.py" -exec chmod +x {} \;
    
    echo "✅ Permissions set correctly"
}

# Function to create environment info script
create_env_info_script() {
    echo "📊 Creating environment info script..."
    
    cat > "$APP_PATH/env-info.sh" << 'EOF'
#!/bin/bash
# Display Python environment information
echo "🐍 Python Environment Information"
echo "================================="
echo "📍 Virtual Environment: $VIRTUAL_ENV"
echo "🐍 Python Version: $(python --version)"
echo "📦 Pip Version: $(pip --version)"
echo "📚 Installed Packages:"
pip list --format=columns
echo ""
echo "🗂️  Environment Variables:"
env | grep -E "(FLASK_|BINANCE_|DATABASE_)" | sort
EOF
    
    chmod +x "$APP_PATH/env-info.sh"
    echo "✅ Environment info script created: $APP_PATH/env-info.sh"
}

# Function to display summary
display_summary() {
    echo ""
    echo "🎉 Python Environment Setup Complete!"
    echo "====================================="
    echo "📍 Virtual Environment: $VENV_PATH"
    echo "📁 Application Path: $APP_PATH"
    echo "🐍 Python: $(which python)"
    echo "📦 Pip: $(which pip)"
    echo ""
    echo "🚀 Usage:"
    echo "  Activate environment: source $APP_PATH/activate-env.sh"
    echo "  View environment info: $APP_PATH/env-info.sh"
    echo "  Start robot: python $APP_PATH/main.py --mode robot"
    echo "  Start webapp: python $APP_PATH/app.py"
    echo ""
}

# Main execution flow
main() {
    echo "🚀 Starting Python environment setup..."
    
    # Ensure we're in the correct directory
    cd "$APP_PATH" || {
        echo "❌ Failed to change to application directory: $APP_PATH"
        exit 1
    }
    
    # Execute setup steps
    check_python_version
    create_virtual_environment
    activate_virtual_environment
    upgrade_pip
    install_dependencies
    validate_installation
    create_activation_script
    create_env_info_script
    set_permissions
    display_summary
    
    echo "✅ Python environment setup completed successfully!"
}

# Error handling
trap 'echo "❌ Setup failed at line $LINENO. Exit code: $?"' ERR

# Execute main function
main "$@"