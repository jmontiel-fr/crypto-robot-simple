"""
Balance Validator for Real Trading Robot

This module validates that the Binance account has sufficient reserve asset
before starting the trading robot. This check is only for real trading,
not for simulations.
"""

import logging
import os
from typing import Tuple, Dict, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class BalanceValidator:
    """
    Validates Binance account balance before starting the robot
    """
    
    def __init__(self, binance_client=None):
        self.binance_client = binance_client
        load_dotenv()
        
        # Get configuration from .env
        self.reserve_asset = os.getenv('RESERVE_ASSET', 'BNB')
        self.min_balance_required = float(os.getenv('MIN_BALANCE_REQUIRED', 10.0))
        self.min_reserve_limit = float(os.getenv('MIN_RESERVE_LIMIT', 5.0))
        
        logger.info(f"Balance validator initialized: {self.reserve_asset} asset, "
                   f"min balance required: {self.min_balance_required}, "
                   f"min limit: {self.min_reserve_limit}")
    
    def get_account_balance(self) -> Tuple[bool, Dict[str, float], str]:
        """
        Get current account balance from Binance
        Returns: (success, balances_dict, error_message)
        """
        if not self.binance_client:
            return False, {}, "No Binance client provided"
        
        try:
            # Get account information
            account_info = self.binance_client.get_account()
            
            if not account_info:
                return False, {}, "Failed to get account information from Binance"
            
            # Extract balances
            balances = {}
            total_balance_usdt = 0.0
            
            for balance in account_info.get('balances', []):
                asset = balance['asset']
                free_balance = float(balance['free'])
                locked_balance = float(balance['locked'])
                total_balance = free_balance + locked_balance
                
                if total_balance > 0:
                    balances[asset] = {
                        'free': free_balance,
                        'locked': locked_balance,
                        'total': total_balance
                    }
                    
                    # Estimate USDT value for reporting
                    if asset == 'USDT':
                        total_balance_usdt += total_balance
                    elif asset == 'BNB':
                        # Rough estimate: 1 BNB ≈ 300 USDT (this should be updated with real prices)
                        total_balance_usdt += total_balance * 300
                    elif asset == 'BTC':
                        # Rough estimate: 1 BTC ≈ 45000 USDT
                        total_balance_usdt += total_balance * 45000
                    elif asset == 'ETH':
                        # Rough estimate: 1 ETH ≈ 2500 USDT
                        total_balance_usdt += total_balance * 2500
            
            logger.info(f"Account balance retrieved: {len(balances)} assets, "
                       f"estimated total: {total_balance_usdt:.2f} USDT")
            
            return True, balances, ""
            
        except Exception as e:
            error_msg = f"Error getting account balance: {str(e)}"
            logger.error(error_msg)
            return False, {}, error_msg
    
    def validate_reserve_asset_balance(self) -> Tuple[bool, str, Dict]:
        """
        Validate that the account has sufficient reserve asset balance
        Returns: (is_valid, message, balance_info)
        """
        logger.info(f"Validating {self.reserve_asset} balance for robot startup")
        
        # Get account balance
        success, balances, error_msg = self.get_account_balance()
        
        if not success:
            return False, f"Cannot validate balance: {error_msg}", {}
        
        # Check if reserve asset exists in account
        if self.reserve_asset not in balances:
            available_assets = list(balances.keys())
            return False, (
                f"❌ INSUFFICIENT FUNDS: No {self.reserve_asset} found in account.\n"
                f"Required: {self.min_balance_required} {self.reserve_asset}\n"
                f"Available assets: {', '.join(available_assets) if available_assets else 'None'}\n"
                f"Please deposit {self.reserve_asset} to your Binance account before starting the robot."
            ), balances
        
        # Get reserve asset balance
        reserve_balance = balances[self.reserve_asset]
        available_balance = reserve_balance['free']  # Only free balance can be used
        total_balance = reserve_balance['total']
        
        # Check if sufficient balance
        if available_balance < self.min_balance_required:
            return False, (
                f"❌ INSUFFICIENT FUNDS: Not enough {self.reserve_asset} in account.\n"
                f"Required: {self.min_balance_required} {self.reserve_asset}\n"
                f"Available (free): {available_balance:.6f} {self.reserve_asset}\n"
                f"Total (free + locked): {total_balance:.6f} {self.reserve_asset}\n"
                f"Shortfall: {self.min_balance_required - available_balance:.6f} {self.reserve_asset}\n"
                f"Please deposit more {self.reserve_asset} or reduce MIN_BALANCE_REQUIRED in .env"
            ), balances
        
        # Check if balance is close to minimum (warning)
        warning_threshold = self.min_balance_required * 1.2  # 20% buffer
        if available_balance < warning_threshold:
            message = (
                f"⚠️  LOW BALANCE WARNING: {self.reserve_asset} balance is close to minimum.\n"
                f"Available: {available_balance:.6f} {self.reserve_asset}\n"
                f"Required: {self.min_balance_required} {self.reserve_asset}\n"
                f"Recommended: {warning_threshold:.6f} {self.reserve_asset} (20% buffer)\n"
                f"✅ Robot can start, but consider adding more funds for safety."
            )
        else:
            message = (
                f"✅ SUFFICIENT FUNDS: {self.reserve_asset} balance is adequate.\n"
                f"Available: {available_balance:.6f} {self.reserve_asset}\n"
                f"Required: {self.min_balance_required} {self.reserve_asset}\n"
                f"Buffer: {available_balance - self.min_balance_required:.6f} {self.reserve_asset}\n"
                f"Robot is ready to start!"
            )
        
        logger.info(f"Balance validation successful: {available_balance:.6f} {self.reserve_asset} available")
        
        return True, message, balances
    
    def get_balance_summary(self) -> Dict:
        """
        Get a summary of account balances for display
        """
        success, balances, error_msg = self.get_account_balance()
        
        if not success:
            return {
                'success': False,
                'error': error_msg,
                'balances': {},
                'reserve_asset': self.reserve_asset,
                'required_amount': self.min_balance_required
            }
        
        # Calculate totals and filter significant balances
        significant_balances = {}
        total_estimated_usdt = 0.0
        
        # Price estimates for major assets (should be updated with real API calls)
        price_estimates = {
            'BTC': 45000,
            'ETH': 2500,
            'BNB': 300,
            'ADA': 0.5,
            'SOL': 100,
            'DOT': 7,
            'MATIC': 0.8,
            'AVAX': 35,
            'LINK': 15,
            'UNI': 8,
            'USDT': 1,
            'USDC': 1,
            'BUSD': 1
        }
        
        for asset, balance_info in balances.items():
            total_balance = balance_info['total']
            
            # Only include balances > $1 equivalent
            estimated_price = price_estimates.get(asset, 1.0)
            estimated_value = total_balance * estimated_price
            
            if estimated_value > 1.0:  # > $1
                significant_balances[asset] = {
                    **balance_info,
                    'estimated_price': estimated_price,
                    'estimated_value_usdt': estimated_value
                }
                total_estimated_usdt += estimated_value
        
        # Check reserve asset status
        reserve_status = "not_found"
        reserve_balance = 0.0
        
        if self.reserve_asset in balances:
            reserve_balance = balances[self.reserve_asset]['free']
            if reserve_balance >= self.min_balance_required:
                reserve_status = "sufficient"
            elif reserve_balance >= self.min_reserve_limit:
                reserve_status = "low"
            else:
                reserve_status = "insufficient"
        
        return {
            'success': True,
            'balances': significant_balances,
            'total_estimated_usdt': total_estimated_usdt,
            'reserve_asset': self.reserve_asset,
            'reserve_balance': reserve_balance,
            'required_amount': self.min_balance_required,
            'min_amount': self.min_reserve_limit,
            'reserve_status': reserve_status,
            'can_start_robot': reserve_status in ['sufficient', 'low']
        }

