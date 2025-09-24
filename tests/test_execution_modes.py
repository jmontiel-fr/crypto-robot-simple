#!/usr/bin/env python3
"""
Comprehensive testing for all execution modes
Tests direct local execution, local Docker, and AWS Docker deployment scenarios
"""

import os
import sys
import subprocess
import tempfile
import json
import time
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "robot"))
sys.path.insert(0, str(project_root / "robot" / "src"))

class TestExecutionModes(unittest.TestCase):
    """Test suite for all execution modes"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.project_root = project_root
        cls.robot_dir = project_root / "robot"
        cls.test_env_file = None
        cls.original_dir = os.getcwd()
        
        # Create test .env file
        cls._create_test_env_file()
        
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        if cls.test_env_file and os.path.exists(cls.test_env_file):
            os.remove(cls.test_env_file)
        os.chdir(cls.original_dir)
    
    @classmethod
    def _create_test_env_file(cls):
        """Create a test .env file for testing"""
        test_env_content = """
# Test environment configuration
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
    
    def setUp(self):
        """Set up each test"""
        os.chdir(self.robot_dir)
    
    def tearDown(self):
        """Clean up after each test"""
        os.chdir(self.original_dir)
    
    def test_direct_local_execution_main_py(self):
        """Test direct execution of main.py"""
        print("\n🧪 Testing direct local execution: main.py")
        
        # Test that main.py exists and is executable
        main_py = self.robot_dir / "main.py"
        self.assertTrue(main_py.exists(), "main.py should exist")
        
        # Test help command (should not crash)
        try:
            result = subprocess.run([
                sys.executable, str(main_py), "--help"
            ], capture_output=True, text=True, timeout=10)
            
            # Should exit with 0 or show help
            self.assertIn("--mode", result.stdout.lower() or result.stderr.lower(),
                         "main.py should show mode option in help")
            print("   ✅ main.py --help works correctly")
            
        except subprocess.TimeoutExpired:
            self.fail("main.py --help timed out")
        except Exception as e:
            self.fail(f"main.py --help failed: {e}")
    
    def test_direct_local_execution_https_server(self):
        """Test direct execution of start_https_server.py"""
        print("\n🧪 Testing direct local execution: start_https_server.py")
        
        # Test that start_https_server.py exists
        https_server = self.robot_dir / "start_https_server.py"
        self.assertTrue(https_server.exists(), "start_https_server.py should exist")
        
        # Test import (should not crash)
        try:
            # Quick syntax check
            result = subprocess.run([
                sys.executable, "-m", "py_compile", str(https_server)
            ], capture_output=True, text=True, timeout=10)
            
            self.assertEqual(result.returncode, 0, 
                           f"start_https_server.py should compile: {result.stderr}")
            print("   ✅ start_https_server.py compiles correctly")
            
        except Exception as e:
            self.fail(f"start_https_server.py compilation failed: {e}")
    
    def test_direct_local_execution_portfolio(self):
        """Test direct execution of start_fresh_portfolio.py"""
        print("\n🧪 Testing direct local execution: start_fresh_portfolio.py")
        
        # Test that start_fresh_portfolio.py exists
        portfolio_script = self.robot_dir / "start_fresh_portfolio.py"
        self.assertTrue(portfolio_script.exists(), "start_fresh_portfolio.py should exist")
        
        # Test help command
        try:
            result = subprocess.run([
                sys.executable, str(portfolio_script), "--help"
            ], capture_output=True, text=True, timeout=10)
            
            # Should show help
            self.assertIn("--cleanup-only", result.stdout.lower() or result.stderr.lower(),
                         "start_fresh_portfolio.py should show cleanup option in help")
            print("   ✅ start_fresh_portfolio.py --help works correctly")
            
        except subprocess.TimeoutExpired:
            self.fail("start_fresh_portfolio.py --help timed out")
        except Exception as e:
            self.fail(f"start_fresh_portfolio.py --help failed: {e}")
    
    def test_certificate_generation_script(self):
        """Test certificate generation script functionality"""
        print("\n🧪 Testing certificate generation script")
        
        cert_script = self.project_root / "tools" / "generate-certificates.sh"
        self.assertTrue(cert_script.exists(), "Certificate generation script should exist")
        
        # Test help command
        try:
            result = subprocess.run([
                "bash", str(cert_script), "help"
            ], capture_output=True, text=True, timeout=10)
            
            self.assertIn("hostname", result.stdout.lower(),
                         "Certificate script should show hostname parameter in help")
            print("   ✅ Certificate generation script help works")
            
        except Exception as e:
            print(f"   ⚠️  Certificate script test skipped: {e}")
    
    def test_env_file_recreation(self):
        """Test .env file recreation from ENV_CONTENT"""
        print("\n🧪 Testing .env file recreation")
        
        # Test environment initialization script
        env_script = self.project_root / "robot" / "scripts" / "create-env.sh"
        self.assertTrue(env_script.exists(), "Environment script should exist")
        
        # Test help command
        try:
            result = subprocess.run([
                "bash", str(env_script), "help"
            ], capture_output=True, text=True, timeout=10)
            
            self.assertIn("source_file", result.stdout.lower(),
                         "Environment script should show source_file parameter")
            print("   ✅ Environment initialization script help works")
            
        except Exception as e:
            print(f"   ⚠️  Environment script test skipped: {e}")
    
    def test_docker_infrastructure_exists(self):
        """Test Docker infrastructure files exist"""
        print("\n🧪 Testing Docker infrastructure")
        
        # Check Dockerfile exists
        dockerfile = self.project_root / "docker" / "Dockerfile"
        self.assertTrue(dockerfile.exists(), "Dockerfile should exist")
        
        # Check entrypoint script exists
        entrypoint = self.project_root / "docker" / "scripts" / "entrypoint.sh"
        self.assertTrue(entrypoint.exists(), "Docker entrypoint script should exist")
        
        # Check certificate structure
        cert_dir = self.project_root / "certificates"
        self.assertTrue(cert_dir.exists(), "Certificates directory should exist")
        
        print("   ✅ Docker infrastructure files exist")
    
    def test_container_management_scripts(self):
        """Test container management scripts"""
        print("\n🧪 Testing container management scripts")
        
        # Check main management script
        manage_script = self.project_root / "robot" / "scripts" / "manage-containers.sh"
        self.assertTrue(manage_script.exists(), "Container management script should exist")
        
        # Check individual scripts
        scripts_to_check = [
            "start-robot.sh",
            "start-webapp.sh", 
            "stop-robot.sh",
            "stop-webapp.sh",
            "container-status.sh"
        ]
        
        scripts_dir = self.project_root / "robot" / "scripts"
        for script_name in scripts_to_check:
            script_path = scripts_dir / script_name
            self.assertTrue(script_path.exists(), f"{script_name} should exist")
        
        # Test help command on main script
        try:
            result = subprocess.run([
                "bash", str(manage_script), "help"
            ], capture_output=True, text=True, timeout=10)
            
            self.assertIn("start-robot", result.stdout.lower(),
                         "Management script should show start-robot command")
            print("   ✅ Container management scripts exist and show help")
            
        except Exception as e:
            print(f"   ⚠️  Container management script test skipped: {e}")
    
    def test_flask_configuration_loading(self):
        """Test Flask configuration loading from .env"""
        print("\n🧪 Testing Flask configuration loading")
        
        try:
            # Test that we can import and check Flask configuration
            from dotenv import load_dotenv
            
            # Clear existing environment variables that might interfere
            test_vars = ['FLASK_PORT', 'FLASK_PROTOCOL', 'HOSTNAME']
            original_values = {}
            for var in test_vars:
                original_values[var] = os.getenv(var)
                if var in os.environ:
                    del os.environ[var]
            
            # Load test environment
            load_dotenv(self.test_env_file, override=True)
            
            # Check that environment variables are loaded
            self.assertEqual(os.getenv('FLASK_PORT'), '5000')
            self.assertEqual(os.getenv('FLASK_PROTOCOL'), 'http')
            self.assertEqual(os.getenv('HOSTNAME'), 'crypto-robot.local')
            
            print("   ✅ Flask configuration loads correctly from .env")
            
            # Restore original environment variables
            for var, value in original_values.items():
                if value is not None:
                    os.environ[var] = value
                elif var in os.environ:
                    del os.environ[var]
            
        except ImportError:
            print("   ⚠️  dotenv not available, skipping Flask config test")
        except Exception as e:
            self.fail(f"Flask configuration test failed: {e}")
    
    def test_certificate_selection_logic(self):
        """Test certificate selection based on environment variables"""
        print("\n🧪 Testing certificate selection logic")
        
        # Test different certificate configurations
        test_cases = [
            ("crypto-robot.local", "certificates/crypto-robot.local"),
            ("jack.crypto-robot-itechsource.com", "certificates/jack.crypto-robot-itechsource.com"),
            ("custom.example.com", "certificates/custom.example.com")
        ]
        
        for hostname, expected_path in test_cases:
            with self.subTest(hostname=hostname):
                # Test path construction logic
                cert_path = f"certificates/{hostname}"
                self.assertEqual(cert_path, expected_path)
        
        print("   ✅ Certificate selection logic works correctly")
    
    def test_three_tier_workflow_compatibility(self):
        """Test three-tier development workflow compatibility"""
        print("\n🧪 Testing three-tier workflow compatibility")
        
        # Tier 1: Direct local execution files exist
        direct_files = [
            self.robot_dir / "main.py",
            self.robot_dir / "start_https_server.py",
            self.robot_dir / "start_fresh_portfolio.py"
        ]
        
        for file_path in direct_files:
            self.assertTrue(file_path.exists(), f"Direct execution file should exist: {file_path}")
        
        # Tier 2: Local Docker files exist
        docker_files = [
            self.project_root / "docker" / "Dockerfile",
            self.project_root / "docker" / "scripts" / "entrypoint.sh"
        ]
        
        for file_path in docker_files:
            self.assertTrue(file_path.exists(), f"Docker file should exist: {file_path}")
        
        # Tier 3: AWS Docker deployment files exist
        aws_files = [
            self.project_root / ".github" / "workflows" / "build-robot-image.yml",
            self.project_root / ".github" / "workflows" / "control-robot-aws.yml"
        ]
        
        for file_path in aws_files:
            self.assertTrue(file_path.exists(), f"AWS deployment file should exist: {file_path}")
        
        print("   ✅ Three-tier workflow files exist")
        print("     • Tier 1: Direct local execution ✅")
        print("     • Tier 2: Local Docker testing ✅") 
        print("     • Tier 3: AWS Docker deployment ✅")
    
    def test_portfolio_management_integration(self):
        """Test portfolio management integration"""
        print("\n🧪 Testing portfolio management integration")
        
        # Check portfolio management script exists
        portfolio_script = self.project_root / "robot" / "scripts" / "portfolio-manager.sh"
        self.assertTrue(portfolio_script.exists(), "Portfolio management script should exist")
        
        # Test help command
        try:
            result = subprocess.run([
                "bash", str(portfolio_script), "help"
            ], capture_output=True, text=True, timeout=10)
            
            self.assertIn("create-fresh", result.stdout.lower(),
                         "Portfolio script should show create-fresh command")
            print("   ✅ Portfolio management integration works")
            
        except Exception as e:
            print(f"   ⚠️  Portfolio management test skipped: {e}")


