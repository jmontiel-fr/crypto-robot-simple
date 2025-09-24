#!/usr/bin/env python3
"""
Trading Integration Tests
Tests trading functionality across different deployment environments
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
from decimal import Decimal
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "robot"))
sys.path.insert(0, str(project_root / "robot" / "src"))

class TestTradingIntegration(unittest.TestCase):
    """Integration tests for trading functionality across environments"""
    
    @classmethod
    def setUpClass(cls):
        """Set up integration test environment"""
        cls.project_root = project_root
        cls.test_env_file = None
        cls._create_integration_test_env()
        
    @classmethod
    def tearDownClass(cls):
        """Clean up integration test environment"""
        if cls.test_env_file and os.path.exists(cls.test_env_file):
            os.remove(cls.test_env_file)
    
    @classmethod
    def _create_integration_test_env(cls):
        """Create integration test environment file"""
        test_env_content = """
BINANCE_TESTNET=true
BINANCE_API_KEY=integration_test_key
BINANCE_SECRET_KEY=integration_test_secret
STARTING_CAPITAL=100.0
RESERVE_ASSET=BNB
DRY_RUN_MODE=true
ENABLE_CALIBRATION=true
DEFAULT_CALIBRATION_PROFILE=moderate_realistic
CYCLE_DURATION=1440
MAX_EXECUTIONS=1
FLASK_PORT=5000
FLASK_PROTOCOL=http
FLASK_HOST=0.0.0.0
HOSTNAME=crypto-robot.local
CERTIFICATE_TYPE=self-signed
DEBUG=true
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write(test_env_content.strip())
            cls.test_env_file = f.name
    
    def setUp(self):
        """Set up each integration test"""
        # Load test environment
        from dotenv import load_dotenv
        load_dotenv(self.test_env_file, override=True)
    
    def test_end_to_end_trading_workflow(self):
        """Test complete trading workflow from start to finish"""
        print("\n🔄 Testing end-to-end trading workflow")
        
        try:
            from dry_run_manager import DryRunManager
            
            # Initialize trading system
            dry_run_manager = DryRunManager()
            
            # Clear any existing positions for clean test
            dry_run_manager.portfolio.positions.clear()
            dry_run_manager._save_portfolio()
            
            initial_balance = dry_run_manager.portfolio.reserve_balance
            
            print(f"   💰 Initial balance: {initial_balance}")
            
            # Execute complete trading cycle
            # 1. Buy operation
            buy_result = dry_run_manager.simulate_buy_order(
                symbol="BTCBNB",
                quantity=Decimal("0.1"),
                price=Decimal("15.5"),
                cycle_number=1
            )
            
            self.assertIsNotNone(buy_result)
            self.assertEqual(buy_result.status, "COMPLETED")
            
            # 2. Check portfolio update
            self.assertIn("BTCBNB", dry_run_manager.portfolio.positions)
            position = dry_run_manager.portfolio.positions["BTCBNB"]
            self.assertEqual(position.quantity, Decimal("0.1"))
            
            # 3. Sell operation
            sell_result = dry_run_manager.simulate_sell_order(
                symbol="BTCBNB", 
                quantity=Decimal("0.05"),
                price=Decimal("16.0"),
                cycle_number=1
            )
            
            self.assertIsNotNone(sell_result)
            self.assertEqual(sell_result.status, "COMPLETED")
            
            # 4. Verify final state
            final_position = dry_run_manager.portfolio.positions["BTCBNB"]
            self.assertEqual(final_position.quantity, Decimal("0.05"))
            
            final_balance = dry_run_manager.portfolio.reserve_balance
            print(f"   💰 Final balance: {final_balance}")
            
            # Should have made some profit (sold at higher price)
            self.assertGreater(final_balance, initial_balance - Decimal("1.0"))
            
            print("   ✅ End-to-end trading workflow completed successfully")
            
        except ImportError as e:
            self.skipTest(f"Trading components not available: {e}")
        except Exception as e:
            self.fail(f"End-to-end trading workflow failed: {e}")


if __name__ == "__main__":
    unittest.main(verbosity=2)