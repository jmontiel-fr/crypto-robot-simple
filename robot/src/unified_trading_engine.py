"""
Unified Trading Engine for both Real Trading and Simulations

This engine implements the same rebalancing logic for both real trading and simulations:
- Rebalance process at start and each cycle
- Replace underperforming cryptos (<-5% in last 4 cycles) with best performers
- Consider top 50 capitalized cryptos
- 10 crypto portfolio allocation
- Trading fee from .env (default 0.1%)
- Stop-loss at 95% of initial value
- Simulation-specific: historical data validation and blocking states
"""

import os
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class EngineMode(Enum):
    REAL_TRADING = "real"
    SIMULATION = "simulation"

@dataclass
class EngineConfig:
    """Configuration for the trading engine"""
    portfolio_size: int = 10
    trading_fee: float = 0.001  # 0.1%
    stop_loss_threshold: float = 0.95  # 95%
    underperformer_threshold: float = -0.05  # -5%
    lookback_cycles: int = 4
    top_coins_count: int = 50
    reserve_asset: str = "BNB"
    
    @classmethod
    def from_env(cls) -> 'EngineConfig':
        """Load configuration from environment variables"""
        return cls(
            portfolio_size=int(os.getenv('PORTFOLIO_SIZE', 10)),
            trading_fee=float(os.getenv('TRADING_FEE', 0.001)),
            stop_loss_threshold=float(os.getenv('STOP_LOSS_THRESHOLD', 0.95)),
            underperformer_threshold=float(os.getenv('UNDERPERFORMER_THRESHOLD', -0.05)),
            lookback_cycles=int(os.getenv('LOOKBACK_CYCLES', 4)),
            top_coins_count=int(os.getenv('TOP_COINS_COUNT', 50)),
            reserve_asset=os.getenv('RESERVE_ASSET', 'BNB')
        )

@dataclass
class CryptoPosition:
    """Represents a cryptocurrency position"""
    symbol: str
    quantity: float
    entry_price: float
    current_price: float = 0.0
    
    @property
    def current_value(self) -> float:
        return self.quantity * self.current_price
    
    @property
    def entry_value(self) -> float:
        return self.quantity * self.entry_price
    
    @property
    def performance(self) -> float:
        """Performance as a ratio (0.05 = 5%)"""
        if self.entry_value == 0:
            return 0.0
        return (self.current_value - self.entry_value) / self.entry_value

@dataclass
class Portfolio:
    """Represents the current portfolio state"""
    positions: Dict[str, CryptoPosition]
    reserve: float
    initial_value: float
    
    @property
    def portfolio_value(self) -> float:
        return sum(pos.current_value for pos in self.positions.values())
    
    @property
    def total_value(self) -> float:
        return self.portfolio_value + self.reserve
    
    @property
    def performance_vs_initial(self) -> float:
        """Performance vs initial value as ratio"""
        if self.initial_value == 0:
            return 0.0
        return self.total_value / self.initial_value

@dataclass
class RebalanceResult:
    """Result of a rebalancing operation"""
    success: bool
    new_portfolio: Portfolio
    actions_taken: List[str]
    error_message: str = ""
    stop_loss_triggered: bool = False
    simulation_blocked: bool = False

