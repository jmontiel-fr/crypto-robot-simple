#!/usr/bin/env python3
"""
Comprehensive test runner for crypto-robot dockerization
Runs all tests for execution modes, certificate generation, and Docker containers
"""

import os
import sys
import subprocess
import time
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def print_header(title):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"🧪 {title}")
    print("=" * 80)

def print_section(title):
    """Print formatted section"""
    print(f"\n📋 {title}")
    print("-" * 60)

def run_test_module(module_name, description):
    """Run a specific test module"""
    print_section(f"Running {description}")
    
    try:
        # Import and run the test module
        module = __import__(f"tests.{module_name}", fromlist=[module_name])
        
        if hasattr(module, f"run_{module_name.replace('test_', '')}_tests"):
            # Run the module's main test function
            test_function = getattr(module, f"run_{module_name.replace('test_', '')}_tests")
            success = test_function()
            return success
        else:
            # Run as unittest module
            result = subprocess.run([
                sys.executable, "-m", f"tests.{module_name}"
            ], cwd=project_root)
            return result.returncode == 0
            
    except ImportError as e:
        print(f"❌ Could not import test module {module_name}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error running test module {module_name}: {e}")
        return False

def run_comprehensive_tests(test_categories=None, verbose=False):
    """Run comprehensive test suite"""
    
    print_header("CRYPTO-ROBOT DOCKERIZATION COMPREHENSIVE TESTING")
    
    start_time = time.time()
    
    # Define test modules and their descriptions
    test_modules = [
        ("test_execution_modes", "Execution Modes Testing", "execution_modes"),
        ("test_certificate_generation", "Certificate Generation Testing", "certificate"),
        ("test_docker_containers", "Docker Container Testing", "docker")
    ]
    
    # Filter test modules if specific categories requested
    if test_categories:
        test_modules = [
            (module, desc, category) for module, desc, category in test_modules
            if category in test_categories
        ]
    
    results = {}
    total_success = True
    
    # Run each test module
    for module_name, description, category in test_modules:
        print(f"\n🚀 Starting {description}...")
        
        try:
            success = run_test_module(module_name, description)
            results[category] = success
            
            if success:
                print(f"✅ {description} - PASSED")
            else:
                print(f"❌ {description} - FAILED")
                total_success = False
                
        except Exception as e:
            print(f"💥 {description} - ERROR: {e}")
            results[category] = False
            total_success = False
    
    # Print comprehensive summary
    print_header("COMPREHENSIVE TEST RESULTS SUMMARY")
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"⏱️  Total execution time: {duration:.2f} seconds")
    print(f"📊 Test categories run: {len(results)}")
    
    print("\n📋 Results by category:")
    for category, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  • {category.replace('_', ' ').title()}: {status}")
    
    # Overall result
    passed_count = sum(1 for success in results.values() if success)
    total_count = len(results)
    success_rate = (passed_count / total_count * 100) if total_count > 0 else 0
    
    print(f"\n📈 Overall success rate: {success_rate:.1f}% ({passed_count}/{total_count})")
    
    if total_success:
        print("\n🎉 ALL TESTS PASSED! The dockerization implementation is working correctly.")
        print("\n✅ VALIDATION COMPLETE:")
        print("  • Direct local execution workflow preserved")
        print("  • Docker containerization system functional")
        print("  • Certificate generation and selection working")
        print("  • Environment variable processing validated")
        print("  • Three-tier development workflow supported")
        print("  • Container management scripts operational")
    else:
        print(f"\n⚠️  SOME TESTS FAILED. Please review the failures above.")
        print("\n🔧 TROUBLESHOOTING STEPS:")
        print("  1. Check that all required files exist")
        print("  2. Verify Docker is installed and running")
        print("  3. Ensure certificates are generated")
        print("  4. Validate .env file configurations")
        print("  5. Check script permissions and executability")
    
    # Provide next steps
    print(f"\n🚀 NEXT STEPS:")
    if total_success:
        print("  1. Run integration tests with actual Docker builds")
        print("  2. Test GitHub Actions workflows in repository")
        print("  3. Deploy to AWS and validate end-to-end functionality")
        print("  4. Run trading functionality validation tests")
    else:
        print("  1. Fix failing tests before proceeding")
        print("  2. Re-run tests to validate fixes")
        print("  3. Check documentation for troubleshooting guidance")
    
    return total_success

def run_quick_validation():
    """Run quick validation of essential components"""
    print_header("QUICK VALIDATION CHECK")
    
    validation_checks = [
        ("Direct execution files", check_direct_execution_files),
        ("Docker infrastructure", check_docker_infrastructure),
        ("Certificate structure", check_certificate_structure),
        ("Container management", check_container_management),
        ("GitHub Actions workflows", check_github_workflows)
    ]
    
    results = {}
    
    for check_name, check_function in validation_checks:
        print(f"\n🔍 Checking {check_name}...")
        try:
            success = check_function()
            results[check_name] = success
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"   {status}")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            results[check_name] = False
    
    # Summary
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    print(f"\n📊 Quick validation: {passed}/{total} checks passed")
    
    if passed == total:
        print("✅ All essential components are in place!")
    else:
        print("⚠️  Some components are missing or need attention.")
    
    return passed == total

def check_direct_execution_files():
    """Check direct execution files exist"""
    required_files = [
        "robot/main.py",
        "robot/start_https_server.py", 
        "robot/start_fresh_portfolio.py"
    ]
    
    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            print(f"     Missing: {file_path}")
            return False
    
    return True

def check_docker_infrastructure():
    """Check Docker infrastructure files exist"""
    required_files = [
        "docker/Dockerfile",
        "docker/scripts/entrypoint.sh"
    ]
    
    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            print(f"     Missing: {file_path}")
            return False
    
    return True

def check_certificate_structure():
    """Check certificate directory structure"""
    cert_dir = project_root / "certificates"
    if not cert_dir.exists():
        print(f"     Missing: certificates directory")
        return False
    
    return True

def check_container_management():
    """Check container management scripts"""
    required_scripts = [
        "robot/scripts/manage-containers.sh",
        "robot/scripts/start-robot.sh",
        "robot/scripts/create-env.sh"
    ]
    
    for script_path in required_scripts:
        full_path = project_root / script_path
        if not full_path.exists():
            print(f"     Missing: {script_path}")
            return False
    
    return True

def check_github_workflows():
    """Check GitHub Actions workflows"""
    required_workflows = [
        ".github/workflows/build-robot-image.yml",
        ".github/workflows/build-robot-infra.yml",
        ".github/workflows/control-robot-infra.yml",
        ".github/workflows/control-robot-aws.yml"
    ]
    
    for workflow_path in required_workflows:
        full_path = project_root / workflow_path
        if not full_path.exists():
            print(f"     Missing: {workflow_path}")
            return False
    
    return True

def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="Crypto-Robot Dockerization Test Runner")
    parser.add_argument("--categories", nargs="+", 
                       choices=["execution_modes", "certificate", "docker"],
                       help="Specific test categories to run")
    parser.add_argument("--quick", action="store_true",
                       help="Run quick validation check only")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose output")
    
    args = parser.parse_args()
    
    if args.quick:
        success = run_quick_validation()
    else:
        success = run_comprehensive_tests(args.categories, args.verbose)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()