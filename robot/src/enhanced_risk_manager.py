"""
Enhanced Risk Manager for Crypto Trading Robot

Implements volatility-based position sizing, dynamic stop-loss, and market filtering
to improve the 51% success rate identified in simulation analysis.
"""

import logging
import requests
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import pandas as pd

logger = logging.getLogger(__name__)

class EnhancedRiskManager:
    """
    Advanced risk management system with volatility-based position sizing
    and dynamic stop-loss adjustment
    """
    
    def __init__(self, config):
        self.config = config
        self.volatility_cache = {}
        self.market_cap_cache = {}
        self.volume_cache = {}
        
        # Risk parameters (can be tuned based on backtesting)
        self.max_position_size = 0.15  # 15% max per position
        self.min_position_size = 0.05  # 5% min per position
        self.volatility_lookback = 14   # 14 days for volatility calculation
        self.min_market_cap_rank = 50  # Top 50 coins by market cap
        self.min_daily_volume = 10000000  # $10M minimum daily volume
        
        logger.info("Enhanced Risk Manager initialized")
    
    def get_market_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Fetch market data for risk analysis
        """
        market_data = {}
        
        try:
            # Get market cap rankings from CoinGecko (free API)
            url = "https://api.coingecko.com/api/v3/coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': 100,
                'page': 1,
                'sparkline': False
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # Create symbol mapping (CoinGecko uses different symbols)
                symbol_map = {
                    'BTC': 'bitcoin', 'ETH': 'ethereum', 'BNB': 'binancecoin',
                    'ADA': 'cardano', 'SOL': 'solana', 'DOT': 'polkadot',
                    'MATIC': 'polygon', 'AVAX': 'avalanche-2', 'LINK': 'chainlink',
                    'UNI': 'uniswap', 'ATOM': 'cosmos', 'XRP': 'ripple',
                    'LTC': 'litecoin', 'BCH': 'bitcoin-cash', 'ALGO': 'algorand'
                }
                
                for coin in data:
                    # Find matching symbol
                    symbol = None
                    for s, cg_id in symbol_map.items():
                        if coin['id'] == cg_id:
                            symbol = s
                            break
                    
                    if symbol and symbol in symbols:
                        market_data[symbol] = {
                            'market_cap_rank': coin.get('market_cap_rank', 999),
                            'market_cap': coin.get('market_cap', 0),
                            'volume_24h': coin.get('total_volume', 0),
                            'price_change_24h': coin.get('price_change_percentage_24h', 0),
                            'current_price': coin.get('current_price', 0)
                        }
                
                logger.info(f"Fetched market data for {len(market_data)} coins")
                
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
        
        return market_data
    
    def calculate_volatility(self, symbol: str, prices: List[float]) -> float:
        """
        Calculate 14-day volatility for a symbol
        """
        if len(prices) < 2:
            return 0.5  # Default high volatility for unknown coins
        
        try:
            # Calculate daily returns
            returns = []
            for i in range(1, len(prices)):
                if prices[i-1] > 0:
                    returns.append((prices[i] - prices[i-1]) / prices[i-1])
            
            if len(returns) < 2:
                return 0.5
            
            # Calculate standard deviation (volatility)
            volatility = np.std(returns) * np.sqrt(365)  # Annualized
            
            # Cache the result
            self.volatility_cache[symbol] = volatility
            
            return volatility
            
        except Exception as e:
            logger.error(f"Error calculating volatility for {symbol}: {e}")
            return 0.5
    
    def filter_coins_by_market_criteria(self, symbols: List[str]) -> List[str]:
        """
        Filter coins based on market cap rank and volume
        """
        market_data = self.get_market_data(symbols)
        filtered_symbols = []
        
        for symbol in symbols:
            data = market_data.get(symbol, {})
            
            # Check market cap rank
            market_cap_rank = data.get('market_cap_rank', 999)
            if market_cap_rank > self.min_market_cap_rank:
                logger.debug(f"Filtered out {symbol}: market cap rank {market_cap_rank}")
                continue
            
            # Check daily volume
            volume_24h = data.get('volume_24h', 0)
            if volume_24h < self.min_daily_volume:
                logger.debug(f"Filtered out {symbol}: low volume ${volume_24h:,.0f}")
                continue
            
            filtered_symbols.append(symbol)
        
        logger.info(f"Filtered {len(symbols)} coins to {len(filtered_symbols)} based on market criteria")
        return filtered_symbols
    
    def calculate_position_sizes(self, symbols: List[str], total_capital: float, 
                               current_prices: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate optimal position sizes based on volatility and risk
        """
        if not symbols:
            return {}
        
        # Get market data for risk assessment
        market_data = self.get_market_data(symbols)
        
        # Calculate volatility-adjusted weights
        weights = {}
        total_weight = 0
        
        for symbol in symbols:
            # Get volatility (use cached if available)
            volatility = self.volatility_cache.get(symbol, 0.3)  # Default 30% volatility
            
            # Calculate inverse volatility weight (lower volatility = higher weight)
            # Add minimum volatility to avoid division by zero
            inv_vol_weight = 1 / max(volatility, 0.1)
            
            # Apply market cap boost (higher market cap = slightly higher weight)
            data = market_data.get(symbol, {})
            market_cap_rank = data.get('market_cap_rank', 50)
            market_cap_boost = max(0.5, (51 - market_cap_rank) / 50)  # 0.5 to 1.0
            
            # Calculate final weight
            weight = inv_vol_weight * market_cap_boost
            weights[symbol] = weight
            total_weight += weight
        
        # Normalize weights and apply position size limits
        position_sizes = {}
        
        for symbol in symbols:
            if total_weight > 0:
                normalized_weight = weights[symbol] / total_weight
                
                # Apply min/max position size limits
                position_size = max(self.min_position_size, 
                                  min(self.max_position_size, normalized_weight))
                
                position_sizes[symbol] = position_size * total_capital
            else:
                # Equal weight fallback
                position_sizes[symbol] = (total_capital / len(symbols)) * 0.8  # 80% allocation
        
        logger.info(f"Calculated position sizes for {len(symbols)} coins")
        return position_sizes
    
    def calculate_dynamic_stop_loss(self, symbol: str, entry_price: float, 
                                  base_stop_loss: float = 0.95) -> float:
        """
        Calculate dynamic stop-loss based on coin volatility
        """
        # Get volatility for the symbol
        volatility = self.volatility_cache.get(symbol, 0.3)
        
        # Adjust stop-loss based on volatility
        # Higher volatility = looser stop-loss to avoid false triggers
        volatility_adjustment = min(0.1, volatility * 0.2)  # Max 10% adjustment
        
        # Calculate adjusted stop-loss
        adjusted_stop_loss = base_stop_loss - volatility_adjustment
        
        # Ensure stop-loss is within reasonable bounds (85% to 98%)
        adjusted_stop_loss = max(0.85, min(0.98, adjusted_stop_loss))
        
        logger.debug(f"Dynamic stop-loss for {symbol}: {adjusted_stop_loss:.3f} "
                    f"(volatility: {volatility:.3f})")
        
        return adjusted_stop_loss
    
    def assess_portfolio_risk(self, portfolio: Dict[str, Dict]) -> Dict[str, float]:
        """
        Assess overall portfolio risk metrics
        """
        risk_metrics = {
            'total_positions': len(portfolio),
            'max_position_pct': 0,
            'avg_volatility': 0,
            'concentration_risk': 0,
            'liquidity_risk': 0
        }
        
        if not portfolio:
            return risk_metrics
        
        total_value = sum(pos.get('value', 0) for pos in portfolio.values())
        volatilities = []
        
        for symbol, position in portfolio.items():
            position_value = position.get('value', 0)
            
            if total_value > 0:
                position_pct = position_value / total_value
                risk_metrics['max_position_pct'] = max(risk_metrics['max_position_pct'], 
                                                     position_pct)
            
            # Get volatility
            volatility = self.volatility_cache.get(symbol, 0.3)
            volatilities.append(volatility)
        
        # Calculate average volatility
        if volatilities:
            risk_metrics['avg_volatility'] = np.mean(volatilities)
        
        # Calculate concentration risk (Herfindahl index)
        if total_value > 0:
            position_squares = sum((pos.get('value', 0) / total_value) ** 2 
                                 for pos in portfolio.values())
            risk_metrics['concentration_risk'] = position_squares
        
        logger.info(f"Portfolio risk assessment: {risk_metrics}")
        return risk_metrics
    
    def should_reduce_trading(self, recent_performance: List[float]) -> bool:
        """
        Determine if trading frequency should be reduced based on recent losses
        """
        if len(recent_performance) < 3:
            return False
        
        # Check for consecutive losses
        consecutive_losses = 0
        for perf in reversed(recent_performance[-5:]):  # Last 5 trades
            if perf < 0:
                consecutive_losses += 1
            else:
                break
        
        # Reduce trading after 3 consecutive losses
        if consecutive_losses >= 3:
            logger.warning(f"Reducing trading frequency due to {consecutive_losses} consecutive losses")
            return True
        
        # Check for significant drawdown
        if len(recent_performance) >= 10:
            recent_avg = np.mean(recent_performance[-10:])
            if recent_avg < -0.05:  # -5% average over last 10 trades
                logger.warning(f"Reducing trading frequency due to poor recent performance: {recent_avg:.2%}")
                return True
        
        return False
    
    def get_risk_adjusted_allocation(self, symbols: List[str], total_capital: float,
                                   current_prices: Dict[str, float]) -> Dict[str, Dict]:
        """
        Main method to get risk-adjusted portfolio allocation
        """
        # Step 1: Filter coins by market criteria
        filtered_symbols = self.filter_coins_by_market_criteria(symbols)
        
        if not filtered_symbols:
            logger.warning("No symbols passed market criteria filters")
            return {}
        
        # Step 2: Calculate position sizes
        position_sizes = self.calculate_position_sizes(filtered_symbols, total_capital, current_prices)
        
        # Step 3: Create allocation with risk parameters
        allocation = {}
        
        for symbol in filtered_symbols:
            if symbol in current_prices and symbol in position_sizes:
                price = current_prices[symbol]
                position_value = position_sizes[symbol]
                quantity = position_value / price if price > 0 else 0
                
                # Calculate dynamic stop-loss
                stop_loss = self.calculate_dynamic_stop_loss(symbol, price)
                
                allocation[symbol] = {
                    'quantity': quantity,
                    'value': position_value,
                    'entry_price': price,
                    'stop_loss_threshold': stop_loss,
                    'volatility': self.volatility_cache.get(symbol, 0.3)
                }
        
        logger.info(f"Generated risk-adjusted allocation for {len(allocation)} coins")
        return allocation

