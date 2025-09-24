# Environment Files with Embedded Certificates

This directory contains host-specific environment files with embedded SSL certificates for the Crypto Robot application. Each environment is configured for its specific deployment target.

## Directory Structure

```
envs/
├── crypto-robot.local/           # Local development environment
│   └── .env                      # Complete .env with embedded self-signed certificates
├── jack_robot.crypto-vision.com/ # Jack's production environment
│   └── .env                      # Complete .env with embedded Let's Encrypt certificates
├── its_robot.crypto-vision.com/  # ITS production environment
│   └── .env                      # Complete .env with embedded Let's Encrypt certificates
└── README.md                     # This file
```

## Environment Configurations

### Local Development (`crypto-robot.local`)
- **Purpose**: Local development and testing
- **Flask Port**: 5000 (HTTP)
- **Certificate**: Self-signed (embedded)
- **Binance**: Testnet mode enabled
- **Starting Capital**: 100 BNB
- **Debug Mode**: Enabled
- **Dry Run**: Enabled (safe for testing)

### Jack's Production (`jack_robot.crypto-vision.com`)
- **Purpose**: Jack's production trading environment
- **Flask Port**: 5443 (HTTPS)
- **Certificate**: Let's Encrypt-style (embedded)
- **Binance**: Live trading mode
- **Starting Capital**: 1000 BNB
- **Debug Mode**: Disabled
- **Dry Run**: Disabled (live trading)

### ITS Production (`its_robot.crypto-vision.com`)
- **Purpose**: ITS production trading environment
- **Flask Port**: 5443 (HTTPS)
- **Certificate**: Let's Encrypt-style (embedded)
- **Binance**: Live trading mode
- **Starting Capital**: 2000 BNB
- **Debug Mode**: Disabled
- **Dry Run**: Disabled (live trading)

## Certificate Embedding

Each .env file contains embedded SSL certificates as environment variables:

```bash
SSL_CERT_CONTENT="-----BEGIN CERTIFICATE-----
...certificate content...
-----END CERTIFICATE-----"

SSL_KEY_CONTENT="-----BEGIN PRIVATE KEY-----
...private key content...
-----END PRIVATE KEY-----"
```

These certificates are extracted at container startup and written to the appropriate filesystem locations.

## Usage

### Local Docker Testing
```bash
# Test with local development environment
docker run -e ENV_CONTENT="$(base64 -w 0 envs/crypto-robot.local/.env)" \
  -e CERTIFICATE="crypto-robot.local" \
  -p 5000:5000 \
  crypto-robot
```

### GitHub Actions Deployment

For GitHub Actions workflows, encode the .env files as base64 and store them as environment secrets:

```bash
# Create GitHub environment secrets
base64 -w 0 envs/crypto-robot.local/.env
base64 -w 0 envs/jack_robot.crypto-vision.com/.env
base64 -w 0 envs/its_robot.crypto-vision.com/.env
```

Then add these as `ENV_CONTENT` secrets in the respective GitHub environments:
- `crypto-robot.local` environment
- `jack_robot.crypto-vision.com` environment
- `its_robot.crypto-vision.com` environment

### Manual EC2 Deployment

Copy the appropriate .env file to your EC2 instance:

```bash
# Copy Jack's environment to EC2
scp envs/jack_robot.crypto-vision.com/.env ec2-user@<instance-ip>:/opt/crypto-robot/hosts/jack_robot.crypto-vision.com/app/.env

# Copy ITS environment to EC2
scp envs/its_robot.crypto-vision.com/.env ec2-user@<instance-ip>:/opt/crypto-robot/hosts/its_robot.crypto-vision.com/app/.env
```

## Security Considerations

1. **Private Keys**: Each .env file contains embedded private keys - keep these files secure
2. **API Keys**: All files use the same Binance API keys - consider using separate keys for production
3. **File Permissions**: Ensure .env files have restricted permissions (600)
4. **Version Control**: Consider using .gitignore to exclude these files if they contain sensitive data

## Updating Certificates

When certificates need to be updated:

1. **Generate new certificates**:
   ```bash
   ./tools/generate-certificates.sh jack_robot.crypto-vision.com letsencrypt
   ./tools/generate-certificates.sh its_robot.crypto-vision.com letsencrypt
   ```

2. **Regenerate .env files**:
   ```bash
   ./tools/create-env-with-certs.sh jack_robot.crypto-vision.com envs/jack_robot.crypto-vision.com/.env
   ./tools/create-env-with-certs.sh its_robot.crypto-vision.com envs/its_robot.crypto-vision.com/.env
   ```

3. **Update API keys** if needed in the generated files

4. **Update GitHub environment secrets** with new base64 encoded content

## Configuration Differences

| Setting | Local | Jack's Prod | ITS Prod |
|---------|-------|-------------|----------|
| Flask Port | 5000 | 5443 | 5443 |
| Protocol | HTTP | HTTPS | HTTPS |
| Debug Mode | true | false | false |
| Binance Testnet | true | false | false |
| Starting Capital | 100 BNB | 1000 BNB | 2000 BNB |
| Dry Run | true | false | false |
| Min Balance | 10 BNB | 50 BNB | 100 BNB |
| Min Reserve | 2 BNB | 10 BNB | 20 BNB |

## Maintenance

- **Certificate Renewal**: Production certificates expire every 90 days
- **API Key Rotation**: Consider rotating Binance API keys periodically
- **Configuration Updates**: Update all environments when adding new configuration options
- **Testing**: Always test configuration changes in local environment first

## Troubleshooting

### Certificate Issues
```bash
# Verify certificate content in .env file
grep -c "BEGIN CERTIFICATE" envs/jack_robot.crypto-vision.com/.env
grep -c "BEGIN PRIVATE KEY" envs/jack_robot.crypto-vision.com/.env
```

### Base64 Encoding Issues
```bash
# Test base64 encoding/decoding
base64 -w 0 envs/jack_robot.crypto-vision.com/.env | base64 -d | head -10
```

### Docker Testing
```bash
# Test environment file with Docker
docker run --rm -e ENV_CONTENT="$(base64 -w 0 envs/jack_robot.crypto-vision.com/.env)" \
  -e CERTIFICATE="jack_robot.crypto-vision.com" \
  crypto-robot status
```