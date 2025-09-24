#!/bin/bash
# Crypto Robot Environment File Management Utilities
# Manages .env file creation, validation, and updates

set -e

echo "⚙️  Crypto Robot Environment Management"
echo "======================================"

# Configuration
APP_PATH="/opt/crypto-robot"
ENV_FILE="$APP_PATH/.env"
ENV_TEMPLATE="$APP_PATH/.env.template"
ENV_BACKUP_DIR="$APP_PATH/backups/env"

# Function to create backup directory
create_backup_dir() {
    if [ ! -d "$ENV_BACKUP_DIR" ]; then
        mkdir -p "$ENV_BACKUP_DIR"
        chmod 755 "$ENV_BACKUP_DIR"
        echo "✅ Created backup directory: $ENV_BACKUP_DIR"
    fi
}

# Function to create .env file from template
create_from_template() {
    echo "📝 Creating .env file from template..."
    
    if [ ! -f "$ENV_TEMPLATE" ]; then
        echo "❌ Template file not found: $ENV_TEMPLATE"
        exit 1
    fi
    
    if [ -f "$ENV_FILE" ]; then
        local backup_file="$ENV_BACKUP_DIR/.env.$(date +%Y%m%d-%H%M%S)"
        echo "💾 Backing up existing .env to: $backup_file"
        cp "$ENV_FILE" "$backup_file"
    fi
    
    cp "$ENV_TEMPLATE" "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    chown ec2-user:ec2-user "$ENV_FILE" 2>/dev/null || true
    
    echo "✅ .env file created from template"
}

# Function to validate .env file
validate_env_file() {
    echo "🔍 Validating .env file..."
    
    if [ ! -f "$ENV_FILE" ]; then
        echo "❌ .env file not found: $ENV_FILE"
        return 1
    fi
    
    local errors=0
    local warnings=0
    
    # Check required variables
    local required_vars=(
        "BINANCE_API_KEY"
        "BINANCE_SECRET_KEY"
        "STARTING_CAPITAL"
        "FLASK_PORT"
        "FLASK_HOST"
        "DATABASE_TYPE"
    )
    
    echo "🔍 Checking required variables..."
    for var in "${required_vars[@]}"; do
        if grep -q "^${var}=" "$ENV_FILE"; then
            local value=$(grep "^${var}=" "$ENV_FILE" | cut -d'=' -f2-)
            if [ -z "$value" ] || [ "$value" = "your_${var,,}_here" ]; then
                echo "⚠️  $var: not configured (using placeholder)"
                warnings=$((warnings + 1))
            else
                echo "✅ $var: configured"
            fi
        else
            echo "❌ $var: missing"
            errors=$((errors + 1))
        fi
    done
    
    # Check for common configuration issues
    echo "🔍 Checking configuration consistency..."
    
    # Check HTTPS configuration
    local use_https=$(grep "^USE_HTTPS=" "$ENV_FILE" | cut -d'=' -f2 | tr '[:upper:]' '[:lower:]')
    local flask_protocol=$(grep "^FLASK_PROTOCOL=" "$ENV_FILE" | cut -d'=' -f2 | tr '[:upper:]' '[:lower:]')
    
    if [ "$use_https" = "true" ] || [ "$flask_protocol" = "https" ]; then
        if ! grep -q "^SSL_CERT_PATH=" "$ENV_FILE" || ! grep -q "^SSL_KEY_PATH=" "$ENV_FILE"; then
            echo "⚠️  HTTPS enabled but SSL certificate paths not configured"
            warnings=$((warnings + 1))
        else
            echo "✅ HTTPS configuration: consistent"
        fi
    fi
    
    # Check database configuration
    local db_type=$(grep "^DATABASE_TYPE=" "$ENV_FILE" | cut -d'=' -f2)
    if [ "$db_type" = "sqlite" ]; then
        if ! grep -q "^DATABASE_PATH=" "$ENV_FILE" || ! grep -q "^DATABASE_FILE=" "$ENV_FILE"; then
            echo "⚠️  SQLite database type but paths not configured"
            warnings=$((warnings + 1))
        else
            echo "✅ Database configuration: consistent"
        fi
    fi
    
    # Summary
    echo ""
    echo "📊 Validation Summary:"
    echo "  Errors: $errors"
    echo "  Warnings: $warnings"
    
    if [ $errors -gt 0 ]; then
        echo "❌ Validation failed with $errors errors"
        return 1
    elif [ $warnings -gt 0 ]; then
        echo "⚠️  Validation completed with $warnings warnings"
        return 0
    else
        echo "✅ Validation passed successfully"
        return 0
    fi
}

