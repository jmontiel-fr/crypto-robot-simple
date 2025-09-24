# Requirements Document

## Introduction

This feature transforms the crypto robot deployment architecture from Docker-based containerization to direct Python deployment on EC2 instances. The goal is to simplify the deployment process by eliminating Docker complexity while maintaining secure API key management through GitHub secrets and enabling direct git-based deployments.

## Requirements

### Requirement 1

**User Story:** As a DevOps engineer, I want to remove Docker dependencies from the deployment process, so that I can simplify the infrastructure and reduce deployment complexity.

#### Acceptance Criteria

1. WHEN the deployment process is executed THEN the system SHALL NOT use Docker containers for running the robot or webapp
2. WHEN Docker-related files are removed THEN the system SHALL maintain all existing functionality through direct Python execution
3. WHEN the cleanup is complete THEN the system SHALL have removed all Docker build workflows, Dockerfiles, and docker-compose configurations
4. WHEN the new deployment runs THEN the system SHALL execute Python applications directly on the EC2 instance without containerization

### Requirement 2

**User Story:** As a developer, I want the robot and webapp to be deployed via git clone commands, so that I can have a simpler and more transparent deployment process.

#### Acceptance Criteria

1. WHEN a deployment is triggered THEN the system SHALL clone the latest code from the GitHub repository to the target EC2 instance
2. WHEN the git clone completes THEN the system SHALL install Python dependencies using pip and requirements.txt
3. WHEN the code is updated THEN the system SHALL pull the latest changes from the repository without rebuilding containers
4. WHEN the deployment process runs THEN the system SHALL set up the Python virtual environment and install all required packages

### Requirement 3

**User Story:** As a security-conscious developer, I want Binance API keys to be injected from GitHub secrets into the .env file during deployment, so that sensitive credentials are managed securely.

#### Acceptance Criteria

1. WHEN deploying to an environment THEN the system SHALL retrieve API keys from GitHub secrets using the pattern `<HOST>_KEYS`
2. WHEN the .env file is created on EC2 THEN the system SHALL inject the Binance API key definitions from the corresponding GitHub secret
3. WHEN running locally THEN the system SHALL use existing .env files that already contain the API keys for testing
4. WHEN the secret injection occurs THEN the system SHALL preserve all other environment variables while only updating the API key sections
5. WHEN the GitHub secret is not found THEN the system SHALL fail the deployment with a clear error message

### Requirement 4

**User Story:** As a developer, I want the GitHub workflows to be updated to support the new deployment method, so that I can deploy and manage the robot without Docker dependencies.

#### Acceptance Criteria

1. WHEN the build-robot-image workflow is removed THEN the system SHALL no longer attempt to build or push Docker images
2. WHEN the control-robot-aws workflow is updated THEN the system SHALL use git clone and Python execution instead of Docker commands
3. WHEN starting the robot THEN the system SHALL execute Python scripts directly with proper environment setup
4. WHEN stopping the robot THEN the system SHALL terminate Python processes instead of stopping Docker containers
5. WHEN checking status THEN the system SHALL report on Python process status instead of Docker container status

### Requirement 5

**User Story:** As a system administrator, I want the EC2 instance to run Python applications with proper process management, so that the applications are reliable and can be monitored effectively.

#### Acceptance Criteria

1. WHEN the robot is started THEN the system SHALL run the Python application as a background process with proper logging
2. WHEN the webapp is started THEN the system SHALL run the Flask application with appropriate port binding and SSL configuration
3. WHEN processes are managed THEN the system SHALL use systemd or similar process management for reliability
4. WHEN applications crash THEN the system SHALL have restart capabilities and proper error logging
5. WHEN multiple environments are deployed THEN the system SHALL isolate processes and configurations appropriately

### Requirement 6

**User Story:** As a developer, I want all documentation and configuration files to be updated to reflect the new deployment architecture, so that the system is properly documented and maintainable.

#### Acceptance Criteria

1. WHEN documentation is updated THEN the system SHALL reflect the new Python-based deployment process in all relevant files
2. WHEN configuration files are updated THEN the system SHALL remove Docker-specific configurations and add Python-specific ones
3. WHEN README files are updated THEN the system SHALL provide clear instructions for the new deployment method
4. WHEN troubleshooting guides are updated THEN the system SHALL include Python-specific debugging and monitoring information
5. WHEN the update is complete THEN the system SHALL have consistent documentation across all files

### Requirement 7

**User Story:** As a system maintainer, I want comprehensive maintenance documentation that details how to update application versions, so that I can efficiently manage and upgrade the system over time.

#### Acceptance Criteria

1. WHEN maintenance documentation is created THEN the system SHALL include step-by-step procedures for updating to new application versions
2. WHEN version update procedures are documented THEN the system SHALL include rollback procedures in case of deployment failures
3. WHEN maintenance documentation is provided THEN the system SHALL include monitoring and health check procedures for the Python applications
4. WHEN troubleshooting guides are created THEN the system SHALL include common issues and their solutions for Python-based deployments
5. WHEN backup procedures are documented THEN the system SHALL include database backup and restore procedures for the direct deployment architecture
6. WHEN the maintenance guide is complete THEN the system SHALL include procedures for managing multiple environments and their configurations