class UnifiedTradingEngine:
    """
    Unified trading engine that works for both real trading and simulations
    """
    
    def __init__(self, mode: EngineMode, config: Optional[EngineConfig] = None):
        self.mode = mode
        self.config = config or EngineConfig.from_env()
        self.price_history: Dict[str, List[float]] = {}
        self.cycle_count = 0
        
        logger.info(f"Initialized UnifiedTradingEngine in {mode.value} mode")
        logger.info(f"Config: portfolio_size={self.config.portfolio_size}, "
                   f"trading_fee={self.config.trading_fee}, "
                   f"stop_loss={self.config.stop_loss_threshold}")
    
    def update_price_history(self, current_prices: Dict[str, float]) -> None:
        """Update price history for all coins"""
        for symbol, price in current_prices.items():
            if symbol not in self.price_history:
                self.price_history[symbol] = []
            self.price_history[symbol].append(price)
    
    def get_top_50_coins(self, available_coins: List[str]) -> List[str]:
        """
        Get top 50 coins by market cap (or available coins in simulation)
        In simulation mode, this is limited by available historical data
        """
        if self.mode == EngineMode.SIMULATION:
            # In simulation, we're limited to coins with historical data
            return available_coins[:self.config.top_coins_count]
        else:
            # In real trading, fetch from Binance API or use provided list
            # For now, return the available coins (this should be enhanced with real market cap data)
            return available_coins[:self.config.top_coins_count]
    
    def calculate_performance_over_cycles(self, symbol: str, cycles: int = None) -> float:
        """Calculate cumulative performance over the last N cycles"""
        cycles = cycles or self.config.lookback_cycles
        prices = self.price_history.get(symbol, [])
        
        if len(prices) < cycles + 1:
            return 0.0
        
        start_price = prices[-(cycles + 1)]
        end_price = prices[-1]
        
        if start_price == 0:
            return 0.0
        
        return (end_price - start_price) / start_price
    
    def find_underperformers(self, portfolio: Portfolio) -> List[str]:
        """Find underperforming cryptos based on last 4 cycles performance"""
        underperformers = []
        
        for symbol in portfolio.positions.keys():
            performance = self.calculate_performance_over_cycles(symbol)
            if performance < self.config.underperformer_threshold:
                underperformers.append(symbol)
                logger.info(f"Underperformer detected: {symbol} ({performance:.2%} over {self.config.lookback_cycles} cycles)")
        
        return underperformers
    
    def find_top_performers(self, available_coins: List[str], exclude: List[str] = None) -> List[str]:
        """Find top performing cryptos from available coins"""
        exclude = exclude or []
        candidates = [coin for coin in available_coins if coin not in exclude]
        
        # Calculate performance for each candidate
        performances = {}
        for symbol in candidates:
            performance = self.calculate_performance_over_cycles(symbol)
            performances[symbol] = performance
        
        # Sort by performance (descending) and return top performers
        sorted_performers = sorted(performances.items(), key=lambda x: x[1], reverse=True)
        top_performers = [symbol for symbol, _ in sorted_performers]
        
        logger.info(f"Top performers: {[(s, f'{p:.2%}') for s, p in sorted_performers[:5]]}")
        return top_performers
    
    def check_historical_data_availability(self, required_coins: List[str]) -> Tuple[List[str], List[str]]:
        """
        Check which coins have sufficient historical data (simulation mode only)
        Returns: (available_coins, missing_coins)
        """
        if self.mode != EngineMode.SIMULATION:
            return required_coins, []
        
        available = []
        missing = []
        
        for coin in required_coins:
            prices = self.price_history.get(coin, [])
            if len(prices) >= self.config.lookback_cycles + 1:
                available.append(coin)
            else:
                missing.append(coin)
        
        return available, missing
    
    def check_stop_loss(self, portfolio: Portfolio) -> bool:
        """Check if stop-loss threshold is triggered"""
        return portfolio.performance_vs_initial < self.config.stop_loss_threshold
    
    def create_initial_portfolio(self, available_coins: List[str], current_prices: Dict[str, float], 
                               initial_reserve: float) -> RebalanceResult:
        """Create initial portfolio allocation"""
        logger.info(f"Creating initial portfolio with {initial_reserve} {self.config.reserve_asset}")
        
        # Get top 50 coins
        top_50 = self.get_top_50_coins(available_coins)
        
        # In simulation mode, check historical data availability
        if self.mode == EngineMode.SIMULATION:
            available_for_selection, missing = self.check_historical_data_availability(top_50)
            if len(available_for_selection) < self.config.portfolio_size:
                error_msg = (f"Simulation stopped at cycle 0: not enough cryptos with historical data. "
                           f"Need {self.config.portfolio_size}, found {len(available_for_selection)}. "
                           f"Missing historical data for: {', '.join(missing)}")
                return RebalanceResult(
                    success=False,
                    new_portfolio=Portfolio({}, initial_reserve, initial_reserve),
                    actions_taken=[],
                    error_message=error_msg,
                    simulation_blocked=True
                )
            top_50 = available_for_selection
        
        # Select top performers for initial allocation
        top_performers = self.find_top_performers(top_50)[:self.config.portfolio_size]
        
        # Calculate allocation per position
        allocation_per_position = initial_reserve / self.config.portfolio_size
        
        # Create positions
        positions = {}
        actions = []
        total_allocated = 0.0
        
        for symbol in top_performers:
            price = current_prices.get(symbol, 0)
            if price > 0:
                # Calculate quantity after trading fee
                gross_quantity = allocation_per_position / price
                fee = gross_quantity * self.config.trading_fee
                net_quantity = gross_quantity - fee
                
                if net_quantity > 0:
                    positions[symbol] = CryptoPosition(
                        symbol=symbol,
                        quantity=net_quantity,
                        entry_price=price,
                        current_price=price
                    )
                    total_allocated += allocation_per_position
                    actions.append(f"BUY {symbol}: {net_quantity:.6f} @ {price:.6f} (fee: {fee:.6f})")
        
        remaining_reserve = initial_reserve - total_allocated
        portfolio = Portfolio(positions, remaining_reserve, initial_reserve)
        
        logger.info(f"*** Initial portfolio created: {len(positions)} positions ***\n"
                   f"*** Allocated: {total_allocated:.2f}, Reserve: {remaining_reserve:.2f} ***")
        
        return RebalanceResult(
            success=True,
            new_portfolio=portfolio,
            actions_taken=actions
        )
    
    def rebalance_portfolio(self, current_portfolio: Portfolio, available_coins: List[str], 
                          current_prices: Dict[str, float]) -> RebalanceResult:
        """
        Rebalance portfolio by replacing underperformers with top performers
        """
        self.cycle_count += 1
        logger.info(f"*** Starting rebalance for cycle #{self.cycle_count} ***")
        
        # Update current prices in portfolio
        for symbol, position in current_portfolio.positions.items():
            position.current_price = current_prices.get(symbol, 0)
        
        # Check stop-loss
        if self.check_stop_loss(current_portfolio):
            logger.warning(f"*** STOP-LOSS TRIGGERED! Cycle #{self.cycle_count} ***\n"
                          f"*** Portfolio value: {current_portfolio.performance_vs_initial:.2%} of initial ***")
            
            # Liquidate all positions
            actions = []
            total_liquidated = 0.0
            
            for symbol, position in current_portfolio.positions.items():
                if position.current_price > 0:
                    # Calculate proceeds after trading fee
                    gross_proceeds = position.current_value
                    fee = gross_proceeds * self.config.trading_fee
                    net_proceeds = gross_proceeds - fee
                    total_liquidated += net_proceeds
                    actions.append(f"SELL {symbol}: {position.quantity:.6f} @ {position.current_price:.6f} "
                                 f"(proceeds: {net_proceeds:.6f}, fee: {fee:.6f})")
            
            final_reserve = current_portfolio.reserve + total_liquidated
            liquidated_portfolio = Portfolio({}, final_reserve, current_portfolio.initial_value)
            
            return RebalanceResult(
                success=True,
                new_portfolio=liquidated_portfolio,
                actions_taken=actions,
                stop_loss_triggered=True
            )
        
        # Skip rebalancing if not enough price history
        if self.cycle_count < self.config.lookback_cycles:
            logger.info(f"*** Skipping rebalance: only cycle #{self.cycle_count}, need {self.config.lookback_cycles} cycles ***")
            return RebalanceResult(
                success=True,
                new_portfolio=current_portfolio,
                actions_taken=[f"HOLD: Waiting for {self.config.lookback_cycles} cycles of price history"]
            )
        
        # Find underperformers
        underperformers = self.find_underperformers(current_portfolio)
        
        if not underperformers:
            logger.info(f"*** Cycle #{self.cycle_count}: No underperformers found, keeping current portfolio ***")
            return RebalanceResult(
                success=True,
                new_portfolio=current_portfolio,
                actions_taken=["HOLD: No underperformers detected"]
            )
        
        # Get top 50 coins for selection
        top_50 = self.get_top_50_coins(available_coins)
        
        # In simulation mode, check historical data availability
        if self.mode == EngineMode.SIMULATION:
            available_for_selection, missing = self.check_historical_data_availability(top_50)
            
            # Calculate how many positions we need to fill
            keepers = [s for s in current_portfolio.positions.keys() if s not in underperformers]
            positions_needed = len(underperformers)
            available_new_coins = [c for c in available_for_selection if c not in keepers]
            
            if len(available_new_coins) < positions_needed:
                error_msg = (f"*** Simulation stopped at cycle #{self.cycle_count}: not enough cryptos with historical data for rebalance ***\n"
                           f"*** Need {positions_needed} new positions, found {len(available_new_coins)} available ***\n"
                           f"*** Missing historical data for: {', '.join(missing)} ***")
                return RebalanceResult(
                    success=False,
                    new_portfolio=current_portfolio,
                    actions_taken=[],
                    error_message=error_msg,
                    simulation_blocked=True
                )
            
            top_50 = available_for_selection
        
        # Find replacement coins (exclude current keepers)
        current_keepers = [s for s in current_portfolio.positions.keys() if s not in underperformers]
        top_performers = self.find_top_performers(top_50, exclude=current_keepers)
        
        # Select replacements
        replacements = top_performers[:len(underperformers)]
        
        # Calculate total value to redistribute
        total_value_to_redistribute = 0.0
        actions = []
        
        # Sell underperformers
        for symbol in underperformers:
            position = current_portfolio.positions[symbol]
            if position.current_price > 0:
                gross_proceeds = position.current_value
                fee = gross_proceeds * self.config.trading_fee
                net_proceeds = gross_proceeds - fee
                total_value_to_redistribute += net_proceeds
                actions.append(f"SELL {symbol}: {position.quantity:.6f} @ {position.current_price:.6f} "
                             f"(proceeds: {net_proceeds:.6f}, fee: {fee:.6f})")
        
        # Create new portfolio
        new_positions = {}
        
        # Keep existing positions (not underperformers)
        for symbol, position in current_portfolio.positions.items():
            if symbol not in underperformers:
                new_positions[symbol] = position
        
        # Add new positions
        allocation_per_new_position = total_value_to_redistribute / len(replacements) if replacements else 0
        
        for symbol in replacements:
            price = current_prices.get(symbol, 0)
            if price > 0 and allocation_per_new_position > 0:
                gross_quantity = allocation_per_new_position / price
                fee = gross_quantity * self.config.trading_fee
                net_quantity = gross_quantity - fee
                
                if net_quantity > 0:
                    new_positions[symbol] = CryptoPosition(
                        symbol=symbol,
                        quantity=net_quantity,
                        entry_price=price,
                        current_price=price
                    )
                    actions.append(f"BUY {symbol}: {net_quantity:.6f} @ {price:.6f} (fee: {fee:.6f})")
        
        new_portfolio = Portfolio(new_positions, current_portfolio.reserve, current_portfolio.initial_value)
        
        logger.info(f"*** Cycle #{self.cycle_count} rebalance completed: replaced {len(underperformers)} underperformers with {len(replacements)} new positions ***")
        
        return RebalanceResult(
            success=True,
            new_portfolio=new_portfolio,
            actions_taken=actions
        )
    
    def get_portfolio_breakdown_for_popup(self, portfolio: Portfolio) -> Dict[str, Dict]:
        """
        Generate portfolio breakdown in the format expected by the frontend popup
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
        
        # If no positions, add placeholder
        if not breakdown:
            breakdown['NO_ASSETS'] = {
                'value': 0.0,
                'performance': 0.0,
                'quantity': 0.0,
                'price': 0.0,
                'entry_price': 0.0
            }
        
        return breakdown
    
    def run_cycle(self, current_portfolio: Portfolio, available_coins: List[str], 
                  current_prices: Dict[str, float]) -> RebalanceResult:
        """
        Run a complete trading cycle
        """
        # Update price history
        self.update_price_history(current_prices)
        
        # Perform rebalancing
        if self.cycle_count == 0:
            # Initial portfolio creation
            return self.create_initial_portfolio(available_coins, current_prices, current_portfolio.reserve)
        else:
            # Regular rebalancing
            return self.rebalance_portfolio(current_portfolio, available_coins, current_prices)


# Example usage and testing
if __name__ == "__main__":
    # Test configuration
    config = EngineConfig.from_env()
    
    # Test simulation mode
    sim_engine = UnifiedTradingEngine(EngineMode.SIMULATION, config)
    
    # Mock data for testing
    available_coins = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'DOT', 'MATIC', 'AVAX', 'LINK', 'UNI']
    current_prices = {coin: 100.0 + i * 10 for i, coin in enumerate(available_coins)}
    
    # Create initial portfolio
    initial_portfolio = Portfolio({}, 1000.0, 1000.0)
    
    print("Testing Unified Trading Engine")
    print("=" * 50)
    
    result = sim_engine.run_cycle(initial_portfolio, available_coins, current_prices)
    print(f"Initial allocation success: {result.success}")
    print(f"Actions: {result.actions_taken}")
    print(f"Portfolio value: {result.new_portfolio.portfolio_value:.2f}")
    print(f"Reserve: {result.new_portfolio.reserve:.2f}")