def validate_robot_startup_balance(binance_client) -> Tuple[bool, str]:
    """
    Convenience function to validate balance before robot startup
    Returns: (can_start, message)
    """
    validator = BalanceValidator(binance_client)
    is_valid, message, _ = validator.validate_reserve_asset_balance()
    return is_valid, message

# Example usage and testing
if __name__ == "__main__":
    import logging
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Balance Validator")
    print("=" * 40)
    
    # Test without Binance client (will fail gracefully)
    validator = BalanceValidator()
    
    print(f"Reserve asset: {validator.reserve_asset}")
    print(f"Required amount: {validator.min_balance_required}")
    print(f"Minimum amount: {validator.min_reserve_limit}")
    
    # Test balance validation (will fail without real client)
    is_valid, message, balances = validator.validate_reserve_asset_balance()
    
    print(f"\nValidation result: {'✅ Valid' if is_valid else '❌ Invalid'}")
    print(f"Message: {message}")
    
    # Test balance summary
    summary = validator.get_balance_summary()
    print(f"\nBalance summary: {summary}")
    
    print(f"\n💡 To use with real Binance client:")
    print(f"   from binance.client import Client")
    print(f"   client = Client(api_key, api_secret)")
    print(f"   validator = BalanceValidator(client)")
    print(f"   can_start, msg = validate_robot_startup_balance(client)")