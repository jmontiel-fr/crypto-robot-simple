#!/bin/bash

# Script to start or stop the web-crypto-robot EC2 instance
# Usage: ./start-stop-ec2.sh [start|stop|status]

set -e  # Exit on any error

# Configuration
INSTANCE_NAME="web-crypto-robot-instance"
REGION="eu-west-1"
AWS_PROFILE="perso"

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

# Function to get instance ID by name
get_instance_id() {
    local instance_id=$(aws ec2 describe-instances \
        --profile "$AWS_PROFILE" \
        --region "$REGION" \
        --no-verify-ssl \
        --filters "Name=tag:Name,Values=$INSTANCE_NAME" "Name=instance-state-name,Values=running,stopped,stopping,pending" \
        --query 'Reservations[0].Instances[0].InstanceId' \
        --output text 2>/dev/null)
    
    if [ "$instance_id" = "None" ] || [ "$instance_id" = "null" ] || [ -z "$instance_id" ]; then
        return 1
    fi
    
    echo "$instance_id"
    return 0
}

# Function to get instance state
get_instance_state() {
    local instance_id="$1"
    aws ec2 describe-instances \
        --profile "$AWS_PROFILE" \
        --region "$REGION" \
        --no-verify-ssl \
        --instance-ids "$instance_id" \
        --query 'Reservations[0].Instances[0].State.Name' \
        --output text 2>/dev/null
}

# Function to get instance public IP
get_instance_public_ip() {
    local instance_id="$1"
    aws ec2 describe-instances \
        --profile "$AWS_PROFILE" \
        --region "$REGION" \
        --no-verify-ssl \
        --instance-ids "$instance_id" \
        --query 'Reservations[0].Instances[0].PublicIpAddress' \
        --output text 2>/dev/null
}

# Function to start instance
start_instance() {
    local instance_id="$1"
    print_status "Starting instance $instance_id..."
    
    aws ec2 start-instances \
        --profile "$AWS_PROFILE" \
        --region "$REGION" \
        --no-verify-ssl \
        --instance-ids "$instance_id" \
        --output table
    
    print_status "Waiting for instance to be running..."
    aws ec2 wait instance-running \
        --profile "$AWS_PROFILE" \
        --region "$REGION" \
        --no-verify-ssl \
        --instance-ids "$instance_id"
    
    local public_ip=$(get_instance_public_ip "$instance_id")
    print_success "Instance is now running!"
    if [ "$public_ip" != "None" ] && [ "$public_ip" != "null" ] && [ -n "$public_ip" ]; then
        print_success "Public IP: $public_ip"
        print_status "You can SSH using: ssh -i web-crypto-robot-key.pem ec2-user@$public_ip"
    fi
}

# Function to stop instance
stop_instance() {
    local instance_id="$1"
    print_status "Stopping instance $instance_id..."
    
    aws ec2 stop-instances \
        --profile "$AWS_PROFILE" \
        --region "$REGION" \
        --no-verify-ssl \
        --instance-ids "$instance_id" \
        --output table
    
    print_status "Waiting for instance to be stopped..."
    aws ec2 wait instance-stopped \
        --profile "$AWS_PROFILE" \
        --region "$REGION" \
        --no-verify-ssl \
        --instance-ids "$instance_id"
    
    print_success "Instance is now stopped!"
}

# Function to show instance status
show_status() {
    local instance_id="$1"
    local state=$(get_instance_state "$instance_id")
    local public_ip=$(get_instance_public_ip "$instance_id")
    
    echo ""
    echo "=== Instance Status ==="
    echo "Instance ID: $instance_id"
    echo "Instance Name: $INSTANCE_NAME"
    echo "Region: $REGION"
    echo "AWS Profile: $AWS_PROFILE"
    echo "State: $state"
    
    if [ "$public_ip" != "None" ] && [ "$public_ip" != "null" ] && [ -n "$public_ip" ]; then
        echo "Public IP: $public_ip"
        if [ "$state" = "running" ]; then
            echo "SSH Command: ssh -i web-crypto-robot-key.pem ec2-user@$public_ip"
        fi
    else
        echo "Public IP: Not assigned"
    fi
    echo "======================="
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [start|stop|status|toggle|help]"
    echo ""
    echo "Commands:"
    echo "  start   - Start the EC2 instance"
    echo "  stop    - Stop the EC2 instance"
    echo "  status  - Show current instance status"
    echo "  toggle  - Toggle instance state (start if stopped, stop if running)"
    echo "  help    - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start    # Start the instance"
    echo "  $0 stop     # Stop the instance"
    echo "  $0 toggle   # Smart toggle based on current state"
    echo "  $0 help     # Show help"
}

# Main script logic
main() {
    # Check if no arguments provided
    if [ $# -eq 0 ]; then
        print_error "No command provided"
        echo ""
        show_usage
        exit 1
    fi

    # Check for help first (before AWS operations)
    if [ "$1" = "help" ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        show_usage
        exit 0
    fi

    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed or not in PATH"
        exit 1
    fi

    # Get instance ID
    print_status "Looking for instance: $INSTANCE_NAME in region: $REGION"
    
    if ! INSTANCE_ID=$(get_instance_id); then
        print_error "Instance '$INSTANCE_NAME' not found in region '$REGION'"
        print_error "Make sure the instance exists and you have proper AWS credentials configured"
        exit 1
    fi
    
    print_success "Found instance: $INSTANCE_ID"
    
    # Get current state
    CURRENT_STATE=$(get_instance_state "$INSTANCE_ID")
    print_status "Current state: $CURRENT_STATE"
    
    # Determine action
    ACTION="$1"
    
    case "$ACTION" in
        "start")
            if [ "$CURRENT_STATE" = "running" ]; then
                print_warning "Instance is already running"
                show_status "$INSTANCE_ID"
            elif [ "$CURRENT_STATE" = "stopped" ]; then
                start_instance "$INSTANCE_ID"
            else
                print_error "Instance is in '$CURRENT_STATE' state. Can only start stopped instances."
                exit 1
            fi
            ;;
        "stop")
            if [ "$CURRENT_STATE" = "stopped" ]; then
                print_warning "Instance is already stopped"
                show_status "$INSTANCE_ID"
            elif [ "$CURRENT_STATE" = "running" ]; then
                stop_instance "$INSTANCE_ID"
            else
                print_error "Instance is in '$CURRENT_STATE' state. Can only stop running instances."
                exit 1
            fi
            ;;
        "status")
            show_status "$INSTANCE_ID"
            ;;
        "toggle")
            if [ "$CURRENT_STATE" = "running" ]; then
                print_status "Instance is running, stopping it..."
                stop_instance "$INSTANCE_ID"
            elif [ "$CURRENT_STATE" = "stopped" ]; then
                print_status "Instance is stopped, starting it..."
                start_instance "$INSTANCE_ID"
            else
                print_error "Instance is in '$CURRENT_STATE' state. Cannot toggle from this state."
                exit 1
            fi
            ;;
        *)
            print_error "Unknown command: $ACTION"
            show_usage
            exit 1
            ;;
    esac
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