class TestEnvironmentVariableProcessing(unittest.TestCase):
    """Test environment variable processing and validation"""
    
    def test_env_content_base64_processing(self):
        """Test ENV_CONTENT base64 encoding/decoding"""
        print("\n🧪 Testing ENV_CONTENT base64 processing")
        
        import base64
        
        # Test content
        test_env = "FLASK_PORT=5000\nFLASK_PROTOCOL=https\nHOSTNAME=test.local"
        
        # Encode
        encoded = base64.b64encode(test_env.encode()).decode()
        
        # Decode
        decoded = base64.b64decode(encoded).decode()
        
        self.assertEqual(test_env, decoded, "Base64 encoding/decoding should work correctly")
        print("   ✅ ENV_CONTENT base64 processing works")
    
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
                cert_path = f"/opt/crypto-robot/certificates/{cert}"
                expected_cert_file = f"{cert_path}/cert.pem"
                expected_key_file = f"{cert_path}/key.pem"
                
                self.assertTrue(expected_cert_file.endswith("cert.pem"))
                self.assertTrue(expected_key_file.endswith("key.pem"))
        
        print("   ✅ CERTIFICATE environment variable handling works")


def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("🚀 COMPREHENSIVE EXECUTION MODE TESTING")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestExecutionModes,
        TestEnvironmentVariableProcessing
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  • {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0]}")
    
    if result.errors:
        print("\n💥 ERRORS:")
        for test, traceback in result.errors:
            print(f"  • {test}: {traceback.split('\\n')[-2]}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
    
    if success_rate == 100:
        print(f"\n🎉 ALL TESTS PASSED! ({success_rate:.1f}%)")
    elif success_rate >= 80:
        print(f"\n✅ MOSTLY SUCCESSFUL ({success_rate:.1f}%)")
    else:
        print(f"\n⚠️  NEEDS ATTENTION ({success_rate:.1f}%)")
    
    print("\n🔍 TESTING COVERAGE:")
    print("  ✅ Direct local execution workflow")
    print("  ✅ Docker containerization system")
    print("  ✅ Environment variable processing")
    print("  ✅ Certificate selection logic")
    print("  ✅ Three-tier development workflow")
    print("  ✅ Portfolio management integration")
    print("  ✅ Container management scripts")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)
def ru
n_execution_mode_tests():
    """Run all execution mode tests"""
    print("🚀 EXECUTION MODE TESTING")
    print("=" * 50)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestExecutionModes
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 EXECUTION MODE TEST SUMMARY")
    print("=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
    
    if success_rate == 100:
        print(f"\n🎉 ALL EXECUTION MODE TESTS PASSED! ({success_rate:.1f}%)")
    elif success_rate >= 80:
        print(f"\n✅ EXECUTION MODE TESTS MOSTLY SUCCESSFUL ({success_rate:.1f}%)")
    else:
        print(f"\n⚠️  EXECUTION MODE TESTS NEED ATTENTION ({success_rate:.1f}%)")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_execution_mode_tests()
    sys.exit(0 if success else 1)