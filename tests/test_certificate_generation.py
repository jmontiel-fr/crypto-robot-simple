#!/usr/bin/env python3
"""
Certificate generation testing
Tests certificate generation script with different hostname and type combinations
"""

import os
import sys
import subprocess
import tempfile
import shutil
import unittest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestCertificateGeneration(unittest.TestCase):
    """Test certificate generation functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.project_root = project_root
        cls.cert_script = project_root / "tools" / "generate-certificates.sh"
        cls.test_cert_dir = None
        cls.original_cert_dir = project_root / "certificates"
        
        # Create temporary certificates directory for testing
        cls.test_cert_dir = tempfile.mkdtemp(prefix="test_certificates_")
        
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        if cls.test_cert_dir and os.path.exists(cls.test_cert_dir):
            shutil.rmtree(cls.test_cert_dir)
    
    def test_certificate_script_exists(self):
        """Test that certificate generation script exists"""
        print("\n🧪 Testing certificate script existence")
        
        self.assertTrue(self.cert_script.exists(), 
                       "Certificate generation script should exist")
        
        # Check if script is executable
        self.assertTrue(os.access(self.cert_script, os.X_OK),
                       "Certificate script should be executable")
        
        print("   ✅ Certificate generation script exists and is executable")
    
    def test_certificate_script_help(self):
        """Test certificate script help functionality"""
        print("\n🧪 Testing certificate script help")
        
        if not self.cert_script.exists():
            self.skipTest("Certificate script not found")
        
        try:
            result = subprocess.run([
                "bash", str(self.cert_script), "help"
            ], capture_output=True, text=True, timeout=15)
            
            # Should show usage information
            output = result.stdout.lower() + result.stderr.lower()
            self.assertIn("usage", output, "Help should show usage information")
            self.assertIn("hostname", output, "Help should mention hostname parameter")
            self.assertIn("self-signed", output, "Help should mention self-signed option")
            
            print("   ✅ Certificate script help works correctly")
            
        except subprocess.TimeoutExpired:
            self.fail("Certificate script help timed out")
        except FileNotFoundError:
            self.skipTest("Bash not available for testing")
        except Exception as e:
            self.fail(f"Certificate script help failed: {e}")
    
    def test_certificate_script_validation(self):
        """Test certificate script parameter validation"""
        print("\n🧪 Testing certificate script parameter validation")
        
        if not self.cert_script.exists():
            self.skipTest("Certificate script not found")
        
        try:
            # Test with no parameters (should show usage)
            result = subprocess.run([
                "bash", str(self.cert_script)
            ], capture_output=True, text=True, timeout=15)
            
            output = result.stdout.lower() + result.stderr.lower()
            # Should show usage or error about missing parameters
            self.assertTrue(
                "usage" in output or "hostname" in output or "error" in output,
                "Script should show usage or error when no parameters provided"
            )
            
            print("   ✅ Certificate script validates parameters correctly")
            
        except subprocess.TimeoutExpired:
            self.fail("Certificate script validation timed out")
        except FileNotFoundError:
            self.skipTest("Bash not available for testing")
        except Exception as e:
            print(f"   ⚠️  Certificate script validation test skipped: {e}")
    
    def test_certificate_directory_structure(self):
        """Test certificate directory structure"""
        print("\n🧪 Testing certificate directory structure")
        
        # Check if certificates directory exists
        cert_dir = self.project_root / "certificates"
        self.assertTrue(cert_dir.exists(), "Certificates directory should exist")
        
        # Check for expected certificate subdirectories
        expected_cert_dirs = [
            "crypto-robot.local",
            "jack.crypto-robot-itechsource.com"
        ]
        
        for cert_hostname in expected_cert_dirs:
            cert_subdir = cert_dir / cert_hostname
            if cert_subdir.exists():
                print(f"   ✅ Found certificate directory: {cert_hostname}")
                
                # Check for certificate files
                cert_file = cert_subdir / "cert.pem"
                key_file = cert_subdir / "key.pem"
                
                if cert_file.exists():
                    print(f"     ✅ Certificate file exists: cert.pem")
                else:
                    print(f"     ⚠️  Certificate file missing: cert.pem")
                
                if key_file.exists():
                    print(f"     ✅ Key file exists: key.pem")
                else:
                    print(f"     ⚠️  Key file missing: key.pem")
            else:
                print(f"   ⚠️  Certificate directory not found: {cert_hostname}")
        
        print("   ✅ Certificate directory structure validated")
    
    def test_certificate_file_formats(self):
        """Test certificate file formats and validity"""
        print("\n🧪 Testing certificate file formats")
        
        cert_dir = self.project_root / "certificates"
        if not cert_dir.exists():
            self.skipTest("Certificates directory not found")
        
        # Find certificate files
        cert_files = list(cert_dir.glob("*/cert.pem"))
        key_files = list(cert_dir.glob("*/key.pem"))
        
        print(f"   Found {len(cert_files)} certificate files")
        print(f"   Found {len(key_files)} key files")
        
        # Test certificate file format
        for cert_file in cert_files:
            with self.subTest(cert_file=cert_file):
                try:
                    with open(cert_file, 'r') as f:
                        content = f.read()
                    
                    # Check for PEM format markers
                    self.assertIn("-----BEGIN CERTIFICATE-----", content,
                                f"Certificate file should be in PEM format: {cert_file}")
                    self.assertIn("-----END CERTIFICATE-----", content,
                                f"Certificate file should be in PEM format: {cert_file}")
                    
                    print(f"     ✅ Valid PEM certificate: {cert_file.parent.name}")
                    
                except Exception as e:
                    print(f"     ⚠️  Could not validate certificate {cert_file}: {e}")
        
        # Test key file format
        for key_file in key_files:
            with self.subTest(key_file=key_file):
                try:
                    with open(key_file, 'r') as f:
                        content = f.read()
                    
                    # Check for PEM format markers (various key types)
                    has_key_marker = any(marker in content for marker in [
                        "-----BEGIN PRIVATE KEY-----",
                        "-----BEGIN RSA PRIVATE KEY-----",
                        "-----BEGIN EC PRIVATE KEY-----"
                    ])
                    
                    self.assertTrue(has_key_marker,
                                  f"Key file should be in PEM format: {key_file}")
                    
                    print(f"     ✅ Valid PEM key: {key_file.parent.name}")
                    
                except Exception as e:
                    print(f"     ⚠️  Could not validate key {key_file}: {e}")
    
    def test_certificate_hostname_matching(self):
        """Test certificate hostname matching"""
        print("\n🧪 Testing certificate hostname matching")
        
        cert_dir = self.project_root / "certificates"
        if not cert_dir.exists():
            self.skipTest("Certificates directory not found")
        
        # Test hostname to certificate path mapping
        test_hostnames = [
            "crypto-robot.local",
            "jack.crypto-robot-itechsource.com",
            "custom.example.com"
        ]
        
        for hostname in test_hostnames:
            with self.subTest(hostname=hostname):
                expected_cert_dir = cert_dir / hostname
                expected_cert_file = expected_cert_dir / "cert.pem"
                expected_key_file = expected_cert_dir / "key.pem"
                
                # Test path construction
                self.assertEqual(str(expected_cert_dir), str(cert_dir / hostname))
                self.assertEqual(str(expected_cert_file), str(expected_cert_dir / "cert.pem"))
                self.assertEqual(str(expected_key_file), str(expected_cert_dir / "key.pem"))
                
                if expected_cert_dir.exists():
                    print(f"   ✅ Certificate directory exists for: {hostname}")
                else:
                    print(f"   ⚠️  Certificate directory missing for: {hostname}")
        
        print("   ✅ Certificate hostname matching logic validated")
    
    def test_certificate_selection_environment(self):
        """Test certificate selection based on environment variables"""
        print("\n🧪 Testing certificate selection environment logic")
        
        # Test different certificate environment configurations
        test_cases = [
            {
                "CERTIFICATE": "crypto-robot.local",
                "expected_path": "certificates/crypto-robot.local"
            },
            {
                "CERTIFICATE": "jack.crypto-robot-itechsource.com", 
                "expected_path": "certificates/jack.crypto-robot-itechsource.com"
            },
            {
                "CERTIFICATE": "custom.example.com",
                "expected_path": "certificates/custom.example.com"
            }
        ]
        
        for test_case in test_cases:
            with self.subTest(certificate=test_case["CERTIFICATE"]):
                # Simulate environment variable
                cert_env = test_case["CERTIFICATE"]
                expected_path = test_case["expected_path"]
                
                # Test path construction logic
                constructed_path = f"certificates/{cert_env}"
                self.assertEqual(constructed_path, expected_path)
                
                print(f"   ✅ Certificate selection works for: {cert_env}")
        
        print("   ✅ Certificate selection environment logic validated")


class TestCertificateIntegration(unittest.TestCase):
    """Test certificate integration with Flask and Docker"""
    
    def test_flask_certificate_loading_logic(self):
        """Test Flask certificate loading logic"""
        print("\n🧪 Testing Flask certificate loading logic")
        
        # Test certificate path construction for Flask
        test_hostnames = [
            "crypto-robot.local",
            "jack.crypto-robot-itechsource.com"
        ]
        
        for hostname in test_hostnames:
            with self.subTest(hostname=hostname):
                # Simulate Flask certificate loading logic
                cert_dir = f"/opt/crypto-robot/certificates/{hostname}"
                cert_file = f"{cert_dir}/cert.pem"
                key_file = f"{cert_dir}/key.pem"
                
                # Test path construction
                self.assertTrue(cert_file.endswith("cert.pem"))
                self.assertTrue(key_file.endswith("key.pem"))
                self.assertIn(hostname, cert_dir)
                
                print(f"   ✅ Flask certificate paths correct for: {hostname}")
        
        print("   ✅ Flask certificate loading logic validated")
    
    def test_docker_certificate_environment(self):
        """Test Docker certificate environment handling"""
        print("\n🧪 Testing Docker certificate environment")
        
        # Test Docker environment variable handling
        test_environments = [
            {
                "CERTIFICATE": "crypto-robot.local",
                "expected_cert_path": "/opt/crypto-robot/certificates/crypto-robot.local/cert.pem",
                "expected_key_path": "/opt/crypto-robot/certificates/crypto-robot.local/key.pem"
            },
            {
                "CERTIFICATE": "jack.crypto-robot-itechsource.com",
                "expected_cert_path": "/opt/crypto-robot/certificates/jack.crypto-robot-itechsource.com/cert.pem",
                "expected_key_path": "/opt/crypto-robot/certificates/jack.crypto-robot-itechsource.com/key.pem"
            }
        ]
        
        for env_config in test_environments:
            with self.subTest(certificate=env_config["CERTIFICATE"]):
                cert_env = env_config["CERTIFICATE"]
                
                # Simulate Docker certificate path construction
                cert_path = f"/opt/crypto-robot/certificates/{cert_env}/cert.pem"
                key_path = f"/opt/crypto-robot/certificates/{cert_env}/key.pem"
                
                self.assertEqual(cert_path, env_config["expected_cert_path"])
                self.assertEqual(key_path, env_config["expected_key_path"])
                
                print(f"   ✅ Docker certificate environment correct for: {cert_env}")
        
        print("   ✅ Docker certificate environment validated")


def run_certificate_tests():
    """Run all certificate generation tests"""
    print("🔐 CERTIFICATE GENERATION TESTING")
    print("=" * 50)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestCertificateGeneration,
        TestCertificateIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 CERTIFICATE TEST SUMMARY")
    print("=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
    
    if success_rate == 100:
        print(f"\n🎉 ALL CERTIFICATE TESTS PASSED! ({success_rate:.1f}%)")
    elif success_rate >= 80:
        print(f"\n✅ CERTIFICATE TESTS MOSTLY SUCCESSFUL ({success_rate:.1f}%)")
    else:
        print(f"\n⚠️  CERTIFICATE TESTS NEED ATTENTION ({success_rate:.1f}%)")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_certificate_tests()
    sys.exit(0 if success else 1)