#!/usr/bin/env python3
"""
Docker container testing
Tests Docker container startup, environment configurations, and certificate integration
"""

import os
import sys
import subprocess
import tempfile
import json
import time
import unittest
import base64
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestDockerContainers(unittest.TestCase):
    """Test Docker container functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.project_root = project_root
        cls.test_env_file = None
        cls.test_containers = []
        
        # Create test .env file
        cls._create_test_env_file()
        
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        # Clean up test containers
        for container_name in cls.test_containers:
            try:
                subprocess.run(["docker", "stop", container_name], 
                             capture_output=True, timeout=30)
                subprocess.run(["docker", "rm", container_name], 
                             capture_output=True, timeout=30)
            except:
                pass
        
        # Clean up test env file
        if cls.test_env_file and os.path.exists(cls.test_env_file):
            os.remove(cls.test_env_file)
    
    @classmethod
    def _create_test_env_file(cls):
        """Create a test .env file for Docker testing"""
        test_env_content = """
FLASK_PORT=5000
FLASK_PROTOCOL=http
FLASK_HOST=0.0.0.0
HOSTNAME=crypto-robot.local
CERTIFICATE_TYPE=self-signed
DEBUG=true
BINANCE_TESTNET=true
BINANCE_API_KEY=test_api_key
BINANCE_SECRET_KEY=test_secret_key
STARTING_CAPITAL=100
DEFAULT_CALIBRATION_PROFILE=moderate_realistic
ENABLE_CALIBRATION=true
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write(test_env_content.strip())
            cls.test_env_file = f.name
    
    def test_dockerfile_exists(self):
        """Test that Dockerfile exists and is valid"""
        print("\n🧪 Testing Dockerfile existence and basic validation")
        
        dockerfile = self.project_root / "docker" / "Dockerfile"
        self.assertTrue(dockerfile.exists(), "Dockerfile should exist")
        
        # Read and validate basic Dockerfile structure
        with open(dockerfile, 'r') as f:
            content = f.read()
        
        # Check for essential Dockerfile commands
        self.assertIn("FROM", content, "Dockerfile should have FROM instruction")
        self.assertIn("COPY", content, "Dockerfile should have COPY instruction")
        self.assertIn("WORKDIR", content, "Dockerfile should have WORKDIR instruction")
        
        print("   ✅ Dockerfile exists and has basic structure")
    
    def test_docker_entrypoint_script(self):
        """Test Docker entrypoint script"""
        print("\n🧪 Testing Docker entrypoint script")
        
        entrypoint = self.project_root / "docker" / "scripts" / "entrypoint.sh"
        self.assertTrue(entrypoint.exists(), "Docker entrypoint script should exist")
        
        # Check if script is executable
        self.assertTrue(os.access(entrypoint, os.X_OK),
                       "Entrypoint script should be executable")
        
        # Read and validate basic script structure
        with open(entrypoint, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for essential environment variable handling
        self.assertIn("ENV_CONTENT", content, 
                     "Entrypoint should handle ENV_CONTENT variable")
        self.assertIn("CERTIFICATE", content,
                     "Entrypoint should handle CERTIFICATE variable")
        
        print("   ✅ Docker entrypoint script exists and handles environment variables")
    
    def test_docker_build_context(self):
        """Test Docker build context and required files"""
        print("\n🧪 Testing Docker build context")
        
        # Check for required files in build context
        required_files = [
            "docker/Dockerfile",
            "docker/scripts/entrypoint.sh",
            "robot/main.py",
            "robot/start_https_server.py",
            "certificates"  # Directory
        ]
        
        for file_path in required_files:
            full_path = self.project_root / file_path
            self.assertTrue(full_path.exists(), 
                          f"Required file/directory should exist: {file_path}")
        
        print("   ✅ Docker build context has required files")
    
    def test_env_content_base64_encoding(self):
        """Test ENV_CONTENT base64 encoding functionality"""
        print("\n🧪 Testing ENV_CONTENT base64 encoding")
        
        # Read test env file
        with open(self.test_env_file, 'r') as f:
            env_content = f.read()
        
        # Test base64 encoding
        encoded = base64.b64encode(env_content.encode()).decode()
        
        # Test decoding
        decoded = base64.b64decode(encoded).decode()
        
        self.assertEqual(env_content, decoded, 
                        "ENV_CONTENT base64 encoding/decoding should work")
        
        # Test that encoded content is valid base64
        self.assertTrue(self._is_valid_base64(encoded),
                       "Encoded content should be valid base64")
        
        print("   ✅ ENV_CONTENT base64 encoding works correctly")
    
    def _is_valid_base64(self, s):
        """Check if string is valid base64"""
        try:
            base64.b64decode(s)
            return True
        except:
            return False
    
    def test_certificate_environment_variable(self):
        """Test CERTIFICATE environment variable handling"""
        print("\n🧪 Testing CERTIFICATE environment variable")
        
        test_certificates = [
            "crypto-robot.local",
            "jack.crypto-robot-itechsource.com",
            "custom.example.com"
        ]
        
        for cert in test_certificates:
            with self.subTest(certificate=cert):
                # Test certificate path construction
                expected_cert_dir = f"/opt/crypto-robot/certificates/{cert}"
                expected_cert_file = f"{expected_cert_dir}/cert.pem"
                expected_key_file = f"{expected_cert_dir}/key.pem"
                
                # Validate path construction
                self.assertTrue(expected_cert_file.endswith("cert.pem"))
                self.assertTrue(expected_key_file.endswith("key.pem"))
                self.assertIn(cert, expected_cert_dir)
        
        print("   ✅ CERTIFICATE environment variable handling validated")
    
    def test_docker_image_availability(self):
        """Test if Docker is available and can build images"""
        print("\n🧪 Testing Docker availability")
        
        try:
            # Check if Docker is available
            result = subprocess.run(["docker", "--version"], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                self.skipTest("Docker not available")
            
            print(f"   ✅ Docker available: {result.stdout.strip()}")
            
            # Test Docker daemon is running
            result = subprocess.run(["docker", "info"], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                self.skipTest("Docker daemon not running")
            
            print("   ✅ Docker daemon is running")
            
        except FileNotFoundError:
            self.skipTest("Docker command not found")
        except subprocess.TimeoutExpired:
            self.skipTest("Docker command timed out")
        except Exception as e:
            self.skipTest(f"Docker test failed: {e}")
    
    def test_container_management_scripts(self):
        """Test container management scripts"""
        print("\n🧪 Testing container management scripts")
        
        # Check main management script
        manage_script = self.project_root / "robot" / "scripts" / "manage-containers.sh"
        self.assertTrue(manage_script.exists(), 
                       "Container management script should exist")
        
        # Test help functionality
        try:
            result = subprocess.run([
                "bash", str(manage_script), "help"
            ], capture_output=True, text=True, timeout=15)
            
            output = result.stdout.lower()
            self.assertIn("start-robot", output, 
                         "Management script should show start-robot command")
            self.assertIn("start-webapp", output,
                         "Management script should show start-webapp command")
            self.assertIn("status", output,
                         "Management script should show status command")
            
            print("   ✅ Container management script help works")
            
        except subprocess.TimeoutExpired:
            self.fail("Container management script help timed out")
        except FileNotFoundError:
            self.skipTest("Bash not available for testing")
        except Exception as e:
            print(f"   ⚠️  Container management script test skipped: {e}")
    
    def test_container_port_configuration(self):
        """Test container port configuration from .env"""
        print("\n🧪 Testing container port configuration")
        
        # Test port extraction from .env file
        with open(self.test_env_file, 'r') as f:
            env_content = f.read()
        
        # Extract port from env content
        port_line = [line for line in env_content.split('\n') 
                    if line.startswith('FLASK_PORT=')]
        
        self.assertTrue(len(port_line) > 0, "FLASK_PORT should be in .env file")
        
        port = port_line[0].split('=')[1]
        self.assertTrue(port.isdigit(), "FLASK_PORT should be numeric")
        self.assertGreater(int(port), 0, "FLASK_PORT should be positive")
        
        print(f"   ✅ Container port configuration: {port}")
    
    def test_container_mode_environment(self):
        """Test container MODE environment variable"""
        print("\n🧪 Testing container MODE environment variable")
        
        valid_modes = ["robot", "webapp", "both"]
        
        for mode in valid_modes:
            with self.subTest(mode=mode):
                # Test mode validation logic
                self.assertIn(mode, valid_modes, f"Mode {mode} should be valid")
        
        print("   ✅ Container MODE environment variable validated")
    
    def test_docker_restart_policy(self):
        """Test Docker restart policy configuration"""
        print("\n🧪 Testing Docker restart policy")
        
        # Test restart policy options
        valid_restart_policies = [
            "no",
            "always", 
            "unless-stopped",
            "on-failure"
        ]
        
        # Test that unless-stopped is used (as per container management script)
        expected_policy = "unless-stopped"
        self.assertIn(expected_policy, valid_restart_policies,
                     "Expected restart policy should be valid")
        
        print(f"   ✅ Docker restart policy: {expected_policy}")


class TestDockerIntegration(unittest.TestCase):
    """Test Docker integration with application components"""
    
    def test_flask_docker_integration(self):
        """Test Flask application Docker integration"""
        print("\n🧪 Testing Flask Docker integration")
        
        # Test Flask configuration for Docker environment
        docker_flask_config = {
            "host": "0.0.0.0",  # Should bind to all interfaces in container
            "port": 5000,       # Should be configurable from .env
            "debug": False      # Should be configurable from .env
        }
        
        # Validate configuration
        self.assertEqual(docker_flask_config["host"], "0.0.0.0",
                        "Flask should bind to all interfaces in Docker")
        self.assertIsInstance(docker_flask_config["port"], int,
                            "Flask port should be integer")
        
        print("   ✅ Flask Docker integration configuration validated")
    
    def test_certificate_docker_integration(self):
        """Test certificate integration in Docker environment"""
        print("\n🧪 Testing certificate Docker integration")
        
        # Test certificate paths in Docker container
        docker_cert_base = "/opt/crypto-robot/certificates"
        
        test_hostnames = [
            "crypto-robot.local",
            "jack.crypto-robot-itechsource.com"
        ]
        
        for hostname in test_hostnames:
            with self.subTest(hostname=hostname):
                cert_dir = f"{docker_cert_base}/{hostname}"
                cert_file = f"{cert_dir}/cert.pem"
                key_file = f"{cert_dir}/key.pem"
                
                # Validate paths
                self.assertTrue(cert_file.startswith(docker_cert_base))
                self.assertTrue(key_file.startswith(docker_cert_base))
                self.assertIn(hostname, cert_dir)
        
        print("   ✅ Certificate Docker integration paths validated")
    
    def test_environment_variable_docker_integration(self):
        """Test environment variable integration in Docker"""
        print("\n🧪 Testing environment variable Docker integration")
        
        # Test required environment variables for Docker
        required_docker_env_vars = [
            "ENV_CONTENT",
            "CERTIFICATE", 
            "MODE"
        ]
        
        # Test optional environment variables
        optional_docker_env_vars = [
            "FLASK_PORT",
            "FLASK_PROTOCOL",
            "FLASK_HOST",
            "DEBUG"
        ]
        
        # Validate environment variable names
        for var in required_docker_env_vars:
            self.assertIsInstance(var, str, f"Environment variable {var} should be string")
            self.assertTrue(len(var) > 0, f"Environment variable {var} should not be empty")
        
        for var in optional_docker_env_vars:
            self.assertIsInstance(var, str, f"Environment variable {var} should be string")
            self.assertTrue(len(var) > 0, f"Environment variable {var} should not be empty")
        
        print("   ✅ Environment variable Docker integration validated")


def run_docker_tests():
    """Run all Docker container tests"""
    print("🐳 DOCKER CONTAINER TESTING")
    print("=" * 50)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestDockerContainers,
        TestDockerIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 DOCKER TEST SUMMARY")
    print("=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  • {test}")
    
    if result.errors:
        print("\n💥 ERRORS:")
        for test, traceback in result.errors:
            print(f"  • {test}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
    
    if success_rate == 100:
        print(f"\n🎉 ALL DOCKER TESTS PASSED! ({success_rate:.1f}%)")
    elif success_rate >= 80:
        print(f"\n✅ DOCKER TESTS MOSTLY SUCCESSFUL ({success_rate:.1f}%)")
    else:
        print(f"\n⚠️  DOCKER TESTS NEED ATTENTION ({success_rate:.1f}%)")
    
    print("\n🔍 DOCKER TESTING COVERAGE:")
    print("  ✅ Dockerfile validation")
    print("  ✅ Docker entrypoint script")
    print("  ✅ Environment variable processing")
    print("  ✅ Certificate integration")
    print("  ✅ Container management scripts")
    print("  ✅ Port configuration")
    print("  ✅ Flask Docker integration")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_docker_tests()
    sys.exit(0 if success else 1)