# Example usage and testing
if __name__ == "__main__":
    import os
    from dataclasses import dataclass
    
    @dataclass
    class MockConfig:
        portfolio_size: int = 10
        trading_fee: float = 0.001
        stop_loss_threshold: float = 0.95
    
    # Test the enhanced risk manager
    config = MockConfig()
    risk_manager = EnhancedRiskManager(config)
    
    # Test symbols
    test_symbols = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'DOT', 'MATIC', 'AVAX', 'LINK', 'UNI']
    test_prices = {symbol: 100.0 + i * 10 for i, symbol in enumerate(test_symbols)}
    
    print("Testing Enhanced Risk Manager")
    print("=" * 40)
    
    # Test market filtering
    filtered = risk_manager.filter_coins_by_market_criteria(test_symbols)
    print(f"Filtered symbols: {filtered}")
    
    # Test position sizing
    allocation = risk_manager.get_risk_adjusted_allocation(filtered, 1000.0, test_prices)
    
    print(f"\nRisk-adjusted allocation:")
    for symbol, data in allocation.items():
        print(f"  {symbol}: ${data['value']:.2f} ({data['quantity']:.6f} coins, "
              f"stop-loss: {data['stop_loss_threshold']:.3f})")
    
    # Test risk assessment
    portfolio = {symbol: {'value': data['value']} for symbol, data in allocation.items()}
    risk_metrics = risk_manager.assess_portfolio_risk(portfolio)
    print(f"\nRisk metrics: {risk_metrics}")