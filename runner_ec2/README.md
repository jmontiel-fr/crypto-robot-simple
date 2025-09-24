# GitHub Actions Self-Hosted Runner (EC2)

This folder contains information about the GitHub Actions self-hosted runner setup that was attempted on the EC2 instance.

## Status: DISCONTINUED

The self-hosted runner setup has been **discontinued** and cleaned up for the following reasons:

1. **Complexity**: Setting up and maintaining a self-hosted runner adds operational overhead
2. **Reliability**: GitHub hosted runners are more reliable and maintained by GitHub
3. **Security**: GitHub hosted runners provide better isolation and security
4. **Simplicity**: Using GitHub hosted runners requires no additional setup or maintenance

## Current Workflow Configuration

All workflows now use **GitHub hosted runners** (`ubuntu-latest`) which provide:

- ✅ **Zero maintenance** - GitHub manages the infrastructure
- ✅ **Latest tools** - Always up-to-date with latest versions
- ✅ **High availability** - GitHub's infrastructure reliability
- ✅ **Security** - Fresh, isolated environment for each run
- ✅ **Scalability** - No queue times during peak usage

## Workflow Runner Configuration

All workflows use:
```yaml
runs-on: ubuntu-latest
```

## Tools Available on GitHub Hosted Runners

GitHub hosted runners come pre-installed with:
- Terraform (latest)
- AWS CLI v2 (latest)
- Docker (latest)
- Git (latest)
- Node.js, Python, Java, and many other tools

## EC2 Instance Usage

The EC2 instance is still available and has the following tools installed:
- ✅ **Terraform v1.13.3** (latest)
- ✅ **AWS CLI v2.30.4** (latest)  
- ✅ **Docker v25.0.8** (latest)
- ✅ **Git v2.50.1** (latest)

The EC2 instance can be used for:
- Manual deployments
- Development and testing
- Running the crypto robot application
- Direct Terraform operations

## Authentication

Workflows use GitHub Secrets for AWS authentication:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

The EC2 instance uses IAM roles for AWS authentication.

## Performance

GitHub hosted runners provide excellent performance:
- Fast provisioning (10-30 seconds)
- High-performance compute resources
- Reliable network connectivity
- No maintenance overhead

## Conclusion

The decision to use GitHub hosted runners provides the best balance of:
- **Performance** - Fast and reliable execution
- **Simplicity** - No setup or maintenance required
- **Security** - Isolated, fresh environments
- **Cost** - No additional infrastructure costs
- **Reliability** - GitHub's managed infrastructure

This approach allows the team to focus on development rather than infrastructure management.