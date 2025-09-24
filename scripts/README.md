# Container Scripts

This directory contains the startup and utility scripts for the Crypto Robot Docker container.

## Scripts Overview

### Core Container Scripts

#### `entrypoint.sh`
Main container entry point that handles:
- Decoding and recreating `.env` file from `ENV_CONTENT` environment variable
- Certificate selection and configuration based on `CERTIFICATE` environment variable
- Service startup based on `MODE` environment variable
- Signal handling and cleanup

#### `start-webapp.sh`
Flask web application startup script that:
- Loads environment configuration from `.env` file
- Configures Flask with dynamic port/protocol settings
- Validates SSL certificates for HTTPS mode
- Starts the web application with proper error handling
- Performs health checks

#### `start-robot.sh`
Trading robot startup script that:
- Loads environment configuration from `.env` file
- Validates Binance API configuration
- Starts the trading robot in various modes (single, auto, live, simulation)
- Monitors robot health and handles retries
- Manages robot lifecycle

### Utility Scripts

#### `test-container.sh`
Local testing script for validating container functionality without Docker:
- Tests directory structure
- Validates `.env` file handling
- Checks certificate availability
- Tests script permissions
- Simulates configuration extraction

## Environment Variables

### Required Variables

- `ENV_CONTENT` - Base64 encoded `.env` file content
- `CERTIFICATE` - Hostname for certificate selection (e.g., "crypto-robot.local")

### Optional Variables

- `MODE` - Container mode: "webapp" (default), "robot", or "both"
- `ROBOT_MODE` - Robot execution mode: "single", "auto", "live", "simulation"

## Usage Examples

### Basic Web Application
```bash
docker run -d \
  -e ENV_CONTENT="$(base64 -w 0 robot/.env)" \
  -e CERTIFICATE="crypto-robot.local" \
  -e MODE="webapp" \
  -p 5000:5000 \
  crypto-robot:latest
```

### Trading Robot Only
```bash
docker run -d \
  -e ENV_CONTENT="$(base64 -w 0 robot/.env)" \
  -e CERTIFICATE="crypto-robot.local" \
  -e MODE="robot" \
  -e ROBOT_MODE="single" \
  crypto-robot:latest
```

### Both Services
```bash
docker run -d \
  -e ENV_CONTENT="$(base64 -w 0 robot/.env)" \
  -e CERTIFICATE="crypto-robot.local" \
  -e MODE="both" \
  -p 5000:5000 \
  crypto-robot:latest
```

## Certificate Selection Logic

The `CERTIFICATE` environment variable determines which certificate directory to use:

```
certificates/
├── crypto-robot.local/          # CERTIFICATE="crypto-robot.local"
├── jack.crypto-robot-itechsource.com/  # CERTIFICATE="jack.crypto-robot-itechsource.com"
└── custom-hostname/             # CERTIFICATE="custom-hostname"
```

Each certificate directory must contain:
- `cert.pem` - SSL certificate
- `key.pem` - Private key

## .env File Recreation

The container recreates the `.env` file from the `ENV_CONTENT` environment variable:

1. `ENV_CONTENT` contains base64-encoded `.env` file content
2. `entrypoint.sh` decodes the content and writes it to `.env`
3. Certificate paths are updated based on `CERTIFICATE` selection
4. Domain name is updated to match the certificate hostname

## Dynamic Configuration

The scripts dynamically configure the application based on `.env` content:

### Flask Configuration
- `FLASK_PORT` - Web server port (default: 5000)
- `FLASK_HOST` - Web server host (default: 0.0.0.0)
- `FLASK_PROTOCOL` - Protocol (http/https)
- `USE_HTTPS` - Enable HTTPS mode
- `DOMAIN_NAME` - Domain name for certificates

### Robot Configuration
- `STARTING_CAPITAL` - Initial trading capital
- `ROBOT_DRY_RUN` - Enable dry run mode
- `STRATEGY_NAME` - Trading strategy
- `VOLATILITY_SELECTION_MODE` - Volatility mode

## Error Handling

All scripts include comprehensive error handling:
- Exit on any command failure (`set -e`)
- Signal handling for graceful shutdown
- Validation of required files and variables
- Retry logic for transient failures
- Detailed logging and error messages

## Testing

Use the test script to validate functionality:

```bash
./scripts/test-container.sh
```

This will check:
- Directory structure
- Script permissions
- Environment variable handling
- Certificate availability
- Configuration extraction

## Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   chmod +x scripts/*.sh
   ```

2. **Certificate Not Found**
   - Verify `CERTIFICATE` environment variable
   - Check certificate directory exists
   - Ensure `cert.pem` and `key.pem` files are present

3. **Invalid ENV_CONTENT**
   - Verify base64 encoding: `base64 -w 0 robot/.env`
   - Check for special characters in environment

4. **Port Already in Use**
   - Change `FLASK_PORT` in `.env` file
   - Use different host port mapping

### Debug Mode

Enable debug output by setting:
```bash
export DEBUG=1
```

This will provide additional logging information during container startup.