# GitHub Configuration Guide - Crypto Robot Python Deployment

## Overview

This guide provides detailed instructions for configuring GitHub repository settings, secrets, and variables required for the Crypto Robot Python direct deployment system.

**Instance Architecture:**
- **Target Instance**: `web-crypto-robot-instance` - Where the crypto robot application runs
- **Runner Instance**: `runner-jmontiel-fr-crypto-robot` - Executes GitHub Actions workflows

## Table of Contents

1. [Repository Settings](#repository-settings)
2. [GitHub Secrets](#github-secrets)
3. [GitHub Variables](#github-variables)
4. [Environment Configuration](#environment-configuration)
5. [Workflow Permissions](#workflow-permissions)
6. [Setup Instructions](#setup-instructions)
7. [Validation](#validation)
8. [Troubleshooting](#troubleshooting)

## Repository Settings

### Actions Settings

1. **Navigate to Repository Settings**:
   - Go to your repository → Settings → Actions → General

2. **Actions Permissions**:
   - ✅ Allow all actions and reusable workflows
   - ✅ Allow actions created by GitHub
   - ✅ Allow actions by Marketplace verified creators

3. **Workflow Permissions**:
   - ✅ Read and write permissions
   - ✅ Allow GitHub Actions to create and approve pull requests

4. **Fork Pull Request Workflows**:
   - ✅ Run workflows from fork pull requests (if needed)

## GitHub Secrets

### Required Secrets

Navigate to: **Repository → Settings → Secrets and variables → Actions**

#### 1. AWS Configuration Secrets

| Secret Name | Description | Example Value | Required |
|-------------|-------------|---------------|----------|
| `AWS_ACCESS_KEY_ID` | AWS access key for managing target EC2 instance | `AKIAIOSFODNN7EXAMPLE` | ✅ |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key for managing target EC2 instance | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` | ✅ |

#### 2. API Keys Secrets (Environment-Specific)

**Pattern**: `<HOSTNAME_UPPERCASE>_KEYS`

| Environment | Secret Name | Description |
|-------------|-------------|-------------|
| `jack_robot.crypto-vision.com` | `JACK_ROBOT_CRYPTO_VISION_COM_KEYS` | Production API keys for jack_robot |
| `its_robot.crypto-vision.com` | `ITS_ROBOT_CRYPTO_VISION_COM_KEYS` | Production API keys for its_robot |

**API Key Secret Format**:

```
BINANCE_API_KEY=your_actual_binance_api_key_here
BINANCE_SECRET_KEY=your_actual_binance_secret_key_here
```

**Important**: Only sensitive API keys are stored in GitHub secrets. Configuration variables like FLASK_HOST, FLASK_PORT, USE_HTTPS are configured in the `.env` files within the repository.

**Note**: SSL certificates are NOT stored in GitHub secrets. They are embedded in the `.env` files and extracted to the filesystem during deployment.

#### 3. Environment Files with Certificates (Optional)

SSL certificates are embedded directly in the `.env` files, not as separate GitHub secrets. The certificates are extracted from the `.env` file during deployment and placed in the filesystem at the locations specified in the `.env` configuration.

**Certificate Handling Process**:
1. Certificates are embedded in `.env` files as `SSL_CERT_CONTENT` and `SSL_KEY_CONTENT`
2. During deployment, the certificate configuration script extracts them to filesystem
3. Certificate paths in `.env` point to the extracted file locations

### Secret Creation Instructions

#### Step 1: Create AWS Secrets

1. Go to **Settings → Secrets and variables → Actions**
2. Click **New repository secret**
3. Create each AWS secret:

```
Name: AWS_ACCESS_KEY_ID
Secret: [Your AWS Access Key ID]
```

```
Name: AWS_SECRET_ACCESS_KEY
Secret: [Your AWS Secret Access Key]
```

#### Step 2: Create API Key Secrets

For each environment, create a secret with the hostname-based naming pattern:

**Example for jack_robot.crypto-vision.com**:

**Example for jack_robot.crypto-vision.com**:
```
Name: JACK_ROBOT_CRYPTO_VISION_COM_KEYS
Secret: BINANCE_API_KEY=your_key
BINANCE_SECRET_KEY=your_secret
```

**Hostname to Secret Name Conversion**:
- Replace dots (.) with underscores (_)
- Replace hyphens (-) with underscores (_)
- Convert to uppercase
- Add `_KEYS` suffix

Examples:
- `crypto-robot.local` → `CRYPTO_ROBOT_LOCAL_KEYS`
- `jack_robot.crypto-vision.com` → `JACK_ROBOT_CRYPTO_VISION_COM_KEYS`
- `test-env.example.com` → `TEST_ENV_EXAMPLE_COM_KEYS`

## GitHub Variables

### Repository Variables

**Note**: Most configuration variables are managed in `.env` files within the repository, not as GitHub variables. Only workflow-specific variables should be configured here if needed.

Navigate to: **Repository → Settings → Secrets and variables → Actions → Variables**

| Variable Name | Description | Default Value | Required |
|---------------|-------------|---------------|----------|
| `ACTIONS_STEP_DEBUG` | Enable debug mode for workflows | `false` | ⚠️ Optional |

### Configuration in .env Files

The following configuration variables are managed in the `.env` files within the repository, **NOT** in GitHub secrets or variables:

#### Application Configuration (in .env files):
- `FLASK_HOST` - Web server host (e.g., `0.0.0.0`, `127.0.0.1`)
- `FLASK_PORT` - Web server port (e.g., `5000`, `5443`)
- `USE_HTTPS` - Enable HTTPS (e.g., `true`, `false`)
- `FLASK_PROTOCOL` - Protocol (e.g., `http`, `https`)
- `DOMAIN_NAME` - Domain name for the environment
- `HOSTNAME` - Hostname for certificate management

#### System Configuration (in .env files):
- `DATABASE_TYPE` - Database type (`sqlite`, `postgresql`)
- `DATABASE_PATH` - Database directory path
- `STARTING_CAPITAL` - Trading capital amount
- `ROBOT_DRY_RUN` - Dry run mode (`true`, `false`)

#### Workflow Configuration (hardcoded in workflows):
- Python version: `3.11` (configured in setup scripts)
- AWS region: `eu-west-1` (configured in workflows)
- Target instance: `web-crypto-robot-instance` (where the application runs)
- Runner instance: `runner-jmontiel-fr-crypto-robot` (executes GitHub Actions workflows)

## SSL Certificate Management

SSL certificates are **NOT stored in GitHub secrets**. They are embedded in the `.env` files and extracted to the filesystem during deployment. 

For detailed certificate management instructions, see the [Python Deployment Guide](PYTHON-DEPLOYMENT-GUIDE.md#ssl-certificate-setup).

## Environment Configuration

### GitHub Environments

Create environments for each deployment target:

1. **Navigate to Environments**:
   - Repository → Settings → Environments

2. **Create Environment**:
   - Click "New environment"
   - Name: `crypto-robot.local` (or your hostname)

3. **Environment Protection Rules** (Optional):
   - ✅ Required reviewers
   - ✅ Wait timer
   - ✅ Deployment branches

4. **Environment Secrets**:
   - Add environment-specific secrets if needed
   - These override repository secrets

### Environment Setup Example

**Environment Name**: `jack_robot.crypto-vision.com`

**Environment Secrets**:
```
JACK_ROBOT_CRYPTO_VISION_COM_KEYS: BINANCE_API_KEY=prod_key
BINANCE_SECRET_KEY=prod_secret
```

**Note**: `crypto-robot.local` environment doesn't use GitHub secrets - API keys are configured directly in the local `.env` file.

**Environment Variables**:
```
FLASK_PORT: 5000
FLASK_HOST: 0.0.0.0
USE_HTTPS: true
DOMAIN_NAME: jack_robot.crypto-vision.com
```

## Workflow Permissions

### Required Permissions

The GitHub Actions workflows require the following permissions:

```yaml
permissions:
  contents: read          # Read repository content
  actions: write          # Manage workflow runs
  secrets: read           # Access repository secrets
  id-token: write         # AWS OIDC (if using)
```

### OIDC Configuration (Advanced)

For enhanced security, you can configure OpenID Connect (OIDC) with AWS:

1. **Create OIDC Provider in AWS**
2. **Configure Trust Relationship**
3. **Add OIDC Secrets**:

```
AWS_ROLE_TO_ASSUME: arn:aws:iam::123456789012:role/GitHubActionsRole
AWS_ROLE_SESSION_NAME: GitHubActions
```

## Setup Instructions

### Step-by-Step Setup

#### 1. Prepare Your Information

Gather the following information:
- AWS Access Key ID and Secret Access Key (for managing `web-crypto-robot-instance`)
- Binance API keys for each production environment
- Hostnames for each deployment environment
- SSL certificates (if using HTTPS)

**Note**: The GitHub Actions workflows run on `runner-jmontiel-fr-crypto-robot` and deploy to `web-crypto-robot-instance`.

#### 2. Create Repository Secrets

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID: [Your AWS Access Key]
AWS_SECRET_ACCESS_KEY: [Your AWS Secret Key]

# API Keys for production environments only
JACK_ROBOT_CRYPTO_VISION_COM_KEYS: BINANCE_API_KEY=prod_key
BINANCE_SECRET_KEY=prod_secret

ITS_ROBOT_CRYPTO_VISION_COM_KEYS: BINANCE_API_KEY=prod_key
BINANCE_SECRET_KEY=prod_secret

# Note: crypto-robot.local uses .env file directly (no GitHub secret needed)
# Note: Flask configuration is in .env files, not GitHub secrets

# Note: SSL certificates are embedded in .env files, not GitHub secrets
```

#### 3. Create Environments

For each deployment target:
1. Create environment with hostname as name
2. Add environment-specific variables
3. Configure protection rules if needed

#### 4. Test Configuration

Run the workflow with `application-status` command to test configuration. The workflow will:
1. Execute on the runner instance (`runner-jmontiel-fr-crypto-robot`)
2. Connect to the target instance (`web-crypto-robot-instance`)
3. Check the application status on the target instance

### Configuration Validation Script

Create a simple validation script:

```bash
#!/bin/bash
# validate-github-config.sh

echo "🔍 Validating GitHub Configuration"

# Check required secrets (you'll need to verify these manually)
echo "Required Secrets:"
echo "  ✅ AWS_ACCESS_KEY_ID"
echo "  ✅ AWS_SECRET_ACCESS_KEY"
echo "  ✅ [HOSTNAME]_KEYS for each environment"

# Check environments
echo "Required Environments:"
echo "  ✅ crypto-robot.local"
echo "  ✅ jack_robot.crypto-vision.com"
echo "  ✅ its_robot.crypto-vision.com"

echo "✅ Manual verification required for secrets"
```

## Validation

### Testing Your Configuration

#### 1. Test Workflow Execution

1. Go to **Actions** tab
2. Select **control-robot-aws** workflow
3. Click **Run workflow**
4. Select environment: `crypto-robot.local`
5. Command: `application-status`
6. Run workflow

#### 2. Verify Secret Access

Check workflow logs for:
- ✅ AWS credentials working
- ✅ API keys retrieved successfully
- ✅ Environment variables loaded

#### 3. Test Each Environment

Repeat the test for each configured environment:
- `crypto-robot.local`
- `jack_robot.crypto-vision.com`
- `its_robot.crypto-vision.com`

### Common Validation Issues

| Issue | Symptom | Solution |
|-------|---------|----------|
| AWS credentials invalid | "Unable to locate credentials" | Verify AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY |
| API keys not found | "GitHub secret not found" | Check secret name matches hostname pattern |
| Secret format error | "Failed to extract API keys" | Use key=value or JSON format in API key secrets |
| Environment not found | "Environment does not exist" | Create environment with exact hostname |
| Certificate extraction fails | "SSL certificate content not found" | See deployment guide for certificate setup |

## Troubleshooting

### Common Issues

#### 1. Secret Not Found Error

**Error**: `GitHub secret not found: HOSTNAME_KEYS`

**Solution**:
1. Verify secret name follows pattern: `<HOSTNAME_UPPERCASE>_KEYS`
2. Check hostname conversion (dots → underscores, uppercase)
3. Ensure secret exists in repository secrets

#### 2. AWS Permission Denied

**Error**: `An error occurred (UnauthorizedOperation)`

**Solution**:
1. Verify AWS credentials are correct
2. Check IAM permissions for EC2 operations
3. Ensure region is correct

#### 3. Secret Format Error

**Error**: `Failed to extract API keys from secret`

**Solution**:
1. Use the simple key=value format:
   ```
   BINANCE_API_KEY=your_key
   BINANCE_SECRET_KEY=your_secret
   ```
2. Ensure Flask configuration is in .env files, not GitHub secrets
3. Local development (crypto-robot.local) doesn't need GitHub secrets
3. Ensure no extra spaces or special characters
4. Validate JSON syntax if using JSON format

#### 4. Environment Access Error

**Error**: `Environment 'hostname' not found`

**Solution**:
1. Create environment with exact hostname
2. Check environment name matches workflow input
3. Verify environment is not archived

#### 5. Certificate Issues

**Error**: Certificate-related deployment errors

**Solution**:
1. Refer to the [Python Deployment Guide](PYTHON-DEPLOYMENT-GUIDE.md#ssl-certificate-setup) for certificate setup
2. Certificates are managed in .env files, not GitHub secrets
3. Use the certificate configuration scripts provided in the deployment guide

### Debug Mode

Enable debug mode in workflows:

1. **Repository Settings → Secrets and variables → Actions**
2. **Add Variable**:
   ```
   Name: ACTIONS_STEP_DEBUG
   Value: true
   ```

3. **Add Secret**:
   ```
   Name: ACTIONS_RUNNER_DEBUG
   Value: true
   ```

### Support Checklist

When seeking support, provide:

- [ ] Repository name and visibility (public/private)
- [ ] Environment names being used
- [ ] Workflow run URL with error
- [ ] Screenshot of secrets configuration (names only, not values)
- [ ] AWS region and instance details:
  - [ ] Target instance: `web-crypto-robot-instance`
  - [ ] Runner instance: `runner-jmontiel-fr-crypto-robot`
- [ ] Error messages from workflow logs

## Security Best Practices

### Secret Management

1. **Rotate Secrets Regularly**:
   - API keys: Every 90 days
   - AWS credentials: Every 180 days

2. **Use Environment-Specific Secrets**:
   - Separate production and development keys
   - Use different AWS accounts if possible

3. **Monitor Secret Usage**:
   - Review workflow logs regularly
   - Set up alerts for failed authentications

4. **Principle of Least Privilege**:
   - AWS IAM: Only required EC2 permissions
   - Binance API: Only required trading permissions

### Access Control

1. **Repository Access**:
   - Limit who can modify secrets
   - Use branch protection rules
   - Require reviews for workflow changes

2. **Environment Protection**:
   - Use required reviewers for production
   - Set deployment branch restrictions
   - Configure wait timers for critical environments

## Maintenance

### Regular Tasks

#### Monthly
- [ ] Review and rotate API keys
- [ ] Check AWS credential expiration
- [ ] Validate all environments are working
- [ ] Update documentation if hostnames change

#### Quarterly
- [ ] Rotate AWS credentials
- [ ] Review IAM permissions
- [ ] Update SSL certificates if needed
- [ ] Audit secret usage in workflows

#### Annually
- [ ] Review all security configurations
- [ ] Update to latest GitHub Actions features
- [ ] Validate disaster recovery procedures

---

## Quick Reference

### Instance Architecture
- **Target Instance**: `web-crypto-robot-instance` (runs applications)
- **Runner Instance**: `runner-jmontiel-fr-crypto-robot` (executes workflows)

### Secret Name Patterns
```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
<HOSTNAME_UPPERCASE>_KEYS
```

### Hostname Conversion Examples
```
jack_robot.crypto-vision.com → JACK_ROBOT_CRYPTO_VISION_COM_KEYS
its_robot.crypto-vision.com → ITS_ROBOT_CRYPTO_VISION_COM_KEYS
```

### API Key Secret Format
```
BINANCE_API_KEY=your_key_here
BINANCE_SECRET_KEY=your_secret_here
```

### Configuration Management
- **GitHub Secrets**: Only sensitive API keys for production environments
- **.env Files**: All configuration (FLASK_HOST, FLASK_PORT, USE_HTTPS, etc.)
- **Local Development**: API keys configured directly in .env file (no GitHub secrets)

---

*This configuration guide ensures secure and reliable deployment of the Crypto Robot using GitHub Actions with Python direct deployment.*