# Implementation Plan

- [x] 1. Remove Docker-related files and configurations



  - Delete docker directory and all Docker-related files
  - Remove Docker build workflow (build-robot-image.yml)
  - Clean up docker-compose configurations and Dockerfiles
  - _Requirements: 1.3, 1.4_

- [x] 2. Create Python deployment scripts

  - [x] 2.1 Create virtual environment setup script


    - Write script to create and configure Python virtual environment
    - Include dependency installation from requirements.txt
    - Add environment validation and error handling
    - _Requirements: 2.2, 2.4_

  - [x] 2.2 Create application startup scripts for direct Python execution


    - Write startup script for robot mode (replace Docker container startup)
    - Write startup script for webapp mode (replace Docker container startup)
    - Include proper environment variable loading and validation
    - _Requirements: 2.1, 5.1, 5.2_

  - [x] 2.3 Create systemd service definition files


    - Write crypto-robot.service file for trading robot process management
    - Write crypto-webapp.service file for web application process management
    - Include restart policies and proper user configuration
    - _Requirements: 5.3, 5.4_

- [x] 3. Implement GitHub secret API key injection system

  - [x] 3.1 Create API key injection script


    - Write script to retrieve API keys from GitHub secrets using <HOST>_KEYS pattern
    - Implement JSON parsing and validation for API key structure
    - Add error handling for missing or invalid secrets
    - _Requirements: 3.1, 3.2, 3.5_

  - [x] 3.2 Create environment file management utilities


    - Write script to merge base .env with injected API keys
    - Preserve existing environment variables while updating API key sections
    - Add validation for required environment variables
    - _Requirements: 3.4, 3.2_

- [x] 4. Update GitHub Actions workflows for Python deployment

  - [x] 4.1 Update control-robot-aws.yml workflow


    - Replace Docker commands with git clone/pull operations
    - Add Python virtual environment setup steps
    - Integrate API key injection from GitHub secrets
    - Update service management commands (systemd instead of Docker)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [x] 4.2 Remove build-robot-image.yml workflow

    - Delete the Docker image build workflow file
    - Update any references to the build workflow in other files
    - _Requirements: 4.1_

- [x] 5. Create service management and monitoring scripts

  - [x] 5.1 Create service control scripts


    - Write script to start/stop/restart Python services using systemd
    - Add service status checking and health monitoring
    - Include log file management and rotation
    - _Requirements: 5.1, 5.2, 5.4_

  - [x] 5.2 Create deployment health check script


    - Write script to validate successful deployment
    - Check Python application startup and port binding
    - Validate SSL certificate configuration
    - Test API connectivity and basic functionality
    - _Requirements: 5.1, 5.2, 5.3_

- [x] 6. Update SSL certificate management for direct deployment

  - [x] 6.1 Modify certificate configuration scripts


    - Update certificate path resolution for direct file system access
    - Remove Docker container mounting logic
    - Add certificate validation before service startup
    - _Requirements: 5.2_

  - [x] 6.2 Update environment configuration for certificate paths


    - Modify .env template to use direct file system paths
    - Update certificate selection logic based on hostname
    - _Requirements: 6.2_

- [x] 7. Create comprehensive documentation and maintenance guides

  - [x] 7.1 Update deployment documentation


    - Rewrite deployment guides to reflect Python-based process
    - Remove Docker-specific instructions and add Python setup steps
    - Update troubleshooting guides for direct Python execution
    - _Requirements: 6.1, 6.3, 6.4_

  - [x] 7.2 Create maintenance and version update documentation


    - Write step-by-step procedures for updating application versions
    - Document rollback procedures for failed deployments
    - Create monitoring and health check procedures for Python applications
    - Include backup and restore procedures for direct deployment architecture
    - _Requirements: 7.1, 7.2, 7.3, 7.5_

  - [x] 7.3 Update configuration documentation


    - Update README files with new deployment instructions
    - Document GitHub secret configuration requirements
    - Update environment variable documentation
    - _Requirements: 6.2, 6.5_

- [x] 8. Create testing and validation scripts

  - [x] 8.1 Create deployment validation tests


    - Write tests to validate Python environment setup
    - Create tests for API key injection functionality
    - Add tests for service startup and configuration
    - _Requirements: 2.4, 3.1, 5.1_

  - [x] 8.2 Create integration tests for the new deployment system


    - Write end-to-end deployment tests
    - Create tests for multi-environment deployment scenarios
    - Add performance comparison tests (Python vs Docker startup times)
    - _Requirements: 4.2, 4.3, 5.2_

- [x] 9. Implement migration and cleanup procedures


  - [x] 9.1 Create migration script for existing deployments


    - Write script to migrate from Docker-based to Python-based deployment
    - Include data migration for databases and configuration files
    - Add validation steps to ensure successful migration
    - _Requirements: 1.1, 1.2_

  - [x] 9.2 Create cleanup script for Docker artifacts


    - Write script to remove Docker containers, images, and volumes
    - Clean up Docker-related configuration files
    - Remove unused Docker build artifacts
    - _Requirements: 1.3, 1.4_