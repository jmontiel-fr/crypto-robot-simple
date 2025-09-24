#!/usr/bin/env python3
"""
Real Trading Robot using Unified Daily Rebalance Engine
Ensures identical logic between simulation and real trading
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
from typing import Optional

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unified_daily_rebalance_engine import UnifiedDailyRebalanceEngine, ExecutionMode, ExecutionResult
from enhanced_binance_client import EnhancedBinanceClient
from robot_state import robot_state_manager

logger = logging.getLogger(__name__)

class RealTradingRobot:
    """
    Real trading robot that uses the same logic as simulations
    """
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        
        # Initialize Binance client
        self.binance_client = None
        if not dry_run:
            try:
                self.binance_client = EnhancedBinanceClient()
                logger.info("✅ Binance client initialized for real trading")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Binance client: {e}")
                raise
        
        # Initialize unified engine
        mode = ExecutionMode.DRY_RUN if dry_run else ExecutionMode.REAL_TRADING
        self.engine = UnifiedDailyRebalanceEngine(mode, self.binance_client, realistic_mode=True)
        
        # Trading state
        self.is_running = False
        self.last_execution_time = None
        self.execution_count = 0
        
        # Configuration from environment
        self.cycle_hours = int(os.getenv('CYCLE_DURATION', '1440')) // 60  # Convert minutes to hours
        self.max_executions = int(os.getenv('MAX_EXECUTIONS', '0'))  # 0 = unlimited
        self.starting_capital = float(os.getenv('STARTING_CAPITAL', '100.0'))
        
        logger.info(f"🤖 Real Trading Robot initialized")
        logger.info(f"🔄 Mode: {'DRY RUN' if dry_run else 'LIVE TRADING'}")
        logger.info(f"⏰ Cycle Frequency: {self.cycle_hours} hours")
        logger.info(f"💰 Starting Capital: {self.starting_capital}")
        logger.info(f"🎯 Strategy: {self.engine.strategy.strategy_name} v{self.engine.strategy.strategy_version}")
    
    def validate_startup(self) -> bool:
        """Validate robot startup conditions"""
        logger.info("🔍 Validating startup conditions...")
        
        try:
            # Validate execution environment
            if not self.engine.validate_execution_environment():
                logger.error("❌ Execution environment validation failed")
                return False
            
            # Check robot state
            if robot_state_manager.is_robot_running():
                logger.error("❌ Another robot instance is already running")
                return False
            
            # Validate configuration
            if self.cycle_hours <= 0:
                logger.error("❌ Invalid cycle frequency")
                return False
            
            if self.starting_capital <= 0:
                logger.error("❌ Invalid starting capital")
                return False
            
            logger.info("✅ Startup validation completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Startup validation failed: {e}")
            return False
    
    def execute_trading_cycle(self) -> ExecutionResult:
        """Execute a single trading cycle"""
        
        current_time = datetime.now()
        current_capital = self.engine.current_capital or self.starting_capital
        
        logger.info(f"🔄 Executing trading cycle #{self.execution_count + 1}")
        logger.info(f"📅 Time: {current_time}")
        logger.info(f"💰 Current Capital: {current_capital:.2f}")
        
        try:
            # Execute the rebalance cycle
            result = self.engine.execute_rebalance_cycle(current_time, current_capital)
            
            # Update state
            self.last_execution_time = current_time
            self.execution_count += 1
            
            # Log results
            if result.success:
                logger.info(f"✅ Trading cycle completed successfully")
                logger.info(f"📊 Return: {result.total_return:.2f}%")
                logger.info(f"💰 New Capital: {result.ending_capital:.2f}")
                logger.info(f"🎯 Volatility Mode: {result.volatility_mode}")
                logger.info(f"🛡️ USDC Protection: {result.usdc_protection}")
                logger.info(f"💸 Trading Costs: ${result.trading_costs:.2f}")
                
                # Update robot state
                robot_state_manager.update_last_execution(current_time)
                robot_state_manager.update_performance_metrics(
                    total_return=result.total_return,
                    current_capital=result.ending_capital,
                    trading_costs=result.trading_costs
                )
                
            else:
                logger.error(f"❌ Trading cycle failed: {result.error_message}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Trading cycle execution failed: {e}")
            import traceback
            traceback.print_exc()
            
            # Return failed result
            return ExecutionResult(
                success=False,
                mode=self.engine.mode,
                timestamp=current_time,
                starting_capital=current_capital,
                ending_capital=current_capital,
                portfolio_value=0.0,
                reserve_value=current_capital,
                total_return=0.0,
                actions_taken=[],
                allocations={},
                trading_costs=0.0,
                market_regime='ERROR',
                volatility_mode=self.engine.strategy.volatility_mode,
                usdc_protection=False,
                error_message=str(e)
            )
    
    def should_execute_cycle(self) -> bool:
        """Check if it's time to execute a trading cycle"""
        
        if not self.last_execution_time:
            return True  # First execution
        
        # Check if enough time has passed
        time_since_last = datetime.now() - self.last_execution_time
        hours_since_last = time_since_last.total_seconds() / 3600
        
        return hours_since_last >= self.cycle_hours
    
    def run_automated_trading(self):
        """Run automated trading with the specified cycle frequency"""
        
        if not self.validate_startup():
            logger.error("❌ Startup validation failed, cannot start trading")
            return
        
        logger.info("🚀 Starting automated trading...")
        logger.info(f"⏰ Cycle frequency: {self.cycle_hours} hours")
        logger.info(f"🎯 Max executions: {'Unlimited' if self.max_executions == 0 else self.max_executions}")
        
        # Mark robot as running
        robot_state_manager.set_robot_running(True)
        self.is_running = True
        
        try:
            while self.is_running:
                try:
                    # Check if it's time to execute
                    if self.should_execute_cycle():
                        # Execute trading cycle
                        result = self.execute_trading_cycle()
                        
                        # Check if we should stop
                        if self.max_executions > 0 and self.execution_count >= self.max_executions:
                            logger.info(f"🏁 Reached maximum executions ({self.max_executions}), stopping")
                            break
                        
                        if not result.success:
                            logger.warning("⚠️ Trading cycle failed, but continuing...")
                    
                    # Wait before next check (check every minute)
                    time.sleep(60)
                    
                except KeyboardInterrupt:
                    logger.info("🛑 Received stop signal")
                    break
                    
                except Exception as e:
                    logger.error(f"❌ Error in trading loop: {e}")
                    time.sleep(300)  # Wait 5 minutes before retrying
        
        finally:
            # Clean shutdown
            self.is_running = False
            robot_state_manager.set_robot_running(False)
            
            # Print final summary
            self._print_final_summary()
            
            logger.info("🏁 Automated trading stopped")
    
    def run_single_cycle(self) -> ExecutionResult:
        """Run a single trading cycle (for testing or manual execution)"""
        
        if not self.validate_startup():
            logger.error("❌ Startup validation failed, cannot execute cycle")
            return None
        
        logger.info("🔄 Executing single trading cycle...")
        
        try:
            result = self.execute_trading_cycle()
            self._print_cycle_summary(result)
            return result
            
        except Exception as e:
            logger.error(f"❌ Single cycle execution failed: {e}")
            return None
    
    def _print_cycle_summary(self, result: ExecutionResult):
        """Print summary of a trading cycle"""
        
        print("\n" + "=" * 60)
        print("📊 TRADING CYCLE SUMMARY")
        print("=" * 60)
        
        print(f"🕐 Timestamp: {result.timestamp}")
        print(f"🎯 Mode: {result.mode.value.upper()}")
        print(f"✅ Success: {result.success}")
        
        if result.success:
            print(f"💰 Starting Capital: ${result.starting_capital:.2f}")
            print(f"💰 Ending Capital: ${result.ending_capital:.2f}")
            print(f"📈 Total Return: {result.total_return:.2f}%")
            print(f"💼 Portfolio Value: ${result.portfolio_value:.2f}")
            print(f"🏦 Reserve Value: ${result.reserve_value:.2f}")
            print(f"💸 Trading Costs: ${result.trading_costs:.2f}")
            print(f"🌍 Market Regime: {result.market_regime}")
            print(f"📊 Volatility Mode: {result.volatility_mode}")
            print(f"🛡️ USDC Protection: {result.usdc_protection}")
            
            print(f"\n📋 Actions Taken:")
            for action in result.actions_taken:
                print(f"  • {action}")
            
            if result.allocations:
                print(f"\n💼 Portfolio Allocations:")
                for symbol, allocation in result.allocations.items():
                    print(f"  • {symbol}: {allocation:.1%}")
        else:
            print(f"❌ Error: {result.error_message}")
        
        print("=" * 60)
    
    def _print_final_summary(self):
        """Print final trading summary"""
        
        performance = self.engine.get_performance_summary()
        
        print("\n" + "=" * 60)
        print("🏁 FINAL TRADING SUMMARY")
        print("=" * 60)
        
        print(f"🔄 Total Executions: {performance['total_executions']}")
        print(f"✅ Success Rate: {performance['success_rate']:.1f}%")
        print(f"📈 Total Return: {performance['total_return']:.2f}%")
        print(f"📊 Average Return: {performance['average_return']:.2f}%")
        print(f"💸 Total Trading Costs: ${performance['total_trading_costs']:.2f}")
        print(f"💰 Final Capital: ${performance['current_capital']:.2f}")
        print(f"🎯 Volatility Modes Used: {', '.join(performance['volatility_modes_used'])}")
        print(f"🛡️ USDC Protection Cycles: {performance['usdc_protection_cycles']}")
        
        print("=" * 60)
    
    def stop(self):
        """Stop the trading robot"""
        logger.info("🛑 Stopping trading robot...")
        self.is_running = False

# Factory functions
def create_real_trading_robot(dry_run: bool = True) -> RealTradingRobot:
    """Create a real trading robot"""
    return RealTradingRobot(dry_run=dry_run)

def create_live_trading_robot() -> RealTradingRobot:
    """Create a live trading robot (not dry run)"""
    return RealTradingRobot(dry_run=False)

# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Real Trading Robot')
    parser.add_argument('--mode', choices=['single', 'auto'], default='single',
                       help='Execution mode (default: single)')
    parser.add_argument('--live', action='store_true',
                       help='Enable live trading (default: dry run)')
    parser.add_argument('--capital', type=float,
                       help='Starting capital override')
    
    args = parser.parse_args()
    
    # Override starting capital if provided
    if args.capital:
        os.environ['STARTING_CAPITAL'] = str(args.capital)
    
    # Create robot
    robot = RealTradingRobot(dry_run=not args.live)
    
    try:
        if args.mode == 'single':
            # Run single cycle
            result = robot.run_single_cycle()
            if result and result.success:
                print("✅ Single cycle completed successfully")
            else:
                print("❌ Single cycle failed")
        else:
            # Run automated trading
            robot.run_automated_trading()
            
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
        robot.stop()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()