# GitHub Actions Workflows

This directory contains the CI/CD workflows for the crypto robot dockerization project.

## 📚 Complete Documentation

For comprehensive documentation including all workflows, step-by-step deployment guides, and troubleshooting information, see:

**[CICD_WORKFLOW_DOCUMENTATION.md](../../CICD_WORKFLOW_DOCUMENTATION.md)**

This document provides:
- Detailed documentation for all 4 workflows
- Complete step-by-step deployment guide
- Comprehensive troubleshooting guide
- Security and best practices
- Emergency procedures

## Quick Reference

### Available Workflows

1. **build-robot-image** - Builds and pushes Docker images to DockerHub
2. **build-robot-infra** - Manages AWS infrastructure with Terraform
3. **control-robot-infra** - Controls EC2 instance lifecycle (start/stop/status)
4. **control-robot-aws** - Manages application deployment and operations
5. **get-ssh-key** - Reusable workflow for SSH key management (see below)

### Quick Start

1. **Setup Secrets** (see full documentation for details):
   ```
   DOCKERHUB_USERNAME, DOCKERHUB_TOKEN
   AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
   EC2_SSH_PRIVATE_KEY, ENV_CONTENT (per environment)
   ```

2. **Deploy Infrastructure**:
   - Run `build-robot-infra` with `action: plan` then `action: apply`

3. **Build Docker Image**:
   - Run `build-robot-image` with desired tag

4. **Deploy Application**:
   - Run `control-robot-aws` with `init_env: true` and appropriate commands

### Common Commands

**Check Status:**
```yaml
Workflow: control-robot-aws
Parameters:
  environment: jack_robot.crypto-vision.com
  execute_command: robot-image-status
```

**Full Deployment:**
```yaml
Workflow: control-robot-aws
Parameters:
  environment: jack_robot.crypto-vision.com
  init_env: true
  execute_command: update-robot-image,stop-robot,stop-webapp,start-robot,start-webapp
```

**Infrastructure Control:**
```yaml
Workflow: control-robot-infra
Parameters:
  action: start  # or stop, status, toggle
```

## Reusable Workflows

### get-ssh-key.yml - SSH Key Management

**Purpose:** Centralized SSH key management for workflows that need to connect to EC2 instances.

**Type:** Reusable workflow (called by other workflows)

**Key Features:**
- **Multiple Sources**: Tries artifacts first, falls back to GitHub secrets
- **Validation**: Checks key validity and sets proper permissions
- **Standardization**: Provides consistent SSH key setup across workflows
- **Fallback Strategy**: Ensures reliability with multiple key sources

**How to Use in Your Workflow:**

```yaml
jobs:
  get-ssh-key:
    uses: ./.github/workflows/get-ssh-key.yml
    secrets: inherit

  your-job-that-needs-ssh:
    needs: get-ssh-key
    runs-on: self-hosted
    if: needs.get-ssh-key.outputs.ssh_key_available == 'true'
    steps:
      - name: Setup SSH known hosts
        run: |
          ssh-keyscan -H ${{ env.INSTANCE_IP }} >> ~/.ssh/known_hosts
          
      - name: Use SSH
        run: |
          # SSH key is available at ~/.ssh/crypto-robot-key.pem
          ssh -i ~/.ssh/crypto-robot-key.pem ec2-user@${{ env.INSTANCE_IP }} "your-command"
```

**Outputs:**
- `ssh_key_available`: Boolean indicating if SSH key is available
- `key_source`: Source of the key (`artifact`, `secret`, or `none`)

**Key Sources (in priority order):**
1. **Workflow Artifacts**: From previous `build-robot-infra` runs
2. **GitHub Secrets**: `EC2_SSH_PRIVATE_KEY` secret
3. **None**: Reports failure if no key found

**Currently Used By:**
- `control-robot-aws.yml` - For application deployment and management

**Benefits:**
- ✅ **DRY Principle**: No duplicate SSH key logic across workflows
- ✅ **Centralized**: Single place to manage SSH key retrieval
- ✅ **Flexible**: Works with multiple key sources
- ✅ **Reliable**: Built-in fallback mechanisms
- ✅ **Maintainable**: Update SSH logic once, affects all workflows

## Legacy Documentation

The sections below provide basic information about the build-robot-image workflow. For complete documentation of all workflows, refer to the comprehensive documentation linked above.

### Build Robot Image Workflow

**Purpose:** Builds and pushes the Docker image to DockerHub registry.

**Key Features:**
- Multi-platform builds (linux/amd64, linux/arm64)
- Automatic certificate inclusion
- Comprehensive metadata and labels
- Usage examples in workflow summary

**Basic Usage:**
```bash
# Manual trigger via GitHub Actions UI
# Specify tag parameter (default: latest)

# Automatic trigger on push to main branch
git push origin main
```

**Example Docker Commands:**
```bash
# Local Development
docker run -d --name crypto-robot \
  -e ENV_CONTENT="$(base64 .env)" \
  -e CERTIFICATE="crypto-robot.local" \
  -p 5000:5000 \
  jmontiel/crypto-robot:latest

# Production Deployment  
docker run -d --name crypto-robot \
  -e ENV_CONTENT="$(base64 .env)" \
  -e CERTIFICATE="jack.crypto-robot-itechsource.com" \
  -p 5443:5443 \
  jmontiel/crypto-robot:latest
```

For complete setup instructions, troubleshooting, and all other workflows, see the [comprehensive documentation](../../CICD_WORKFLOW_DOCUMENTATION.md).