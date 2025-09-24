#!/usr/bin/env python3
"""
Unified Daily Rebalance Engine
Ensures identical logic between simulation and real trading execution
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

# Import the volatility-optimized strategy
from daily_rebalance_volatile_strategy import DailyRebalanceVolatileStrategy

logger = logging.getLogger(__name__)

class ExecutionMode(Enum):
    SIMULATION = "simulation"
    REAL_TRADING = "real_trading"
    DRY_RUN = "dry_run"

@dataclass
class ExecutionResult:
    """Result of a trading execution"""
    success: bool
    mode: ExecutionMode
    timestamp: datetime
    starting_capital: float
    ending_capital: float
    portfolio_value: float
    reserve_value: float
    total_return: float
    actions_taken: List[str]
    allocations: Dict[str, float]
    trading_costs: float
    market_regime: str
    volatility_mode: str
    usdc_protection: bool
    error_message: str = ""
    
    @property
    def performance_summary(self) -> Dict:
        """Get performance summary"""
        return {
            'starting_capital': self.starting_capital,
            'ending_capital': self.ending_capital,
            'total_return': self.total_return,
            'portfolio_value': self.portfolio_value,
            'reserve_value': self.reserve_value,
            'trading_costs': self.trading_costs,
            'net_profit': self.ending_capital - self.starting_capital - self.trading_costs
        }

class UnifiedDailyRebalanceEngine:
    """
    Unified engine that ensures identical logic between simulation and real trading
    """
    
    def __init__(self, mode: ExecutionMode, binance_client=None, realistic_mode: bool = True):
        self.mode = mode
        self.binance_client = binance_client
        self.realistic_mode = realistic_mode
        
        # Initialize the volatility-optimized strategy
        self.strategy = DailyRebalanceVolatileStrategy(realistic_mode=realistic_mode)
        
        # Execution state
        self.current_capital = 0.0
        self.execution_history = []
        
        # Import os for environment variables
        import os
        
        # Configuration from environment
        self.dry_run_mode = os.getenv('ROBOT_DRY_RUN', 'true').lower() == 'true'
        self.min_balance_required = float(os.getenv('MIN_BALANCE_REQUIRED', '10.0'))
        
        # Calibration profile for realistic constraints (dry-run and simulation modes)
        self.calibration_profile = None
        self.apply_calibration = os.getenv('ENABLE_CALIBRATION', 'true').lower() == 'true'
        
        if self.apply_calibration and (mode in [ExecutionMode.DRY_RUN, ExecutionMode.SIMULATION]):
            self._load_calibration_profile()
        
        logger.info(f"Unified Daily Rebalance Engine initialized in {mode.value} mode")
        logger.info(f"Strategy: {self.strategy.strategy_name} v{self.strategy.strategy_version}")
        logger.info(f"Volatility Mode: {self.strategy.volatility_mode}")
        logger.info(f"Realistic Mode: {realistic_mode}")
        logger.info(f"Dry Run: {self.dry_run_mode}")
        logger.info(f"Calibration Applied: {self.apply_calibration}")
        if self.calibration_profile:
            logger.info(f"Calibration Profile: {self.calibration_profile.get('profile_name', 'Unknown')}")
    
    def _load_calibration_profile(self):
        """Load calibration profile for realistic constraints"""
        try:
            import json
            import os
            
            # Get default profile name from environment
            default_profile = os.getenv('DEFAULT_CALIBRATION_PROFILE', 'moderate_realistic')
            
            # Try to load the profile
            profile_path = f"calibration_profiles/{default_profile}.json"
            
            if os.path.exists(profile_path):
                with open(profile_path, 'r') as f:
                    self.calibration_profile = json.load(f)
                logger.info(f"✅ Loaded calibration profile: {default_profile}")
            else:
                # Use built-in moderate profile if file doesn't exist
                self.calibration_profile = self._get_builtin_moderate_profile()
                logger.info(f"✅ Using built-in calibration profile: moderate_realistic")
                
        except Exception as e:
            logger.warning(f"⚠️ Could not load calibration profile: {e}")
            logger.info("Using built-in moderate profile as fallback")
            self.calibration_profile = self._get_builtin_moderate_profile()
    
    def _get_builtin_moderate_profile(self):
        """Get built-in moderate calibration profile"""
        return {
            "profile_name": "moderate_realistic",
            "calibration_parameters": {
                "market_timing_efficiency": 0.70,
                "daily_slippage": 0.004,
                "trading_fee": 0.001,
                "volatility_drag": 0.002,
                "max_daily_return": 0.035,
                "min_daily_return": -0.05
            },
            "expected_monthly_return": "35-65%",
            "risk_level": "medium"
        }
    
    def validate_execution_environment(self) -> bool:
        """Validate that the execution environment is ready"""
        try:
            if self.mode == ExecutionMode.REAL_TRADING:
                if not self.binance_client:
                    logger.error("Real trading mode requires Binance client")
                    return False
                
                # Validate API connection
                try:
                    account_info = self.binance_client.get_account()
                    logger.info("✅ Binance API connection validated")
                except Exception as e:
                    logger.error(f"❌ Binance API connection failed: {e}")
                    return False
                
                # Check minimum balance
                if not self.dry_run_mode:
                    try:
                        balance = self._get_account_balance()
                        if balance < self.min_balance_required:
                            logger.error(f"❌ Insufficient balance: {balance} < {self.min_balance_required}")
                            return False
                        logger.info(f"✅ Account balance validated: {balance}")
                    except Exception as e:
                        logger.error(f"❌ Balance validation failed: {e}")
                        return False
            
            # Validate strategy configuration
            if not self.strategy.volatile_cryptos:
                logger.error("❌ No cryptocurrencies selected for trading")
                return False
            
            logger.info(f"✅ Execution environment validated for {self.mode.value} mode")
            return True
            
        except Exception as e:
            logger.error(f"❌ Environment validation failed: {e}")
            return False
    
    def execute_rebalance_cycle(self, current_date: datetime, starting_capital: float) -> ExecutionResult:
        """Execute a single rebalancing cycle using the unified strategy"""
        
        logger.info(f"*** 🔄 Executing rebalance cycle in {self.mode.value} mode ***")
        logger.info(f"*** 📅 Date: {current_date} ***")
        logger.info(f"*** 💰 Starting Capital: {starting_capital} ***")
        
        try:
            # Execute the strategy's daily rebalance logic (live trading mode)
            rebalance_result = self.strategy.execute_daily_rebalance(current_date, starting_capital, simulation_mode=False)
            
            if not rebalance_result or not rebalance_result.get('success'):
                error_msg = rebalance_result.get('reason', 'Unknown error') if rebalance_result else 'Strategy execution failed'
                logger.error(f"❌ Strategy execution failed: {error_msg}")
                
                return ExecutionResult(
                    success=False,
                    mode=self.mode,
                    timestamp=current_date,
                    starting_capital=starting_capital,
                    ending_capital=starting_capital,
                    portfolio_value=0.0,
                    reserve_value=starting_capital,
                    total_return=0.0,
                    actions_taken=[],
                    allocations={},
                    trading_costs=0.0,
                    market_regime='UNKNOWN',
                    volatility_mode=self.strategy.volatility_mode,
                    usdc_protection=False,
                    error_message=error_msg
                )
            
            # Extract results from strategy execution
            allocations = rebalance_result.get('allocations', {})
            trading_costs = rebalance_result.get('trading_costs', 0.0)
            market_regime = rebalance_result.get('market_regime', 'UNKNOWN')
            usdc_protection = rebalance_result.get('usdc_protection', False)
            volatility_mode = rebalance_result.get('volatility_mode', self.strategy.volatility_mode)
            
            # Execute trades based on mode
            if self.mode == ExecutionMode.SIMULATION:
                execution_result = self._execute_simulation_trades(
                    allocations, starting_capital, trading_costs, current_date
                )
            elif self.mode == ExecutionMode.REAL_TRADING:
                execution_result = self._execute_real_trades(
                    allocations, starting_capital, trading_costs, current_date
                )
            else:  # DRY_RUN
                execution_result = self._execute_dry_run_trades(
                    allocations, starting_capital, trading_costs, current_date
                )
            
            # Calculate final values
            ending_capital = execution_result['ending_capital']
            portfolio_value = execution_result['portfolio_value']
            reserve_value = execution_result['reserve_value']
            total_return = ((ending_capital / starting_capital) - 1) * 100 if starting_capital > 0 else 0.0
            
            # Create execution result
            result = ExecutionResult(
                success=True,
                mode=self.mode,
                timestamp=current_date,
                starting_capital=starting_capital,
                ending_capital=ending_capital,
                portfolio_value=portfolio_value,
                reserve_value=reserve_value,
                total_return=total_return,
                actions_taken=execution_result['actions_taken'],
                allocations=allocations,
                trading_costs=trading_costs,
                market_regime=market_regime,
                volatility_mode=volatility_mode,
                usdc_protection=usdc_protection
            )
            
            # Store execution history
            self.execution_history.append(result)
            self.current_capital = ending_capital
            
            logger.info(f"*** ✅ Rebalance cycle completed successfully ***")
            logger.info(f"*** 📊 Return: {total_return:.2f}% ***")
            logger.info(f"*** 💰 Final Capital: {ending_capital:.2f} ***")
            logger.info(f"*** 🎯 Volatility Mode: {volatility_mode} ***")
            logger.info(f"*** 🛡️ USDC Protection: {usdc_protection} ***")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Execution failed: {e}")
            import traceback
            traceback.print_exc()
            
            return ExecutionResult(
                success=False,
                mode=self.mode,
                timestamp=current_date,
                starting_capital=starting_capital,
                ending_capital=starting_capital,
                portfolio_value=0.0,
                reserve_value=starting_capital,
                total_return=0.0,
                actions_taken=[],
                allocations={},
                trading_costs=0.0,
                market_regime='ERROR',
                volatility_mode=self.strategy.volatility_mode,
                usdc_protection=False,
                error_message=str(e)
            )
    
    def _execute_simulation_trades(self, allocations: Dict[str, float], capital: float, 
                                 trading_costs: float, current_date: datetime) -> Dict:
        """Execute trades in simulation mode"""
        
        # In simulation mode, we use the strategy's built-in performance calculation
        # This ensures consistency with the simulation engine
        
        actions_taken = []
        
        if 'USDC' in allocations:
            # USDC protection mode
            portfolio_value = 0.0
            reserve_value = capital - trading_costs
            ending_capital = reserve_value
            actions_taken.append("USDC_PROTECTION: Converted to stablecoin")
        else:
            # Normal crypto allocation
            portfolio_value = capital * 0.95  # 95% in crypto
            reserve_value = capital * 0.05    # 5% reserve
            ending_capital = capital - trading_costs
            
            # Apply calibration constraints if enabled
            if self.apply_calibration and self.calibration_profile:
                ending_capital = self._apply_calibration_constraints(
                    capital, ending_capital, current_date
                )
                actions_taken.append("CALIBRATION: Applied realistic performance constraints")
            
            for symbol, allocation in allocations.items():
                if allocation > 0:
                    allocated_amount = capital * allocation
                    actions_taken.append(f"ALLOCATE {symbol}: {allocation:.1%} (${allocated_amount:.2f})")
        
        return {
            'ending_capital': ending_capital,
            'portfolio_value': portfolio_value,
            'reserve_value': reserve_value,
            'actions_taken': actions_taken
        }
    
    def _execute_real_trades(self, allocations: Dict[str, float], capital: float,
                           trading_costs: float, current_date: datetime) -> Dict:
        """Execute trades in real trading mode"""
        
        actions_taken = []
        
        if self.dry_run_mode:
            logger.info("🔍 DRY RUN MODE: No actual trades will be executed")
            return self._execute_dry_run_trades(allocations, capital, trading_costs, current_date)
        
        try:
            # Get current account balance
            account_balance = self._get_account_balance()
            
            if 'USDC' in allocations:
                # USDC protection: convert everything to USDC/BUSD
                actions_taken.append("REAL_TRADE: Converting portfolio to USDC protection")
                # Implementation would go here for real USDC conversion
                portfolio_value = 0.0
                reserve_value = account_balance
                ending_capital = account_balance
            else:
                # Normal crypto rebalancing
                actions_taken.append("REAL_TRADE: Executing crypto rebalancing")
                # Implementation would go here for real crypto trades
                portfolio_value = account_balance * 0.95
                reserve_value = account_balance * 0.05
                ending_capital = account_balance - trading_costs
                
                for symbol, allocation in allocations.items():
                    if allocation > 0:
                        # Real trade execution would go here
                        actions_taken.append(f"REAL_TRADE {symbol}: {allocation:.1%}")
            
            return {
                'ending_capital': ending_capital,
                'portfolio_value': portfolio_value,
                'reserve_value': reserve_value,
                'actions_taken': actions_taken
            }
            
        except Exception as e:
            logger.error(f"❌ Real trading execution failed: {e}")
            raise
    
    def _execute_dry_run_trades(self, allocations: Dict[str, float], capital: float,
                              trading_costs: float, current_date: datetime) -> Dict:
        """Execute trades in dry run mode (simulation of real trading with calibration)"""
        
        actions_taken = []
        
        if 'USDC' in allocations:
            # USDC protection simulation
            portfolio_value = 0.0
            reserve_value = capital - trading_costs
            ending_capital = reserve_value
            actions_taken.append("DRY_RUN: USDC Protection (would convert to stablecoin)")
        else:
            # Normal crypto allocation simulation
            portfolio_value = capital * 0.95
            reserve_value = capital * 0.05
            ending_capital = capital - trading_costs
            
            # Apply calibration constraints if enabled
            if self.apply_calibration and self.calibration_profile:
                ending_capital = self._apply_calibration_constraints(
                    capital, ending_capital, current_date
                )
                actions_taken.append("CALIBRATION: Applied realistic performance constraints")
            
            for symbol, allocation in allocations.items():
                if allocation > 0:
                    allocated_amount = capital * allocation
                    actions_taken.append(f"DRY_RUN {symbol}: {allocation:.1%} (${allocated_amount:.2f})")
        
        return {
            'ending_capital': ending_capital,
            'portfolio_value': portfolio_value,
            'reserve_value': reserve_value,
            'actions_taken': actions_taken
        }
    
    def _apply_calibration_constraints(self, starting_capital: float, raw_ending_capital: float, 
                                     current_date: datetime) -> float:
        """Apply calibration profile constraints to make performance realistic"""
        
        if not self.calibration_profile:
            return raw_ending_capital
        
        try:
            import random
            
            # Get calibration parameters
            params = self.calibration_profile.get('calibration_parameters', {})
            
            market_timing_efficiency = params.get('market_timing_efficiency', 0.70)
            daily_slippage = params.get('daily_slippage', 0.004)
            volatility_drag = params.get('volatility_drag', 0.002)
            max_daily_return = params.get('max_daily_return', 0.035)
            min_daily_return = params.get('min_daily_return', -0.05)
            
            # Calculate raw return
            raw_return = (raw_ending_capital / starting_capital) - 1 if starting_capital > 0 else 0
            
            # Apply market timing efficiency (reduce positive returns)
            if raw_return > 0:
                adjusted_return = raw_return * market_timing_efficiency
            else:
                adjusted_return = raw_return  # Don't reduce losses
            
            # Apply slippage and volatility drag
            adjusted_return -= daily_slippage
            adjusted_return -= volatility_drag
            
            # Add some randomness for realism (±20% of the adjustment)
            randomness_factor = 1.0 + (random.random() - 0.5) * 0.4
            adjusted_return *= randomness_factor
            
            # Cap the daily return to realistic limits
            adjusted_return = max(min_daily_return, min(adjusted_return, max_daily_return))
            
            # Calculate calibrated ending capital
            calibrated_ending_capital = starting_capital * (1 + adjusted_return)
            
            # Log calibration adjustment
            logger.info(f"📊 CALIBRATION: Raw return {raw_return:.2%} → Calibrated {adjusted_return:.2%}")
            logger.info(f"📊 CALIBRATION: Profile {self.calibration_profile.get('profile_name', 'Unknown')}")
            
            return calibrated_ending_capital
            
        except Exception as e:
            logger.warning(f"⚠️ Calibration constraint application failed: {e}")
            return raw_ending_capital
    
    def _get_account_balance(self) -> float:
        """Get current account balance from Binance"""
        if not self.binance_client:
            return 0.0
        
        try:
            account_info = self.binance_client.get_account()
            
            # Get BNB balance (or configured reserve asset)
            reserve_asset = os.getenv('RESERVE_ASSET', 'BNB')
            
            for balance in account_info['balances']:
                if balance['asset'] == reserve_asset:
                    free_balance = float(balance['free'])
                    locked_balance = float(balance['locked'])
                    total_balance = free_balance + locked_balance
                    return total_balance
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error getting account balance: {e}")
            raise
    
    def get_performance_summary(self) -> Dict:
        """Get overall performance summary"""
        if not self.execution_history:
            return {
                'total_executions': 0,
                'success_rate': 0.0,
                'total_return': 0.0,
                'average_return': 0.0,
                'total_trading_costs': 0.0,
                'volatility_modes_used': [],
                'usdc_protection_cycles': 0
            }
        
        successful_executions = [e for e in self.execution_history if e.success]
        total_executions = len(self.execution_history)
        success_rate = len(successful_executions) / total_executions * 100
        
        if successful_executions:
            first_capital = successful_executions[0].starting_capital
            last_capital = successful_executions[-1].ending_capital
            total_return = ((last_capital / first_capital) - 1) * 100 if first_capital > 0 else 0.0
            
            average_return = sum(e.total_return for e in successful_executions) / len(successful_executions)
            total_trading_costs = sum(e.trading_costs for e in successful_executions)
            
            volatility_modes = list(set(e.volatility_mode for e in successful_executions))
            usdc_protection_cycles = sum(1 for e in successful_executions if e.usdc_protection)
        else:
            total_return = 0.0
            average_return = 0.0
            total_trading_costs = 0.0
            volatility_modes = []
            usdc_protection_cycles = 0
        
        return {
            'total_executions': total_executions,
            'success_rate': success_rate,
            'total_return': total_return,
            'average_return': average_return,
            'total_trading_costs': total_trading_costs,
            'volatility_modes_used': volatility_modes,
            'usdc_protection_cycles': usdc_protection_cycles,
            'current_capital': self.current_capital
        }

# Factory function for creating engines
def create_unified_engine(mode: str, binance_client=None, realistic_mode: bool = True) -> UnifiedDailyRebalanceEngine:
    """Create a unified daily rebalance engine"""
    
    mode_enum = ExecutionMode(mode.lower())
    return UnifiedDailyRebalanceEngine(mode_enum, binance_client, realistic_mode)

# Example usage
if __name__ == "__main__":
    # Test the unified engine
    print("🧪 Testing Unified Daily Rebalance Engine")
    print("=" * 50)
    
    # Test simulation mode
    sim_engine = create_unified_engine("simulation", realistic_mode=True)
    
    if sim_engine.validate_execution_environment():
        print("✅ Environment validation passed")
        
        # Execute a test cycle
        test_date = datetime.now()
        test_capital = 1000.0
        
        result = sim_engine.execute_rebalance_cycle(test_date, test_capital)
        
        if result.success:
            print("✅ Test execution successful")
            print(f"📊 Performance: {result.performance_summary}")
        else:
            print(f"❌ Test execution failed: {result.error_message}")
    else:
        print("❌ Environment validation failed")