"""
Enhanced Real Trading Engine using the Unified Trading Engine

This engine replaces the old real trading logic with the new unified trading engine
that implements proper rebalancing, stop-loss, and market data integration.
"""

import logging
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime

from src.unified_trading_engine import EngineConfig, Portfolio, CryptoPosition
from src.engine_integration import RealTradingEngineAdapter, convert_db_portfolio_to_engine_portfolio
from src.balance_validator import BalanceValidator, validate_robot_startup_balance

logger = logging.getLogger(__name__)

class EnhancedRealTradingEngine:
    """
    Enhanced real trading engine that uses the unified trading logic
    """
    
    def __init__(self, binance_client, portfolio_manager=None, robot_state_manager=None):
        self.binance_client = binance_client
        self.portfolio_manager = portfolio_manager
        self.robot_state_manager = robot_state_manager
        
        self.config = EngineConfig.from_env()
        self.adapter = RealTradingEngineAdapter(binance_client, self.config)
        self.balance_validator = BalanceValidator(binance_client)
        
        # Trading state
        self.stop_loss_triggered = False
        self.last_cycle_time = None
        self.startup_validated = False
        
        logger.info("Enhanced Real Trading Engine initialized with unified trading logic and balance validation")
    
    def get_current_portfolio_from_db(self) -> Portfolio:
        """
        Get current portfolio from database
        """
        try:
            if self.portfolio_manager:
                # Get portfolio from portfolio manager
                db_portfolio = self.portfolio_manager.get_current_portfolio()
                db_positions = self.portfolio_manager.get_active_positions()
                
                reserve = db_portfolio.bnb_reserve if db_portfolio else 0.0
                initial_value = getattr(db_portfolio, 'initial_value', reserve) if db_portfolio else reserve
                
                return convert_db_portfolio_to_engine_portfolio(db_positions, reserve, initial_value)
            else:
                # Fallback: create empty portfolio
                return Portfolio({}, 0.0, 0.0)
                
        except Exception as e:
            logger.error(f"Error getting portfolio from database: {e}")
            return Portfolio({}, 0.0, 0.0)
    
    def save_portfolio_to_db(self, portfolio: Portfolio, actions_taken: List[str]) -> bool:
        """
        Save updated portfolio to database
        """
        try:
            if not self.portfolio_manager:
                logger.warning("No portfolio manager available to save portfolio")
                return False
            
            # Update portfolio reserve
            self.portfolio_manager.update_portfolio_reserve(portfolio.reserve)
            
            # Update positions
            for symbol, position in portfolio.positions.items():
                self.portfolio_manager.update_or_create_position(
                    symbol=symbol,
                    quantity=position.quantity,
                    entry_price=position.entry_price,
                    current_price=position.current_price
                )
            
            # Deactivate positions that are no longer in the portfolio
            current_symbols = set(portfolio.positions.keys())
            db_positions = self.portfolio_manager.get_active_positions()
            
            for db_pos in db_positions:
                if db_pos.symbol not in current_symbols:
                    self.portfolio_manager.deactivate_position(db_pos.symbol)
            
            # Create trading cycle record
            self.portfolio_manager.create_trading_cycle(
                portfolio_value=portfolio.portfolio_value,
                bnb_reserve=portfolio.reserve,
                total_value=portfolio.total_value,
                actions_taken=actions_taken,
                portfolio_breakdown=self._create_portfolio_breakdown(portfolio)
            )
            
            logger.info(f"Portfolio saved to database: {len(portfolio.positions)} positions, "
                       f"reserve: {portfolio.reserve:.6f}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving portfolio to database: {e}")
            return False
    
    def _create_portfolio_breakdown(self, portfolio: Portfolio) -> Dict:
        """
        Create portfolio breakdown for database storage
        """
        breakdown = {}
        
        for symbol, position in portfolio.positions.items():
            breakdown[symbol] = {
                'value': position.current_value,
                'performance': position.performance,
                'quantity': position.quantity,
                'price': position.current_price,
                'entry_price': position.entry_price
            }
        
        return breakdown
    
    def validate_startup_balance(self) -> Tuple[bool, str]:
        """
        Validate that the Binance account has sufficient balance to start the robot
        Returns: (can_start, message)
        """
        logger.info("Validating Binance account balance for robot startup")
        
        try:
            is_valid, message, balances = self.balance_validator.validate_reserve_asset_balance()
            
            if is_valid:
                self.startup_validated = True
                logger.info("✅ Balance validation successful - robot can start")
            else:
                logger.error(f"❌ Balance validation failed: {message}")
            
            return is_valid, message
            
        except Exception as e:
            error_msg = f"Balance validation error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_balance_summary(self) -> Dict:
        """
        Get account balance summary for display
        """
        try:
            return self.balance_validator.get_balance_summary()
        except Exception as e:
            logger.error(f"Error getting balance summary: {e}")
            return {
                'success': False,
                'error': str(e),
                'balances': {},
                'can_start_robot': False
            }
    
    def check_robot_state(self) -> Tuple[bool, str]:
        """
        Check if robot is allowed to trade (includes balance validation)
        Returns: (can_trade, reason)
        """
        try:
            # First check balance if not already validated
            if not self.startup_validated:
                can_start, balance_msg = self.validate_startup_balance()
                if not can_start:
                    return False, f"Insufficient balance: {balance_msg}"
            
            if not self.robot_state_manager:
                return True, "No state manager"
            
            status = self.robot_state_manager.get_status_summary()
            
            if status.get('is_frozen', False):
                return False, f"Robot is frozen: {status.get('freeze_reason', 'Unknown reason')}"
            
            if status.get('cycles_suspended', False):
                return False, "Trading cycles are suspended"
            
            return True, "OK"
            
        except Exception as e:
            logger.error(f"Error checking robot state: {e}")
            return False, f"State check error: {e}"
    
    def startup_robot(self) -> Dict:
        """
        Perform startup validation and initialization
        """
        logger.info("Starting robot startup validation")
        
        try:
            # Validate balance first
            can_start, balance_message = self.validate_startup_balance()
            
            if not can_start:
                return {
                    'success': False,
                    'error': 'insufficient_balance',
                    'message': balance_message,
                    'can_start': False
                }
            
            # Get balance summary for logging
            balance_summary = self.get_balance_summary()
            
            logger.info("✅ Robot startup validation successful")
            logger.info(f"Reserve asset: {balance_summary.get('reserve_asset')} = {balance_summary.get('reserve_balance', 0):.6f}")
            
            return {
                'success': True,
                'message': balance_message,
                'balance_summary': balance_summary,
                'can_start': True
            }
            
        except Exception as e:
            error_msg = f"Robot startup failed: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': 'startup_error',
                'message': error_msg,
                'can_start': False
            }
    
    def execute_trading_cycle(self) -> Dict:
        """
        Execute a complete trading cycle
        """
        cycle_start_time = datetime.now()
        
        logger.info("Starting real trading cycle")
        
        # Check robot state (includes balance validation)
        can_trade, state_reason = self.check_robot_state()
        if not can_trade:
            logger.warning(f"Trading cycle skipped: {state_reason}")
            return {
                'success': False,
                'error': state_reason,
                'actions_taken': [],
                'cycle_time': cycle_start_time
            }
        
        try:
            # Get current portfolio
            current_portfolio = self.get_current_portfolio_from_db()
            
            # Run trading cycle
            result, execution_results = self.adapter.run_trading_cycle(current_portfolio)
            
            if not result.success:
                logger.error(f"Trading cycle failed: {result.error_message}")
                return {
                    'success': False,
                    'error': result.error_message,
                    'actions_taken': result.actions_taken,
                    'cycle_time': cycle_start_time
                }
            
            # Handle stop-loss
            if result.stop_loss_triggered:
                self.stop_loss_triggered = True
                logger.critical("STOP-LOSS TRIGGERED! Portfolio liquidated.")
                
                # Freeze robot to prevent further trading
                if self.robot_state_manager:
                    self.robot_state_manager.freeze_robot(
                        f"Stop-loss triggered at {cycle_start_time}. Portfolio value fell below 95% of initial value."
                    )
            
            # Save updated portfolio
            save_success = self.save_portfolio_to_db(result.new_portfolio, result.actions_taken)
            
            if not save_success:
                logger.error("Failed to save portfolio to database")
                return {
                    'success': False,
                    'error': 'Failed to save portfolio to database',
                    'actions_taken': result.actions_taken,
                    'execution_results': execution_results,
                    'cycle_time': cycle_start_time
                }
            
            self.last_cycle_time = cycle_start_time
            
            # Prepare cycle summary
            cycle_summary = {
                'success': True,
                'cycle_time': cycle_start_time,
                'actions_taken': result.actions_taken,
                'execution_results': execution_results,
                'portfolio_value': result.new_portfolio.portfolio_value,
                'reserve_value': result.new_portfolio.reserve,
                'total_value': result.new_portfolio.total_value,
                'performance_vs_initial': result.new_portfolio.performance_vs_initial,
                'stop_loss_triggered': result.stop_loss_triggered,
                'positions_count': len(result.new_portfolio.positions)
            }
            
            logger.info(f"Trading cycle completed successfully: "
                       f"Portfolio={result.new_portfolio.portfolio_value:.6f}, "
                       f"Reserve={result.new_portfolio.reserve:.6f}, "
                       f"Total={result.new_portfolio.total_value:.6f}")
            
            return cycle_summary
            
        except Exception as e:
            logger.error(f"Trading cycle failed with exception: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'success': False,
                'error': str(e),
                'actions_taken': [],
                'cycle_time': cycle_start_time
            }
    
    def get_portfolio_status(self) -> Dict:
        """
        Get current portfolio status
        """
        try:
            portfolio = self.get_current_portfolio_from_db()
            
            return {
                'portfolio_value': portfolio.portfolio_value,
                'reserve_value': portfolio.reserve,
                'total_value': portfolio.total_value,
                'performance_vs_initial': portfolio.performance_vs_initial,
                'positions_count': len(portfolio.positions),
                'stop_loss_triggered': self.stop_loss_triggered,
                'last_cycle_time': self.last_cycle_time,
                'positions': [
                    {
                        'symbol': pos.symbol,
                        'quantity': pos.quantity,
                        'entry_price': pos.entry_price,
                        'current_price': pos.current_price,
                        'current_value': pos.current_value,
                        'performance': pos.performance
                    }
                    for pos in portfolio.positions.values()
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting portfolio status: {e}")
            return {
                'error': str(e),
                'portfolio_value': 0.0,
                'reserve_value': 0.0,
                'total_value': 0.0,
                'positions_count': 0,
                'stop_loss_triggered': self.stop_loss_triggered
            }
    
    def manual_rebalance(self) -> Dict:
        """
        Manually trigger a rebalancing cycle
        """
        logger.info("Manual rebalance requested")
        return self.execute_trading_cycle()
    
    def emergency_stop(self, reason: str = "Manual emergency stop") -> Dict:
        """
        Emergency stop: liquidate all positions and freeze robot
        """
        logger.critical(f"Emergency stop triggered: {reason}")
        
        try:
            # Get current portfolio
            current_portfolio = self.get_current_portfolio_from_db()
            
            # Force liquidation by setting stop-loss
            current_portfolio.initial_value = current_portfolio.total_value * 2  # Force stop-loss
            
            # Run trading cycle (should trigger stop-loss)
            result = self.execute_trading_cycle()
            
            # Ensure robot is frozen
            if self.robot_state_manager:
                self.robot_state_manager.freeze_robot(f"Emergency stop: {reason}")
            
            return {
                'success': True,
                'message': 'Emergency stop executed',
                'reason': reason,
                'result': result
            }
            
        except Exception as e:
            logger.error(f"Emergency stop failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'reason': reason
            }

# Example usage and testing
if __name__ == "__main__":
    import os
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    print("Enhanced Real Trading Engine")
    print("=" * 40)
    print("This engine integrates with:")
    print("- Binance API for market data and trade execution")
    print("- Database for portfolio persistence")
    print("- Robot state manager for safety controls")
    print("- Unified trading logic with stop-loss and rebalancing")
    print()
    print("Key features:")
    print("- Replace underperformers (<-5% over 4 cycles)")
    print("- Select from top 50 coins by market cap")
    print("- 10-coin portfolio allocation")
    print("- Stop-loss at 95% of initial value")
    print("- Trading fee consideration (0.1% default)")
    print("- Real-time market data integration")
    print()
    print("To use this engine, initialize with:")
    print("engine = EnhancedRealTradingEngine(binance_client, portfolio_manager, robot_state_manager)")
    print("result = engine.execute_trading_cycle()")