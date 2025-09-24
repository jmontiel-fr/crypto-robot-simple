"""
Portfolio Extract Operation
Allows extracting a specified EUR value from the portfolio by selling proportional amounts
of each cryptocurrency and converting to USDC while preserving the BNB reserve.
"""
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class PortfolioExtractor:
    def __init__(self, portfolio_manager, binance_client, robot_state_manager):
        """
        Initialize portfolio extractor
        
        Args:
            portfolio_manager: PortfolioManager instance
            binance_client: EnhancedBinanceClient instance 
            robot_state_manager: RobotStateManager instance
        """
        self.portfolio_manager = portfolio_manager
        self.binance_client = binance_client
        self.robot_state_manager = robot_state_manager
        
    def get_eur_to_bnb_rate(self) -> float:
        """Get current EUR to BNB exchange rate"""
        try:
            # Get EUR/USDT and BNB/USDT rates to calculate EUR/BNB
            eur_usdt_price = self.binance_client.get_current_price("EURUSDT")
            bnb_usdt_price = self.binance_client.get_current_price("BNBUSDT")
            
            if eur_usdt_price > 0 and bnb_usdt_price > 0:
                eur_bnb_rate = eur_usdt_price / bnb_usdt_price
                logger.info(f"EUR to BNB rate: 1 EUR = {eur_bnb_rate:.6f} BNB")
                return eur_bnb_rate
            else:
                logger.error("Could not get EUR/BNB exchange rate")
                return 0.0
                
        except Exception as e:
            logger.error(f"Error getting EUR to BNB rate: {e}")
            return 0.0
    
    def check_usdc_availability(self) -> bool:
        """Check if USDC is available for trading"""
        try:
            # Check if USDC/BNB pair exists
            usdc_bnb_price = self.binance_client.get_current_price("USDCBNB")
            if usdc_bnb_price > 0:
                logger.info("USDC/BNB pair available")
                return True
            
            # Check if USDC/USDT pair exists (fallback)
            usdc_usdt_price = self.binance_client.get_current_price("USDCUSDT")
            if usdc_usdt_price > 0:
                logger.info("USDC/USDT pair available (will convert via USDT)")
                return True
                
            logger.warning("USDC trading pairs not found")
            return False
            
        except Exception as e:
            logger.error(f"Error checking USDC availability: {e}")
            return False
    
    def calculate_extract_amounts(self, eur_amount: float) -> Tuple[bool, Dict[str, float], float]:
        """
        Calculate how much of each cryptocurrency to sell for the extraction
        
        Args:
            eur_amount: Amount in EUR to extract
            
        Returns:
            Tuple of (success, {symbol: quantity_to_sell}, total_bnb_needed)
        """
        try:
            # Convert EUR to BNB equivalent
            eur_bnb_rate = self.get_eur_to_bnb_rate()
            if eur_bnb_rate <= 0:
                return False, {}, 0.0
            
            total_bnb_needed = eur_amount * eur_bnb_rate
            logger.info(f"Need to extract {total_bnb_needed:.6f} BNB (€{eur_amount})")
            
            # Get current portfolio positions
            positions = self.portfolio_manager.positions
            if not positions:
                logger.error("No positions in portfolio to extract from")
                return False, {}, 0.0
            
            # Calculate total portfolio value
            total_portfolio_value = self.portfolio_manager.get_portfolio_value()
            if total_portfolio_value <= 0:
                logger.error("Portfolio has no value")
                return False, {}, 0.0
            
            # Check if we have enough value to extract
            if total_bnb_needed > total_portfolio_value:
                logger.error(f"Insufficient portfolio value. Need: {total_bnb_needed:.6f}, Available: {total_portfolio_value:.6f}")
                return False, {}, 0.0
            
            # Calculate proportional amounts to sell from each position
            extract_amounts = {}
            for symbol, position in positions.items():
                # Calculate this position's share of the total portfolio
                position_weight = position.current_value / total_portfolio_value
                
                # Calculate BNB amount to extract from this position
                bnb_to_extract = total_bnb_needed * position_weight
                
                # Get current price
                current_price = self.binance_client.get_current_price(f"{symbol}BNB")
                if current_price <= 0:
                    logger.warning(f"Could not get price for {symbol}, skipping")
                    continue
                
                # Calculate quantity to sell
                quantity_to_sell = bnb_to_extract / current_price
                
                # Make sure we don't sell more than we have
                if quantity_to_sell > position.quantity:
                    quantity_to_sell = position.quantity
                
                extract_amounts[symbol] = quantity_to_sell
                
                logger.info(f"{symbol}: Sell {quantity_to_sell:.6f} (Weight: {position_weight:.2%}, Value: {bnb_to_extract:.6f} BNB)")
            
            return True, extract_amounts, total_bnb_needed
            
        except Exception as e:
            logger.error(f"Error calculating extract amounts: {e}")
            return False, {}, 0.0
    
    def convert_bnb_to_usdc(self, bnb_amount: float, dry_run: bool = False) -> Tuple[bool, float]:
        """
        Convert BNB to USDC
        
        Args:
            bnb_amount: Amount of BNB to convert
            dry_run: If True, only simulate the conversion
            
        Returns:
            Tuple of (success, usdc_amount_received)
        """
        try:
            # Check if direct USDC/BNB pair exists
            try:
                usdc_bnb_price = self.binance_client.get_current_price("USDCBNB")
                if usdc_bnb_price > 0:
                    # Direct conversion
                    usdc_amount = bnb_amount / usdc_bnb_price
                    logger.info(f"Direct conversion: {bnb_amount:.6f} BNB → {usdc_amount:.6f} USDC")
                    
                    if dry_run:
                        logger.info(f"[SIMULATED] Converting {bnb_amount:.6f} BNB to {usdc_amount:.6f} USDC")
                        return True, usdc_amount
                    else:
                        # Execute actual order
                        order_result = self.binance_client.place_market_order("USDCBNB", "BUY", bnb_amount)
                        if order_result:
                            actual_usdc = float(order_result.get('executedQty', usdc_amount))
                            logger.info(f"✅ Converted {bnb_amount:.6f} BNB to {actual_usdc:.6f} USDC")
                            return True, actual_usdc
                        else:
                            logger.error("Failed to execute BNB→USDC order")
                            return False, 0.0
            except Exception as e:
                logger.warning(f"Direct USDC/BNB conversion failed: {e}")
            
            # Fallback: BNB → USDT → USDC
            try:
                bnb_usdt_price = self.binance_client.get_current_price("BNBUSDT")
                usdc_usdt_price = self.binance_client.get_current_price("USDCUSDT")
                
                if bnb_usdt_price > 0 and usdc_usdt_price > 0:
                    usdt_amount = bnb_amount * bnb_usdt_price
                    usdc_amount = usdt_amount / usdc_usdt_price
                    
                    logger.info(f"Two-step conversion: {bnb_amount:.6f} BNB → {usdt_amount:.2f} USDT → {usdc_amount:.6f} USDC")
                    
                    if dry_run:
                        logger.info(f"[SIMULATED] Converting {bnb_amount:.6f} BNB to {usdc_amount:.6f} USDC via USDT")
                        return True, usdc_amount
                    else:
                        # Execute two orders: BNB → USDT, then USDT → USDC
                        # Step 1: BNB → USDT
                        bnb_order = self.binance_client.place_market_order("BNBUSDT", "SELL", bnb_amount)
                        if not bnb_order:
                            logger.error("Failed to execute BNB→USDT order")
                            return False, 0.0
                        
                        actual_usdt = float(bnb_order.get('cummulativeQuoteQty', usdt_amount))
                        
                        # Step 2: USDT → USDC
                        usdc_order = self.binance_client.place_market_order("USDCUSDT", "BUY", actual_usdt)
                        if not usdc_order:
                            logger.error("Failed to execute USDT→USDC order")
                            return False, 0.0
                        
                        actual_usdc = float(usdc_order.get('executedQty', usdc_amount))
                        logger.info(f"✅ Converted {bnb_amount:.6f} BNB to {actual_usdc:.6f} USDC via USDT")
                        return True, actual_usdc
            except Exception as e:
                logger.warning(f"Two-step BNB→USDT→USDC conversion failed: {e}")
            
            logger.error("Could not convert BNB to USDC - no valid trading pairs found")
            return False, 0.0
            
        except Exception as e:
            logger.error(f"Error converting BNB to USDC: {e}")
            return False, 0.0
    
    def execute_extract(self, eur_amount: float, dry_run: bool = False) -> Tuple[bool, Dict]:
        """
        Execute the full extract operation
        
        Args:
            eur_amount: Amount in EUR to extract
            dry_run: If True, only simulate the operation
            
        Returns:
            Tuple of (success, operation_summary)
        """
        operation_summary = {
            'eur_amount_requested': eur_amount,
            'timestamp': datetime.now(),
            'dry_run': dry_run,
            'steps_completed': [],
            'errors': [],
            'positions_sold': {},
            'bnb_collected': 0.0,
            'usdc_received': 0.0,
            'reserve_preserved': True
        }
        
        try:
            logger.info(f"Starting extract operation: €{eur_amount} (Dry run: {dry_run})")
            
            # Step 1: Validate prerequisites
            if not self.check_usdc_availability():
                error = "USDC trading pairs not available"
                operation_summary['errors'].append(error)
                return False, operation_summary
            
            operation_summary['steps_completed'].append("Prerequisites validated")
            
            # Step 2: Calculate extract amounts
            success, extract_amounts, total_bnb_needed = self.calculate_extract_amounts(eur_amount)
            if not success:
                error = "Failed to calculate extract amounts"
                operation_summary['errors'].append(error)
                return False, operation_summary
            
            operation_summary['steps_completed'].append("Extract amounts calculated")
            operation_summary['bnb_needed'] = total_bnb_needed
            
            # Step 3: Freeze robot (if not dry run)
            if not dry_run:
                freeze_success = self.robot_state_manager.freeze_robot(f"Portfolio extraction in progress: €{eur_amount}")
                if not freeze_success:
                    error = "Failed to freeze robot"
                    operation_summary['errors'].append(error)
                    return False, operation_summary
                
                operation_summary['steps_completed'].append("Robot frozen")
            else:
                operation_summary['steps_completed'].append("Robot freeze skipped (dry run)")
            
            # Step 4: Execute sells
            total_bnb_collected = 0.0
            positions_sold = {}
            
            try:
                for symbol, quantity_to_sell in extract_amounts.items():
                    if quantity_to_sell <= 0:
                        continue
                    
                    current_price = self.binance_client.get_current_price(f"{symbol}BNB")
                    
                    if not dry_run:
                        # Execute actual sell
                        cost = self.portfolio_manager.execute_trade(symbol, "SELL", quantity_to_sell, current_price)
                        if cost >= 0:  # Successful trade (cost is fee for sells)
                            bnb_received = (quantity_to_sell * current_price) - cost
                            total_bnb_collected += bnb_received
                            positions_sold[symbol] = {
                                'quantity_sold': quantity_to_sell,
                                'price': current_price,
                                'bnb_received': bnb_received,
                                'fee': cost
                            }
                            logger.info(f"Sold {quantity_to_sell:.6f} {symbol} for {bnb_received:.6f} BNB")
                    else:
                        # Simulate sell
                        bnb_received = quantity_to_sell * current_price * (1 - 0.001)  # Simulate fee
                        total_bnb_collected += bnb_received
                        positions_sold[symbol] = {
                            'quantity_sold': quantity_to_sell,
                            'price': current_price,
                            'bnb_received': bnb_received,
                            'fee': quantity_to_sell * current_price * 0.001
                        }
                        logger.info(f"[SIMULATED] Sold {quantity_to_sell:.6f} {symbol} for {bnb_received:.6f} BNB")
                
                operation_summary['steps_completed'].append("Position sales executed")
                operation_summary['positions_sold'] = positions_sold
                operation_summary['bnb_collected'] = total_bnb_collected
                
                # Step 5: Convert BNB to USDC
                if total_bnb_collected > 0:
                    success, usdc_received = self.convert_bnb_to_usdc(total_bnb_collected, dry_run)
                    if success:
                        operation_summary['usdc_received'] = usdc_received
                        if dry_run:
                            operation_summary['steps_completed'].append("BNB to USDC conversion simulated")
                        else:
                            operation_summary['steps_completed'].append("BNB converted to USDC")
                    else:
                        operation_summary['errors'].append("Failed to convert BNB to USDC")
                
            except Exception as e:
                error = f"Error during position sales: {e}"
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
            success = len(operation_summary['errors']) == 0 and total_bnb_collected > 0
            
            logger.info(f"Extract operation completed. Success: {success}")
            logger.info(f"BNB collected: {total_bnb_collected:.6f}")
            logger.info(f"USDC received: {operation_summary.get('usdc_received', 0):.6f}")
            
            return success, operation_summary
            
        except Exception as e:
            error = f"Unexpected error during extract operation: {e}"
            operation_summary['errors'].append(error)
            logger.error(error)
            
            # Try to unfreeze robot if it was frozen
            if not dry_run:
                try:
                    self.robot_state_manager.unfreeze_robot()
                except:
                    pass
            
            return False, operation_summary
