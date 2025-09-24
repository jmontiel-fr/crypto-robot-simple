#!/usr/bin/env python3
"""
Daily Rebalance Volatile Strategy with USDC Protection

This strategy implements:
- Daily rebalancing across 10 optimized cryptocurrencies
- Volatility-based allocation adjustments
- USDC protection during bear markets
- Enhanced risk management
"""

import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import json
import random

logger = logging.getLogger(__name__)

class DailyRebalanceVolatileStrategy:
    """Daily rebalancing strategy with volatility optimization and USDC protection"""
    
    def __init__(self, realistic_mode: bool = True):
        self.strategy_name = "daily_rebalance_volatile"
        self.strategy_version = "v2.2"
        self.realistic_mode = realistic_mode
        
        # Strategy configuration
        self.target_cryptos = 10
        self.rebalance_frequency = 24  # hours
        
        # Volatility modes
        self.volatility_mode = "adaptive"  # low, average, high, adaptive
        
        # Enhanced USDC protection settings
        self.usdc_protection_enabled = True
        self.bear_market_threshold = -0.08  # -8% triggers USDC protection (more sensitive)
        self.consecutive_loss_threshold = 2  # 2 consecutive losses triggers protection (faster response)
        self.usdc_exit_threshold = 0.03     # +3% market recovery to exit USDC (quicker re-entry)
        
        # Advanced protection triggers
        self.volatility_threshold = 0.06    # High volatility trigger (6% daily volatility)
        self.cumulative_loss_threshold = -0.12  # -12% cumulative loss over 5 days
        self.market_fear_threshold = 0.8    # Market fear index (simulated)
        
        # Enhanced performance tracking
        self.recent_performance = []
        self.consecutive_losses = 0
        self.in_usdc_protection = False
        self.volatility_history = []
        self.protection_cooldown = 0  # Prevent rapid switching
        self.market_sentiment_score = 0.5  # 0 = extreme fear, 1 = extreme greed
        
        # Optimized cryptocurrency selection (based on analysis)
        self.optimized_cryptos = [
            'BTC', 'ETH', 'BNB', 'SOL', 'ADA', 
            'DOT', 'AVAX', 'MATIC', 'LINK', 'UNI'
        ]
        
        logger.info(f"✅ {self.strategy_name} v{self.strategy_version} initialized")
        logger.info(f"   Volatility mode: {self.volatility_mode}")
        logger.info(f"   USDC protection: {'enabled' if self.usdc_protection_enabled else 'disabled'}")
        logger.info(f"   Target cryptos: {self.target_cryptos}")
    
    def should_activate_usdc_protection(self, current_performance: float, 
                                       recent_losses: int, market_data: Dict = None) -> bool:
        """Enhanced USDC protection with multiple intelligent triggers"""
        
        if not self.usdc_protection_enabled or self.protection_cooldown > 0:
            return False
        
        protection_signals = []
        
        # 1. Significant portfolio decline (enhanced sensitivity)
        if current_performance <= self.bear_market_threshold:
            protection_signals.append(f"Portfolio decline: {current_performance:.1%}")
        
        # 2. Consecutive losses (faster response)
        if recent_losses >= self.consecutive_loss_threshold:
            protection_signals.append(f"Consecutive losses: {recent_losses}")
        
        # 3. High volatility detection
        if len(self.volatility_history) >= 3:
            recent_volatility = sum(self.volatility_history[-3:]) / 3
            if recent_volatility > self.volatility_threshold:
                protection_signals.append(f"High volatility: {recent_volatility:.1%}")
        
        # 4. Cumulative loss over period
        if len(self.recent_performance) >= 5:
            cumulative_loss = sum(self.recent_performance[-5:])
            if cumulative_loss <= self.cumulative_loss_threshold:
                protection_signals.append(f"Cumulative 5-day loss: {cumulative_loss:.1%}")
        
        # 5. Market sentiment analysis (simulated)
        self._update_market_sentiment(current_performance, market_data)
        if self.market_sentiment_score < 0.3:  # Extreme fear
            protection_signals.append(f"Market fear: {self.market_sentiment_score:.2f}")
        
        # 6. Technical indicator: Sharp decline acceleration
        if len(self.recent_performance) >= 3:
            recent_trend = self.recent_performance[-1] - self.recent_performance[-3]
            if recent_trend < -0.05:  # Accelerating decline
                protection_signals.append(f"Accelerating decline: {recent_trend:.1%}")
        
        # Activate protection if multiple signals present
        if len(protection_signals) >= 2:  # Require at least 2 signals for activation
            logger.info(f"🛡️ USDC Protection ACTIVATED by multiple signals:")
            for signal in protection_signals:
                logger.info(f"   • {signal}")
            return True
        elif len(protection_signals) == 1 and current_performance <= -0.12:  # Single strong signal
            logger.info(f"🛡️ USDC Protection ACTIVATED by strong signal: {protection_signals[0]}")
            return True
        
        return False
    
    def should_exit_usdc_protection(self, market_recovery: float, market_data: Dict = None) -> bool:
        """Enhanced USDC protection exit with intelligent conditions"""
        
        if not self.in_usdc_protection:
            return False
        
        exit_signals = []
        
        # 1. Market recovery threshold
        if market_recovery >= self.usdc_exit_threshold:
            exit_signals.append(f"Market recovery: {market_recovery:.1%}")
        
        # 2. Sustained positive performance
        if len(self.recent_performance) >= 2:
            recent_positive = all(p > 0 for p in self.recent_performance[-2:])
            if recent_positive:
                exit_signals.append("2 consecutive positive days")
        
        # 3. Volatility normalization
        if len(self.volatility_history) >= 3:
            recent_volatility = sum(self.volatility_history[-3:]) / 3
            if recent_volatility < 0.03:  # Low volatility
                exit_signals.append(f"Volatility normalized: {recent_volatility:.1%}")
        
        # 4. Market sentiment improvement
        if self.market_sentiment_score > 0.6:  # Optimism returning
            exit_signals.append(f"Market sentiment improved: {self.market_sentiment_score:.2f}")
        
        # 5. Technical momentum shift
        if len(self.recent_performance) >= 3:
            momentum = sum(self.recent_performance[-3:])
            if momentum > 0.02:  # Positive 3-day momentum
                exit_signals.append(f"Positive momentum: {momentum:.1%}")
        
        # Exit if multiple positive signals or strong single signal
        if len(exit_signals) >= 2:
            logger.info(f"🚀 EXITING USDC Protection - Multiple positive signals:")
            for signal in exit_signals:
                logger.info(f"   • {signal}")
            self.protection_cooldown = 3  # 3-day cooldown to prevent rapid switching
            return True
        elif market_recovery >= 0.06:  # Strong single recovery signal
            logger.info(f"🚀 EXITING USDC Protection - Strong recovery: {market_recovery:.1%}")
            self.protection_cooldown = 2  # Shorter cooldown for strong signals
            return True
        
        return False
    
    def _update_market_sentiment(self, current_performance: float, market_data: Dict = None):
        """Update market sentiment score based on performance and market data"""
        
        # Base sentiment on recent performance
        if current_performance > 0.05:  # Strong positive
            sentiment_change = 0.1
        elif current_performance > 0.02:  # Moderate positive
            sentiment_change = 0.05
        elif current_performance > -0.02:  # Neutral
            sentiment_change = 0.0
        elif current_performance > -0.05:  # Moderate negative
            sentiment_change = -0.05
        else:  # Strong negative
            sentiment_change = -0.1
        
        # Apply momentum from consecutive performance
        if len(self.recent_performance) >= 3:
            recent_trend = sum(self.recent_performance[-3:])
            if recent_trend > 0.06:  # Strong positive trend
                sentiment_change += 0.05
            elif recent_trend < -0.06:  # Strong negative trend
                sentiment_change -= 0.05
        
        # Update sentiment with bounds
        self.market_sentiment_score = max(0.0, min(1.0, self.market_sentiment_score + sentiment_change))
    
    def _update_performance_tracking(self, daily_return: float, volatility: float = None):
        """Update performance and volatility tracking"""
        
        # Update performance history (keep last 10 days)
        self.recent_performance.append(daily_return)
        if len(self.recent_performance) > 10:
            self.recent_performance.pop(0)
        
        # Update volatility history if provided
        if volatility is not None:
            self.volatility_history.append(volatility)
            if len(self.volatility_history) > 10:
                self.volatility_history.pop(0)
        
        # Update consecutive losses counter
        if daily_return < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
        
        # Decrease protection cooldown
        if self.protection_cooldown > 0:
            self.protection_cooldown -= 1
    
    def execute_daily_rebalance(self, current_date: datetime, current_capital: float, 
                              simulation_mode: bool = True, 
                              market_data: Dict = None) -> Dict:
        """Execute daily rebalancing with USDC protection"""
        
        try:
            # Handle None market_data
            if market_data is None:
                market_data = {}
            
            # Update performance history FIRST
            self.recent_performance.append(current_capital)
            if len(self.recent_performance) > 30:  # Keep last 30 days
                self.recent_performance.pop(0)
            
            # Calculate current performance (compare to PREVIOUS day, not oldest day)
            if len(self.recent_performance) >= 2:
                # Compare to yesterday (recent_performance[-2])
                yesterday_capital = self.recent_performance[-2]
                if yesterday_capital > 0:
                    current_performance = (current_capital / yesterday_capital) - 1
                    daily_change = current_performance
                else:
                    current_performance = 0.0
                    daily_change = 0.0
            else:
                current_performance = 0.0
                daily_change = 0.0
            
            # Track consecutive losses (based on daily change)
            if daily_change < 0:
                self.consecutive_losses += 1
                logger.info(f"📉 Daily loss: {daily_change:.2%}, consecutive losses: {self.consecutive_losses}")
            else:
                if self.consecutive_losses > 0:
                    logger.info(f"📈 Daily gain: {daily_change:.2%}, resetting consecutive losses from {self.consecutive_losses}")
                self.consecutive_losses = 0
            
            # Calculate overall performance (from start)
            if len(self.recent_performance) > 1 and self.recent_performance[0] > 0:
                overall_performance = (current_capital / self.recent_performance[0]) - 1
            else:
                overall_performance = 0.0
            
            # Calculate current volatility for enhanced protection
            current_volatility = 0.0
            if market_data:
                # Estimate volatility from recent price movements
                btc_prices = market_data.get('BTC', [])
                if len(btc_prices) >= 2 and btc_prices[-2] != 0:
                    recent_change = abs(btc_prices[-1] / btc_prices[-2] - 1)
                    current_volatility = recent_change
            
            # Update performance tracking
            self._update_performance_tracking(overall_performance, current_volatility)
            
            # Check for enhanced USDC protection activation
            should_protect = self.should_activate_usdc_protection(
                overall_performance, self.consecutive_losses, market_data
            )
            
            # Log protection check
            if self.consecutive_losses >= 2:  # Log when getting close to threshold
                logger.info(f"🛡️ Protection check: overall_perf={overall_performance:.2%}, consecutive_losses={self.consecutive_losses}, threshold={self.consecutive_loss_threshold}")
            
            if should_protect and not self.in_usdc_protection:
                logger.info(f"🛡️ ACTIVATING USDC PROTECTION")
                self.in_usdc_protection = True
                return self._execute_usdc_protection(current_capital, current_date)
            
            # Check for USDC protection exit
            if self.in_usdc_protection:
                # Use daily change for recovery detection
                market_recovery = daily_change if daily_change > 0 else 0
                should_exit = self.should_exit_usdc_protection(market_recovery, market_data)
                
                if should_exit:
                    self.in_usdc_protection = False
                    logger.info(f"🚀 EXITING USDC PROTECTION - Resuming crypto trading")
                else:
                    return self._execute_usdc_protection(current_capital, current_date)
            
            # Normal crypto rebalancing
            return self._execute_crypto_rebalancing(current_capital, market_data, 
                                                  simulation_mode, current_date)
            
        except Exception as e:
            logger.error(f"❌ Error in daily rebalance execution: {e}")
            # Fallback to basic rebalancing
            return self._execute_crypto_rebalancing(current_capital, market_data, 
                                                  simulation_mode, current_date)
    
    def _execute_usdc_protection(self, current_capital: float, 
                               current_date: datetime = None) -> Dict:
        """Execute USDC protection mode"""
        
        logger.info(f"🛡️ USDC PROTECTION MODE: Converting portfolio to stablecoin")
        
        return {
            'success': True,
            'allocations': {'USDC': 1.0},  # 100% USDC
            'actions_taken': ['USDC_PROTECTION: Converted to stablecoin for market protection'],
            'total_value': current_capital * 0.999,  # Small conversion fee
            'portfolio_breakdown': {'USDC': current_capital * 0.999},
            'trading_costs': current_capital * 0.001,
            'protection_mode': True,
            'reason': f'USDC protection active - consecutive losses: {self.consecutive_losses}'
        }
    
    def _execute_crypto_rebalancing(self, current_capital: float, market_data: Dict,
                                  simulation_mode: bool = True, 
                                  current_date: datetime = None) -> Dict:
        """Execute normal crypto rebalancing"""
        
        # Smart momentum-based allocation with risk adjustment
        allocations = {}
        portfolio_breakdown = {}
        
        # Calculate momentum scores for each crypto
        momentum_scores = {}
        total_momentum = 0
        
        for crypto in self.optimized_cryptos:
            if crypto in market_data and len(market_data[crypto]) >= 7:
                # Use our enhanced momentum calculation
                from src.daily_rebalance_simulation_engine import EnhancedCoinSelector
                selector = EnhancedCoinSelector()
                momentum_score = selector.calculate_momentum_score(market_data[crypto])
                
                # Normalize and ensure positive weights
                momentum_scores[crypto] = max(0.1, 1.0 + momentum_score)  # Minimum 10% weight
                total_momentum += momentum_scores[crypto]
            else:
                momentum_scores[crypto] = 1.0
                total_momentum += 1.0
        
        # Calculate risk-adjusted allocations
        min_allocation = 0.05  # Minimum 5% per asset
        max_allocation = 0.25  # Maximum 25% per asset
        
        for crypto in self.optimized_cryptos:
            # Base allocation from momentum
            if total_momentum > 0:
                momentum_weight = momentum_scores[crypto] / total_momentum
            else:
                momentum_weight = 1.0 / len(self.optimized_cryptos)  # Equal weight fallback
            
            # Apply min/max constraints
            allocation = max(min_allocation, min(max_allocation, momentum_weight))
            
            allocations[crypto] = allocation
            portfolio_breakdown[crypto] = current_capital * allocation
        
        # Normalize to ensure total = 1.0
        total_allocation = sum(allocations.values())
        if total_allocation > 0:
            for crypto in allocations:
                allocations[crypto] /= total_allocation
                portfolio_breakdown[crypto] = current_capital * allocations[crypto]
        else:
            # Fallback to equal allocation
            equal_weight = 1.0 / len(self.optimized_cryptos)
            for crypto in allocations:
                allocations[crypto] = equal_weight
                portfolio_breakdown[crypto] = current_capital * equal_weight
        
        # Apply small trading costs
        trading_costs = current_capital * 0.001  # 0.1% trading costs
        total_value = current_capital - trading_costs
        
        return {
            'success': True,
            'allocations': allocations,
            'actions_taken': ['CRYPTO_REBALANCE: Rebalanced across optimized cryptocurrencies'],
            'total_value': total_value,
            'portfolio_breakdown': portfolio_breakdown,
            'trading_costs': trading_costs,
            'protection_mode': False,
            'reason': f'Normal crypto trading - consecutive losses: {self.consecutive_losses}'
        }
    
    def get_performance_summary(self) -> Dict:
        """Get overall performance summary for compatibility with simulation engine"""
        
        return {
            'total_executions': len(self.recent_performance),
            'success_rate': 100.0,  # Assume all executions successful
            'total_return': 0.0,  # Will be calculated by simulation engine
            'average_return': 0.0,
            'total_trading_costs': 0.0,
            'volatility_modes_used': [self.volatility_mode],
            'usdc_protection_cycles': sum(1 for _ in range(len(self.recent_performance)) if self.in_usdc_protection),
            'consecutive_losses': self.consecutive_losses,
            'protection_active': self.in_usdc_protection
        }