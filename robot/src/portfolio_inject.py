"""
Portfolio Inject Operation
Allows injecting a specified USDC amount into the portfolio by converting USDC to cryptocurrencies
and distributing proportionally across existing portfolio positions.
"""
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class PortfolioInjector:
    def __init__(self, portfolio_manager, binance_client, robot_state_manager):
        """
        Initialize portfolio injector
        
        Args:
            portfolio_manager: PortfolioManager instance
            binance_client: EnhancedBinanceClient instance 
            robot_state_manager: RobotStateManager instance
        """
        self.portfolio_manager = portfolio_manager
        self.binance_client = binance_client
        self.robot_state_manager = robot_state_manager
        
    def get_usdc_balance(self) -> float:
        """Get current USDC balance in Binance account"""
        try:
            account_info = self.binance_client.get_account_info()
            balances = account_info.get('balances', [])
            
            for balance in balances:
                if balance['asset'] == 'USDC':
                    free_balance = float(balance['free'])
                    logger.info(f"USDC balance: {free_balance:.6f}")
                    return free_balance
            
            logger.warning("USDC balance not found in account")
            return 0.0
            
        except Exception as e:
            logger.error(f"Error getting USDC balance: {e}")
            return 0.0
    
    def check_usdc_availability(self, required_amount: float) -> Tuple[bool, str]:
        """
        Check if sufficient USDC is available for injection
        
        Args:
            required_amount: USDC amount needed
            
        Returns:
            Tuple of (is_available, message)
        """
        try:
            available_usdc = self.get_usdc_balance()
            
            if available_usdc >= required_amount:
                return True, f"✅ Sufficient USDC available: {available_usdc:.6f} USDC"
            else:
                shortage = required_amount - available_usdc
                return False, f"❌ Insufficient USDC. Available: {available_usdc:.6f}, Required: {required_amount:.6f}, Shortage: {shortage:.6f}"
                
        except Exception as e:
            error_msg = f"Error checking USDC availability: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_portfolio_proportions(self) -> Dict[str, float]:
        """
        Get current portfolio proportions for each cryptocurrency
        
        Returns:
            Dict of {symbol: proportion} where proportion is 0.0-1.0
        """
        try:
            positions = self.portfolio_manager.positions
            if not positions:
                logger.warning("No positions in portfolio")
                return {}
            
            # Calculate total portfolio value
            total_value = sum(pos.current_value for pos in positions.values())
            
            if total_value <= 0:
                logger.warning("Portfolio has no value")
                return {}
            
            # Calculate proportions
            proportions = {}
            for symbol, position in positions.items():
                proportion = position.current_value / total_value
                proportions[symbol] = proportion
                logger.info(f"{symbol}: {proportion:.2%} of portfolio")
            
            return proportions
            
        except Exception as e:
            logger.error(f"Error calculating portfolio proportions: {e}")
            return {}
    
    def convert_usdc_to_bnb(self, usdc_amount: float, dry_run: bool = False) -> Tuple[bool, float]:
        """
        Convert USDC to BNB for further distribution
        
        Args:
            usdc_amount: Amount of USDC to convert
            dry_run: If True, only simulate the conversion
            
        Returns:
            Tuple of (success, bnb_amount_received)
        """
        try:
            # Check if direct USDC/BNB pair exists
            try:
                usdc_bnb_price = self.binance_client.get_current_price("USDCBNB")
                if usdc_bnb_price > 0:
                    # Direct conversion
                    bnb_amount = usdc_amount * usdc_bnb_price
                    logger.info(f"Direct conversion: {usdc_amount:.6f} USDC → {bnb_amount:.6f} BNB")
                    
                    if dry_run:
                        logger.info(f"[SIMULATED] Converting {usdc_amount:.6f} USDC to {bnb_amount:.6f} BNB")
                        return True, bnb_amount
                    else:
                        # Execute actual order
                        order_result = self.binance_client.place_market_order("USDCBNB", "SELL", usdc_amount)
                        if order_result:
                            actual_bnb = float(order_result.get('cummulativeQuoteQty', bnb_amount))
                            logger.info(f"✅ Converted {usdc_amount:.6f} USDC to {actual_bnb:.6f} BNB")
                            return True, actual_bnb
                        else:
                            logger.error("Failed to execute USDC→BNB order")
                            return False, 0.0
            except Exception as e:
                logger.warning(f"Direct USDC/BNB conversion failed: {e}")
            
            # Fallback: USDC → USDT → BNB
            try:
                usdc_usdt_price = self.binance_client.get_current_price("USDCUSDT")
                bnb_usdt_price = self.binance_client.get_current_price("BNBUSDT")
                
                if usdc_usdt_price > 0 and bnb_usdt_price > 0:
                    usdt_amount = usdc_amount * usdc_usdt_price
                    bnb_amount = usdt_amount / bnb_usdt_price
                    
                    logger.info(f"Two-step conversion: {usdc_amount:.6f} USDC → {usdt_amount:.2f} USDT → {bnb_amount:.6f} BNB")
                    
                    if dry_run:
                        logger.info(f"[SIMULATED] Converting {usdc_amount:.6f} USDC to {bnb_amount:.6f} BNB via USDT")
                        return True, bnb_amount
                    else:
                        # Execute two orders: USDC → USDT, then USDT → BNB
                        # Step 1: USDC → USDT
                        usdc_order = self.binance_client.place_market_order("USDCUSDT", "SELL", usdc_amount)
                        if not usdc_order:
                            logger.error("Failed to execute USDC→USDT order")
                            return False, 0.0
                        
                        actual_usdt = float(usdc_order.get('cummulativeQuoteQty', usdt_amount))
                        
                        # Step 2: USDT → BNB
                        bnb_order = self.binance_client.place_market_order("BNBUSDT", "BUY", actual_usdt)
                        if not bnb_order:
                            logger.error("Failed to execute USDT→BNB order")
                            return False, 0.0
                        
                        actual_bnb = float(bnb_order.get('executedQty', bnb_amount))
                        logger.info(f"✅ Converted {usdc_amount:.6f} USDC to {actual_bnb:.6f} BNB via USDT")
                        return True, actual_bnb
            except Exception as e:
                logger.warning(f"Two-step USDC→USDT→BNB conversion failed: {e}")
            
            logger.error("Could not convert USDC to BNB - no valid trading pairs found")
            return False, 0.0
            
        except Exception as e:
            logger.error(f"Error converting USDC to BNB: {e}")
            return False, 0.0
    
    def calculate_injection_amounts(self, usdc_amount: float) -> Tuple[bool, Dict[str, float], float]:
        """
        Calculate how much of each cryptocurrency to buy for the injection
        
        Args:
            usdc_amount: Amount in USDC to inject
            
        Returns:
            Tuple of (success, {symbol: bnb_amount_to_invest}, total_bnb_available)
        """
        try:
            # Get portfolio proportions
            proportions = self.get_portfolio_proportions()
            if not proportions:
                logger.error("Cannot calculate injection amounts - no portfolio proportions available")
                return False, {}, 0.0
            
            # Convert USDC to BNB equivalent (for calculation purposes)
            usdc_bnb_rate = self.get_usdc_to_bnb_rate()
            if usdc_bnb_rate <= 0:
                return False, {}, 0.0
            
            total_bnb_to_distribute = usdc_amount * usdc_bnb_rate
            logger.info(f"Will distribute {total_bnb_to_distribute:.6f} BNB across portfolio proportionally")
            
            # Calculate BNB amounts for each position
            injection_amounts = {}
            for symbol, proportion in proportions.items():
                bnb_amount = total_bnb_to_distribute * proportion
                injection_amounts[symbol] = bnb_amount
                
                logger.info(f"{symbol}: Add {bnb_amount:.6f} BNB worth (Proportion: {proportion:.2%})")
            
            return True, injection_amounts, total_bnb_to_distribute
            
        except Exception as e:
            logger.error(f"Error calculating injection amounts: {e}")
            return False, {}, 0.0
    
    def get_usdc_to_bnb_rate(self) -> float:
        """Get current USDC to BNB exchange rate"""
        try:
            # Try direct USDC/BNB rate
            try:
                usdc_bnb_price = self.binance_client.get_current_price("USDCBNB")
                if usdc_bnb_price > 0:
                    logger.info(f"USDC to BNB rate: 1 USDC = {usdc_bnb_price:.6f} BNB")
                    return usdc_bnb_price
            except:
                pass
            
            # Fallback: Calculate via USDT
            usdc_usdt_price = self.binance_client.get_current_price("USDCUSDT")
            bnb_usdt_price = self.binance_client.get_current_price("BNBUSDT")
            
            if usdc_usdt_price > 0 and bnb_usdt_price > 0:
                usdc_bnb_rate = usdc_usdt_price / bnb_usdt_price
                logger.info(f"USDC to BNB rate (via USDT): 1 USDC = {usdc_bnb_rate:.6f} BNB")
                return usdc_bnb_rate
            
            logger.error("Could not get USDC to BNB exchange rate")
            return 0.0
            
        except Exception as e:
            logger.error(f"Error getting USDC to BNB rate: {e}")
            return 0.0
    
    def execute_inject(self, usdc_amount: float, dry_run: bool = False) -> Tuple[bool, Dict]:
        """
        Execute the full inject operation
        
        Args:
            usdc_amount: Amount in USDC to inject
            dry_run: If True, only simulate the operation
            
        Returns:
            Tuple of (success, operation_summary)
        """
        operation_summary = {
            'usdc_amount_requested': usdc_amount,
            'timestamp': datetime.now(),
            'dry_run': dry_run,
            'steps_completed': [],
            'errors': [],
            'positions_enhanced': {},
            'bnb_distributed': 0.0,
            'usdc_converted': 0.0,
            'portfolio_preserved': True
        }
        
        try:
            logger.info(f"Starting inject operation: {usdc_amount:.6f} USDC (Dry run: {dry_run})")
            
            # Step 1: Check USDC availability
            is_available, availability_msg = self.check_usdc_availability(usdc_amount)
            if not is_available:
                operation_summary['errors'].append(availability_msg)
                return False, operation_summary
            
            operation_summary['steps_completed'].append("USDC availability confirmed")
            logger.info(availability_msg)
            
            # Step 2: Calculate injection amounts
            success, injection_amounts, total_bnb_to_distribute = self.calculate_injection_amounts(usdc_amount)
            if not success:
                error = "Failed to calculate injection amounts"
                operation_summary['errors'].append(error)
                return False, operation_summary
            
            operation_summary['steps_completed'].append("Injection amounts calculated")
            operation_summary['bnb_to_distribute'] = total_bnb_to_distribute
            
            # Step 3: Freeze robot (if not dry run)
            if not dry_run:
                freeze_success = self.robot_state_manager.freeze_robot(f"Portfolio injection in progress: {usdc_amount:.6f} USDC")
                if not freeze_success:
                    error = "Failed to freeze robot"
                    operation_summary['errors'].append(error)
                    return False, operation_summary
                
                operation_summary['steps_completed'].append("Robot frozen")
            else:
                operation_summary['steps_completed'].append("Robot freeze skipped (dry run)")
            
            # Step 4: Convert USDC to BNB
            bnb_success, bnb_received = self.convert_usdc_to_bnb(usdc_amount, dry_run)
            if not bnb_success:
                error = "Failed to convert USDC to BNB"
                operation_summary['errors'].append(error)
                if not dry_run:
                    self.robot_state_manager.unfreeze_robot()
                return False, operation_summary
            
            operation_summary['steps_completed'].append("USDC converted to BNB")
            operation_summary['bnb_received'] = bnb_received
            operation_summary['usdc_converted'] = usdc_amount
            
            # Step 5: Distribute BNB to crypto positions
            total_bnb_distributed = 0.0
            positions_enhanced = {}
            
            try:
                for symbol, bnb_amount in injection_amounts.items():
                    if bnb_amount <= 0:
                        continue
                    
                    current_price = self.binance_client.get_current_price(f"{symbol}BNB")
                    if current_price <= 0:
                        logger.warning(f"Could not get price for {symbol}, skipping")
                        continue
                    
                    quantity_to_buy = bnb_amount / current_price
                    
                    if not dry_run:
                        # Execute actual buy
                        cost = self.portfolio_manager.execute_trade(symbol, "BUY", quantity_to_buy, current_price)
                        if cost > 0:  # Successful trade
                            total_bnb_distributed += bnb_amount
                            positions_enhanced[symbol] = {
                                'quantity_bought': quantity_to_buy,
                                'price': current_price,
                                'bnb_invested': bnb_amount,
                                'cost': cost
                            }
                            logger.info(f"Bought {quantity_to_buy:.6f} {symbol} with {bnb_amount:.6f} BNB")
                    else:
                        # Simulate buy
                        cost = bnb_amount * 1.001  # Simulate fee
                        total_bnb_distributed += bnb_amount
                        positions_enhanced[symbol] = {
                            'quantity_bought': quantity_to_buy,
                            'price': current_price,
                            'bnb_invested': bnb_amount,
                            'cost': cost
                        }
                        logger.info(f"[SIMULATED] Bought {quantity_to_buy:.6f} {symbol} with {bnb_amount:.6f} BNB")
                
                operation_summary['steps_completed'].append("BNB distributed to positions")
                operation_summary['positions_enhanced'] = positions_enhanced
                operation_summary['bnb_distributed'] = total_bnb_distributed
                
            except Exception as e:
                error = f"Error during position enhancement: {e}"
                operation_summary['errors'].append(error)
                logger.error(error)
            
            # Step 6: Unfreeze robot (if not dry run)
            if not dry_run:
                unfreeze_success = self.robot_state_manager.unfreeze_robot()
                if unfreeze_success:
                    operation_summary['steps_completed'].append("Robot unfrozen")
                else:
                    operation_summary['errors'].append("Failed to unfreeze robot")
            else:
                operation_summary['steps_completed'].append("Robot unfreeze skipped (dry run)")
            
            # Check if operation was successful
            success = len(operation_summary['errors']) == 0 and total_bnb_distributed > 0
            
            logger.info(f"Inject operation completed. Success: {success}")
            logger.info(f"USDC converted: {operation_summary.get('usdc_converted', 0):.6f}")
            logger.info(f"BNB distributed: {total_bnb_distributed:.6f}")
            logger.info(f"Positions enhanced: {len(positions_enhanced)}")
            
            return success, operation_summary
            
        except Exception as e:
            error = f"Unexpected error during inject operation: {e}"
            operation_summary['errors'].append(error)
            logger.error(error)
            
            # Try to unfreeze robot if it was frozen
            if not dry_run:
                try:
                    self.robot_state_manager.unfreeze_robot()
                except:
                    pass
            
            return False, operation_summary