# Function to update specific environment variable
update_env_var() {
    local var_name="$1"
    local var_value="$2"
    
    if [ -z "$var_name" ] || [ -z "$var_value" ]; then
        echo "❌ Variable name and value required"
        return 1
    fi
    
    echo "🔧 Updating $var_name..."
    
    if [ ! -f "$ENV_FILE" ]; then
        echo "❌ .env file not found: $ENV_FILE"
        return 1
    fi
    
    # Create backup
    local backup_file="$ENV_BACKUP_DIR/.env.$(date +%Y%m%d-%H%M%S)"
    cp "$ENV_FILE" "$backup_file"
    
    # Update the variable
    if grep -q "^${var_name}=" "$ENV_FILE"; then
        # Variable exists, update it
        sed -i "s|^${var_name}=.*|${var_name}=${var_value}|" "$ENV_FILE"
        echo "✅ Updated existing variable: $var_name"
    else
        # Variable doesn't exist, add it
        echo "${var_name}=${var_value}" >> "$ENV_FILE"
        echo "✅ Added new variable: $var_name"
    fi
    
    # Maintain file permissions
    chmod 600 "$ENV_FILE"
    chown ec2-user:ec2-user "$ENV_FILE" 2>/dev/null || true
}

# Function to merge environment files
merge_env_files() {
    local source_file="$1"
    local target_file="${2:-$ENV_FILE}"
    
    if [ ! -f "$source_file" ]; then
        echo "❌ Source file not found: $source_file"
        return 1
    fi
    
    echo "🔄 Merging $source_file into $target_file..."
    
    # Create backup of target file
    if [ -f "$target_file" ]; then
        local backup_file="$ENV_BACKUP_DIR/.env.$(date +%Y%m%d-%H%M%S)"
        cp "$target_file" "$backup_file"
        echo "💾 Backup created: $backup_file"
    fi
    
    # Create temporary file for merging
    local temp_file=$(mktemp)
    
    # Start with target file (if exists)
    if [ -f "$target_file" ]; then
        cp "$target_file" "$temp_file"
    fi
    
    # Process source file line by line
    while IFS= read -r line; do
        # Skip comments and empty lines
        if [[ "$line" =~ ^[[:space:]]*# ]] || [[ -z "$line" ]]; then
            continue
        fi
        
        # Extract variable name
        if [[ "$line" =~ ^([^=]+)= ]]; then
            local var_name="${BASH_REMATCH[1]}"
            
            # Update or add the variable
            if grep -q "^${var_name}=" "$temp_file" 2>/dev/null; then
                # Update existing variable
                sed -i "s|^${var_name}=.*|${line}|" "$temp_file"
            else
                # Add new variable
                echo "$line" >> "$temp_file"
            fi
        fi
    done < "$source_file"
    
    # Replace target file
    mv "$temp_file" "$target_file"
    chmod 600 "$target_file"
    chown ec2-user:ec2-user "$target_file" 2>/dev/null || true
    
    echo "✅ Files merged successfully"
}

# Function to show environment variables (without sensitive values)
show_env_vars() {
    echo "📋 Environment Variables:"
    echo "========================"
    
    if [ ! -f "$ENV_FILE" ]; then
        echo "❌ .env file not found: $ENV_FILE"
        return 1
    fi
    
    # Show variables with sensitive ones masked
    while IFS= read -r line; do
        if [[ "$line" =~ ^([^=]+)=(.*)$ ]]; then
            local var_name="${BASH_REMATCH[1]}"
            local var_value="${BASH_REMATCH[2]}"
            
            # Mask sensitive variables
            case "$var_name" in
                *API_KEY*|*SECRET*|*PASSWORD*|*TOKEN*)
                    if [ -n "$var_value" ] && [ "$var_value" != "your_${var_name,,}_here" ]; then
                        echo "🔒 $var_name=***CONFIGURED***"
                    else
                        echo "⚠️  $var_name=***NOT_CONFIGURED***"
                    fi
                    ;;
                *)
                    echo "📝 $var_name=$var_value"
                    ;;
            esac
        fi
    done < <(grep "^[^#]" "$ENV_FILE" | grep "=")
}

