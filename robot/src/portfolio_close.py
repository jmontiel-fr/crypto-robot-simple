"""
Portfolio Closer for complete portfolio liquidation and reset functionality
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from decimal import Decimal

logger = logging.getLogger(__name__)

class PortfolioCloser:
    """
    Handles complete portfolio closure operations including:
    - Liquidating all cryptocurrency positions
    - Converting BNB reserve to USDC
    - Clearing portfolio data
    - Optionally resetting with new configuration
    """
    
    def __init__(self, portfolio_manager, binance_client, robot_state_manager):
        """
        Initialize portfolio closer
        
        Args:
            portfolio_manager: Portfolio management instance
            binance_client: Enhanced Binance client
            robot_state_manager: Robot state management instance
        """
        self.portfolio_manager = portfolio_manager
        self.binance_client = binance_client
        self.robot_state_manager = robot_state_manager
        self.logger = logger
        
    def execute_close(self, liquidate_all=True, reset_portfolio=False, 
                     new_reserve_amount=None, auto_start=False, dry_run=True):
        """
        Execute complete portfolio closure
        
        Args:
            liquidate_all: Whether to liquidate all positions
            reset_portfolio: Whether to reset portfolio after closure
            new_reserve_amount: New BNB reserve amount for reset
            auto_start: Whether to auto-start robot after reset
            dry_run: Whether to simulate the operation
            
        Returns:
            Tuple[bool, Dict]: Success status and operation summary
        """
        steps_completed = []
        errors = []
        
        try:
            # Step 1: Freeze the robot
            self.logger.info("Step 1: Freezing robot for portfolio closure")
            if not dry_run:
                self.robot_state_manager.freeze_robot("Portfolio closure operation")
            steps_completed.append("Robot frozen")
            
            # Step 2: Get current portfolio state
            self.logger.info("Step 2: Analyzing current portfolio")
            portfolio_info = self._get_portfolio_info()
            if not portfolio_info['has_positions'] and not portfolio_info['has_reserve']:
                return False, {
                    'errors': ['No positions or reserve to liquidate'],
                    'steps_completed': steps_completed,
                    'dry_run': dry_run
                }
            steps_completed.append("Portfolio analyzed")
            
            # Step 3: Liquidate all crypto positions
            total_usdc_generated = 0
            positions_liquidated = 0
            
            if portfolio_info['has_positions']:
                self.logger.info("Step 3: Liquidating all cryptocurrency positions")
                liquidation_result = self._liquidate_all_positions(dry_run)
                if not liquidation_result['success']:
                    errors.extend(liquidation_result['errors'])
                else:
                    total_usdc_generated += liquidation_result['usdc_generated']
                    positions_liquidated = liquidation_result['positions_count']
                    steps_completed.append(f"Liquidated {positions_liquidated} positions")
            
            # Step 4: Convert BNB reserve to USDC
            bnb_converted = 0
            if portfolio_info['has_reserve']:
                self.logger.info("Step 4: Converting BNB reserve to USDC")
                bnb_result = self._convert_bnb_reserve(dry_run)
                if not bnb_result['success']:
                    errors.extend(bnb_result['errors'])
                else:
                    total_usdc_generated += bnb_result['usdc_generated']
                    bnb_converted = bnb_result['bnb_converted']
                    steps_completed.append(f"Converted {bnb_converted:.6f} BNB reserve")
            
            # Step 5: Clear portfolio data
            if not dry_run:
                self.logger.info("Step 5: Clearing portfolio data")
                self._clear_portfolio_data()
                steps_completed.append("Portfolio data cleared")
            else:
                steps_completed.append("Portfolio data would be cleared")
            
            # Step 6: Reset portfolio if requested
            if reset_portfolio:
                self.logger.info("Step 6: Resetting portfolio with new configuration")
                reset_result = self._reset_portfolio(
                    new_reserve_amount, auto_start, dry_run
                )
                if not reset_result['success']:
                    errors.extend(reset_result['errors'])
                else:
                    steps_completed.append("Portfolio reset completed")
            
            # Prepare summary
            summary = {
                'total_usdc_generated': total_usdc_generated,
                'positions_liquidated': positions_liquidated,
                'bnb_converted': bnb_converted,
                'reset_portfolio': reset_portfolio,
                'new_reserve_amount': new_reserve_amount if reset_portfolio else 0,
                'auto_start': auto_start if reset_portfolio else False,
                'dry_run': dry_run,
                'steps_completed': steps_completed,
                'errors': errors
            }
            
            success = len(errors) == 0
            
            if success:
                self.logger.info(f"Portfolio closure {'simulation' if dry_run else 'operation'} completed successfully")
            else:
                self.logger.error(f"Portfolio closure failed with {len(errors)} errors")
            
            return success, summary
            
        except Exception as e:
            error_msg = f"Portfolio closure operation failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            errors.append(error_msg)
            
            return False, {
                'errors': errors,
                'steps_completed': steps_completed,
                'dry_run': dry_run
            }
    
    def _get_portfolio_info(self):
        """Get current portfolio information"""
        try:
            # Get current positions
            positions = self.portfolio_manager.get_current_positions()
            has_positions = len(positions) > 0
            
            # Get BNB reserve
            state = self.robot_state_manager.get_state()
            bnb_reserve = state.get('bnb_reserve', 0)
            has_reserve = bnb_reserve > 0.001  # More than dust amount
            
            return {
                'has_positions': has_positions,
                'has_reserve': has_reserve,
                'positions_count': len(positions),
                'bnb_reserve': bnb_reserve,
                'positions': positions
            }
        except Exception as e:
            self.logger.error(f"Failed to get portfolio info: {e}")
            return {
                'has_positions': False,
                'has_reserve': False,
                'positions_count': 0,
                'bnb_reserve': 0,
                'positions': {}
            }
    
    def _liquidate_all_positions(self, dry_run=True):
        """Liquidate all cryptocurrency positions"""
        try:
            positions = self.portfolio_manager.get_current_positions()
            if not positions:
                return {
                    'success': True,
                    'usdc_generated': 0,
                    'positions_count': 0,
                    'errors': []
                }
            
            total_usdc = 0
            liquidation_errors = []
            successful_liquidations = 0
            
            for symbol, position in positions.items():
                if symbol == 'USDC':  # Skip USDC itself
                    continue
                    
                try:
                    amount = position.get('amount', 0)
                    if amount <= 0:
                        continue
                    
                    if dry_run:
                        # Simulate the sale
                        current_price = self.binance_client.get_current_price(f"{symbol}USDT")
                        estimated_usdc = amount * current_price
                        total_usdc += estimated_usdc
                        successful_liquidations += 1
                        self.logger.info(f"[DRY RUN] Would sell {amount} {symbol} for ~{estimated_usdc:.2f} USDC")
                    else:
                        # Execute actual sale
                        sale_result = self._sell_position_to_usdc(symbol, amount)
                        if sale_result['success']:
                            total_usdc += sale_result['usdc_received']
                            successful_liquidations += 1
                        else:
                            liquidation_errors.extend(sale_result['errors'])
                            
                except Exception as e:
                    error_msg = f"Failed to liquidate {symbol}: {str(e)}"
                    self.logger.error(error_msg)
                    liquidation_errors.append(error_msg)
            
            return {
                'success': len(liquidation_errors) == 0,
                'usdc_generated': total_usdc,
                'positions_count': successful_liquidations,
                'errors': liquidation_errors
            }
            
        except Exception as e:
            error_msg = f"Failed to liquidate positions: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'usdc_generated': 0,
                'positions_count': 0,
                'errors': [error_msg]
            }
    
    def _sell_position_to_usdc(self, symbol, amount):
        """Sell a specific position to USDC"""
        try:
            # First try direct SYMBOL/USDC pair
            usdc_pair = f"{symbol}USDC"
            
            try:
                # Check if USDC pair exists and is active
                symbol_info = self.binance_client.get_symbol_info(usdc_pair)
                if symbol_info and symbol_info['status'] == 'TRADING':
                    result = self.binance_client.place_market_sell_order(usdc_pair, amount)
                    if result['success']:
                        return {
                            'success': True,
                            'usdc_received': result['filled_qty'] * result['avg_price'],
                            'errors': []
                        }
            except:
                pass  # Fall back to USDT conversion
            
            # Fall back to SYMBOL/USDT then USDT/USDC
            usdt_pair = f"{symbol}USDT"
            
            # Sell to USDT first
            usdt_result = self.binance_client.place_market_sell_order(usdt_pair, amount)
            if not usdt_result['success']:
                return {
                    'success': False,
                    'usdc_received': 0,
                    'errors': [f"Failed to sell {symbol} to USDT: {usdt_result.get('error', 'Unknown error')}"]
                }
            
            usdt_amount = usdt_result['filled_qty'] * usdt_result['avg_price']
            
            # Convert USDT to USDC
            usdc_result = self.binance_client.place_market_buy_order("USDCUSDT", usdt_amount)
            if not usdc_result['success']:
                return {
                    'success': False,
                    'usdc_received': 0,
                    'errors': [f"Failed to convert USDT to USDC: {usdc_result.get('error', 'Unknown error')}"]
                }
            
            return {
                'success': True,
                'usdc_received': usdc_result['filled_qty'],
                'errors': []
            }
            
        except Exception as e:
            error_msg = f"Failed to sell {symbol}: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'usdc_received': 0,
                'errors': [error_msg]
            }
    
    def _convert_bnb_reserve(self, dry_run=True):
        """Convert BNB reserve to USDC (keeping small amount for fees)"""
        try:
            state = self.robot_state_manager.get_state()
            bnb_reserve = state.get('bnb_reserve', 0)
            
            if bnb_reserve <= 0.001:  # Less than dust amount
                return {
                    'success': True,
                    'usdc_generated': 0,
                    'bnb_converted': 0,
                    'errors': []
                }
            
            # Keep small amount for transaction fees (0.001 BNB)
            fee_reserve = 0.001
            convertible_bnb = max(0, bnb_reserve - fee_reserve)
            
            if convertible_bnb <= 0:
                return {
                    'success': True,
                    'usdc_generated': 0,
                    'bnb_converted': 0,
                    'errors': []
                }
            
            if dry_run:
                # Simulate the conversion
                bnb_price = self.binance_client.get_current_price("BNBUSDT")
                estimated_usdc = convertible_bnb * bnb_price
                self.logger.info(f"[DRY RUN] Would convert {convertible_bnb:.6f} BNB to ~{estimated_usdc:.2f} USDC")
                return {
                    'success': True,
                    'usdc_generated': estimated_usdc,
                    'bnb_converted': convertible_bnb,
                    'errors': []
                }
            else:
                # Execute actual conversion
                # First convert BNB to USDT
                usdt_result = self.binance_client.place_market_sell_order("BNBUSDT", convertible_bnb)
                if not usdt_result['success']:
                    return {
                        'success': False,
                        'usdc_generated': 0,
                        'bnb_converted': 0,
                        'errors': [f"Failed to convert BNB to USDT: {usdt_result.get('error', 'Unknown error')}"]
                    }
                
                usdt_amount = usdt_result['filled_qty'] * usdt_result['avg_price']
                
                # Then convert USDT to USDC
                usdc_result = self.binance_client.place_market_buy_order("USDCUSDT", usdt_amount)
                if not usdc_result['success']:
                    return {
                        'success': False,
                        'usdc_generated': 0,
                        'bnb_converted': 0,
                        'errors': [f"Failed to convert USDT to USDC: {usdc_result.get('error', 'Unknown error')}"]
                    }
                
                # Update robot state with remaining BNB
                self.robot_state_manager.update_state({'bnb_reserve': fee_reserve})
                
                return {
                    'success': True,
                    'usdc_generated': usdc_result['filled_qty'],
                    'bnb_converted': convertible_bnb,
                    'errors': []
                }
                
        except Exception as e:
            error_msg = f"Failed to convert BNB reserve: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'usdc_generated': 0,
                'bnb_converted': 0,
                'errors': [error_msg]
            }
    
    def _clear_portfolio_data(self):
        """Clear all portfolio data from database"""
        try:
            # Clear positions
            self.portfolio_manager.clear_all_positions()
            
            # Clear trading cycles
            self.portfolio_manager.clear_trading_history()
            
            # Reset robot state (except BNB reserve which is handled separately)
            state = self.robot_state_manager.get_state()
            new_state = {
                'status': 'NOT_STARTED',
                'bnb_reserve': state.get('bnb_reserve', 0),
                'current_cycle': 0,
                'is_frozen': False,
                'freeze_reason': None,
                'last_operation': 'portfolio_closed',
                'last_update': datetime.now().isoformat()
            }
            self.robot_state_manager.update_state(new_state)
            
            self.logger.info("Portfolio data cleared successfully")
            
        except Exception as e:
            error_msg = f"Failed to clear portfolio data: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
    
    def _reset_portfolio(self, new_reserve_amount, auto_start, dry_run=True):
        """Reset portfolio with new configuration"""
        try:
            if dry_run:
                self.logger.info(f"[DRY RUN] Would reset portfolio with {new_reserve_amount} BNB reserve")
                return {
                    'success': True,
                    'errors': []
                }
            
            # Set new BNB reserve
            new_state = {
                'status': 'NOT_STARTED',
                'bnb_reserve': new_reserve_amount,
                'current_cycle': 0,
                'is_frozen': False,
                'freeze_reason': None,
                'last_operation': 'portfolio_reset',
                'last_update': datetime.now().isoformat()
            }
            
            if auto_start:
                new_state['status'] = 'RUNNING'
                new_state['last_operation'] = 'portfolio_reset_and_started'
            
            self.robot_state_manager.update_state(new_state)
            
            self.logger.info(f"Portfolio reset with {new_reserve_amount} BNB reserve, auto_start: {auto_start}")
            
            return {
                'success': True,
                'errors': []
            }
            
        except Exception as e:
            error_msg = f"Failed to reset portfolio: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'errors': [error_msg]
            }