# Function to check environment file differences
check_differences() {
    local file1="${1:-$ENV_TEMPLATE}"
    local file2="${2:-$ENV_FILE}"
    
    echo "🔍 Checking differences between files..."
    echo "  File 1: $file1"
    echo "  File 2: $file2"
    
    if [ ! -f "$file1" ] || [ ! -f "$file2" ]; then
        echo "❌ One or both files not found"
        return 1
    fi
    
    # Extract variable names from both files
    local vars1=$(grep "^[^#].*=" "$file1" | cut -d'=' -f1 | sort)
    local vars2=$(grep "^[^#].*=" "$file2" | cut -d'=' -f1 | sort)
    
    # Find variables only in file1
    local only_in_1=$(comm -23 <(echo "$vars1") <(echo "$vars2"))
    if [ -n "$only_in_1" ]; then
        echo "📝 Variables only in $file1:"
        echo "$only_in_1" | sed 's/^/  /'
    fi
    
    # Find variables only in file2
    local only_in_2=$(comm -13 <(echo "$vars1") <(echo "$vars2"))
    if [ -n "$only_in_2" ]; then
        echo "📝 Variables only in $file2:"
        echo "$only_in_2" | sed 's/^/  /'
    fi
    
    # Find common variables with different values
    local common_vars=$(comm -12 <(echo "$vars1") <(echo "$vars2"))
    if [ -n "$common_vars" ]; then
        echo "🔍 Checking values for common variables..."
        while read -r var; do
            local val1=$(grep "^${var}=" "$file1" | cut -d'=' -f2-)
            local val2=$(grep "^${var}=" "$file2" | cut -d'=' -f2-)
            
            if [ "$val1" != "$val2" ]; then
                case "$var" in
                    *API_KEY*|*SECRET*|*PASSWORD*|*TOKEN*)
                        echo "🔒 $var: values differ (sensitive - not shown)"
                        ;;
                    *)
                        echo "📝 $var: '$val1' vs '$val2'"
                        ;;
                esac
            fi
        done <<< "$common_vars"
    fi
}

# Function to display usage
show_usage() {
    echo "Usage: $0 COMMAND [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  create              Create .env from template"
    echo "  validate            Validate .env file"
    echo "  update VAR VALUE    Update environment variable"
    echo "  merge SOURCE        Merge source file into .env"
    echo "  show                Show environment variables (sensitive masked)"
    echo "  diff [FILE1] [FILE2] Compare environment files"
    echo "  backup              Create backup of current .env"
    echo "  restore BACKUP      Restore from backup file"
    echo ""
    echo "Examples:"
    echo "  $0 create"
    echo "  $0 validate"
    echo "  $0 update FLASK_PORT 5000"
    echo "  $0 merge /tmp/new-config.env"
    echo "  $0 show"
    echo "  $0 diff"
    echo ""
}

# Function to create backup
create_backup() {
    if [ ! -f "$ENV_FILE" ]; then
        echo "❌ .env file not found: $ENV_FILE"
        return 1
    fi
    
    create_backup_dir
    local backup_file="$ENV_BACKUP_DIR/.env.$(date +%Y%m%d-%H%M%S)"
    cp "$ENV_FILE" "$backup_file"
    echo "✅ Backup created: $backup_file"
}

# Function to restore from backup
restore_backup() {
    local backup_file="$1"
    
    if [ -z "$backup_file" ]; then
        echo "📋 Available backups:"
        ls -la "$ENV_BACKUP_DIR"/.env.* 2>/dev/null || echo "No backups found"
        return 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        echo "❌ Backup file not found: $backup_file"
        return 1
    fi
    
    # Create backup of current file before restoring
    if [ -f "$ENV_FILE" ]; then
        create_backup
    fi
    
    cp "$backup_file" "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    chown ec2-user:ec2-user "$ENV_FILE" 2>/dev/null || true
    
    echo "✅ Restored from backup: $backup_file"
}

# Main execution
main() {
    create_backup_dir
    
    case "${1:-}" in
        create)
            create_from_template
            ;;
        validate)
            validate_env_file
            ;;
        update)
            if [ $# -lt 3 ]; then
                echo "❌ Usage: $0 update VAR_NAME VAR_VALUE"
                exit 1
            fi
            update_env_var "$2" "$3"
            ;;
        merge)
            if [ $# -lt 2 ]; then
                echo "❌ Usage: $0 merge SOURCE_FILE"
                exit 1
            fi
            merge_env_files "$2"
            ;;
        show)
            show_env_vars
            ;;
        diff)
            check_differences "$2" "$3"
            ;;
        backup)
            create_backup
            ;;
        restore)
            restore_backup "$2"
            ;;
        *)
            show_usage
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"