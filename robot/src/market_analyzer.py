"""
Market Analyzer with Technical Indicators

Implements RSI, MACD, moving averages, and momentum analysis
to improve coin selection and timing decisions.
"""

import logging
import requests
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MarketAnalyzer:
    """
    Advanced market analysis with technical indicators and momentum scoring
    """
    
    def __init__(self):
        self.price_cache = {}
        self.indicator_cache = {}
        
        # Technical analysis parameters
        self.rsi_period = 14
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.sma_short = 7
        self.sma_long = 21
        
        logger.info("Market Analyzer initialized")
    
    def fetch_historical_prices(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """
        Fetch historical price data for technical analysis
        """
        try:
            # Use Binance API for historical data
            url = "https://api.binance.com/api/v3/klines"
            params = {
                'symbol': f"{symbol}USDT",
                'interval': '1d',
                'limit': days
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                if data:
                    df = pd.DataFrame(data, columns=[
                        'timestamp', 'open', 'high', 'low', 'close', 'volume',
                        'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                        'taker_buy_quote', 'ignore'
                    ])
                    
                    # Convert to proper data types
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    for col in ['open', 'high', 'low', 'close', 'volume']:
                        df[col] = pd.to_numeric(df[col])
                    
                    # Cache the data
                    self.price_cache[symbol] = df
                    
                    logger.debug(f"Fetched {len(df)} price points for {symbol}")
                    return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.error(f"Error fetching historical prices for {symbol}: {e}")
        
        return pd.DataFrame()
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index (RSI)
        """
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return pd.Series([50] * len(prices))  # Neutral RSI
    
    def calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """
        Calculate MACD (Moving Average Convergence Divergence)
        """
        try:
            ema_fast = prices.ewm(span=fast).mean()
            ema_slow = prices.ewm(span=slow).mean()
            
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal).mean()
            histogram = macd_line - signal_line
            
            return {
                'macd': macd_line,
                'signal': signal_line,
                'histogram': histogram
            }
        except Exception as e:
            logger.error(f"Error calculating MACD: {e}")
            return {
                'macd': pd.Series([0] * len(prices)),
                'signal': pd.Series([0] * len(prices)),
                'histogram': pd.Series([0] * len(prices))
            }
    
    def calculate_moving_averages(self, prices: pd.Series, short: int = 7, long: int = 21) -> Dict[str, pd.Series]:
        """
        Calculate Simple Moving Averages
        """
        try:
            sma_short = prices.rolling(window=short).mean()
            sma_long = prices.rolling(window=long).mean()
            
            return {
                'sma_short': sma_short,
                'sma_long': sma_long
            }
        except Exception as e:
            logger.error(f"Error calculating moving averages: {e}")
            return {
                'sma_short': prices,
                'sma_long': prices
            }
    
    def calculate_momentum_score(self, symbol: str) -> float:
        """
        Calculate comprehensive momentum score (0-100)
        """
        df = self.fetch_historical_prices(symbol, 30)
        
        if df.empty or len(df) < 21:
            return 50  # Neutral score for insufficient data
        
        try:
            prices = df['close']
            
            # Calculate technical indicators
            rsi = self.calculate_rsi(prices, self.rsi_period)
            macd_data = self.calculate_macd(prices, self.macd_fast, self.macd_slow, self.macd_signal)
            ma_data = self.calculate_moving_averages(prices, self.sma_short, self.sma_long)
            
            # Get latest values
            current_price = prices.iloc[-1]
            current_rsi = rsi.iloc[-1] if not rsi.empty else 50
            current_macd = macd_data['macd'].iloc[-1] if not macd_data['macd'].empty else 0
            current_signal = macd_data['signal'].iloc[-1] if not macd_data['signal'].empty else 0
            current_sma_short = ma_data['sma_short'].iloc[-1] if not ma_data['sma_short'].empty else current_price
            current_sma_long = ma_data['sma_long'].iloc[-1] if not ma_data['sma_long'].empty else current_price
            
            # Calculate momentum components
            momentum_score = 0
            
            # 1. Price momentum (25 points)
            price_change_7d = (current_price / prices.iloc[-8] - 1) * 100 if len(prices) >= 8 else 0
            price_momentum = min(25, max(0, (price_change_7d + 10) * 1.25))  # -10% to +10% -> 0 to 25
            momentum_score += price_momentum
            
            # 2. RSI momentum (25 points)
            if 30 <= current_rsi <= 70:  # Not oversold/overbought
                rsi_momentum = 25
            elif current_rsi > 70:  # Overbought (negative)
                rsi_momentum = max(0, 25 - (current_rsi - 70) * 2)
            else:  # Oversold (slightly positive)
                rsi_momentum = min(25, 15 + (30 - current_rsi) * 0.5)
            momentum_score += rsi_momentum
            
            # 3. MACD momentum (25 points)
            if current_macd > current_signal:  # Bullish crossover
                macd_momentum = 25
            else:  # Bearish
                macd_momentum = 10
            momentum_score += macd_momentum
            
            # 4. Moving average momentum (25 points)
            if current_price > current_sma_short > current_sma_long:  # Strong uptrend
                ma_momentum = 25
            elif current_price > current_sma_short:  # Mild uptrend
                ma_momentum = 20
            elif current_price > current_sma_long:  # Sideways above long MA
                ma_momentum = 15
            else:  # Downtrend
                ma_momentum = 5
            momentum_score += ma_momentum
            
            # Ensure score is between 0 and 100
            momentum_score = max(0, min(100, momentum_score))
            
            # Cache the result
            self.indicator_cache[symbol] = {
                'momentum_score': momentum_score,
                'rsi': current_rsi,
                'macd': current_macd,
                'signal': current_signal,
                'price_change_7d': price_change_7d,
                'timestamp': datetime.now()
            }
            
            logger.debug(f"Momentum score for {symbol}: {momentum_score:.1f}")
            return momentum_score
            
        except Exception as e:
            logger.error(f"Error calculating momentum score for {symbol}: {e}")
            return 50
    
    def get_market_sentiment(self) -> Dict[str, float]:
        """
        Get overall market sentiment indicators
        """
        sentiment = {
            'fear_greed_index': 50,  # Neutral default
            'btc_dominance': 50,
            'market_trend': 0  # -1 bearish, 0 neutral, 1 bullish
        }
        
        try:
            # Try to get Fear & Greed Index (alternative.me API)
            url = "https://api.alternative.me/fng/"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and len(data['data']) > 0:
                    sentiment['fear_greed_index'] = float(data['data'][0]['value'])
                    logger.debug(f"Fear & Greed Index: {sentiment['fear_greed_index']}")
            
        except Exception as e:
            logger.warning(f"Could not fetch Fear & Greed Index: {e}")
        
        try:
            # Get BTC dominance from CoinGecko
            url = "https://api.coingecko.com/api/v3/global"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'market_cap_percentage' in data['data']:
                    btc_dominance = data['data']['market_cap_percentage'].get('btc', 50)
                    sentiment['btc_dominance'] = btc_dominance
                    logger.debug(f"BTC Dominance: {btc_dominance:.1f}%")
            
        except Exception as e:
            logger.warning(f"Could not fetch BTC dominance: {e}")
        
        # Determine market trend based on sentiment
        if sentiment['fear_greed_index'] > 60:
            sentiment['market_trend'] = 1  # Bullish
        elif sentiment['fear_greed_index'] < 40:
            sentiment['market_trend'] = -1  # Bearish
        else:
            sentiment['market_trend'] = 0  # Neutral
        
        return sentiment
    
    def rank_coins_by_momentum(self, symbols: List[str]) -> List[Tuple[str, float]]:
        """
        Rank coins by momentum score
        """
        coin_scores = []
        
        for symbol in symbols:
            score = self.calculate_momentum_score(symbol)
            coin_scores.append((symbol, score))
        
        # Sort by score (descending)
        coin_scores.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"Ranked {len(symbols)} coins by momentum")
        return coin_scores
    
    def filter_coins_by_technical_analysis(self, symbols: List[str], 
                                         min_momentum_score: float = 60) -> List[str]:
        """
        Filter coins based on technical analysis criteria
        """
        filtered_coins = []
        market_sentiment = self.get_market_sentiment()
        
        # Adjust minimum score based on market sentiment
        if market_sentiment['market_trend'] == -1:  # Bearish market
            min_momentum_score += 10  # Be more selective
        elif market_sentiment['market_trend'] == 1:  # Bullish market
            min_momentum_score -= 5  # Be less selective
        
        for symbol in symbols:
            momentum_score = self.calculate_momentum_score(symbol)
            
            # Check momentum threshold
            if momentum_score >= min_momentum_score:
                # Additional technical filters
                indicators = self.indicator_cache.get(symbol, {})
                rsi = indicators.get('rsi', 50)
                
                # Avoid extremely overbought conditions
                if rsi < 80:  # Not extremely overbought
                    filtered_coins.append(symbol)
                    logger.debug(f"Selected {symbol}: momentum={momentum_score:.1f}, RSI={rsi:.1f}")
                else:
                    logger.debug(f"Filtered out {symbol}: overbought (RSI={rsi:.1f})")
            else:
                logger.debug(f"Filtered out {symbol}: low momentum ({momentum_score:.1f})")
        
        logger.info(f"Technical analysis filtered {len(symbols)} coins to {len(filtered_coins)}")
        return filtered_coins
    
    def get_entry_exit_signals(self, symbol: str) -> Dict[str, str]:
        """
        Generate entry/exit signals based on technical analysis
        """
        indicators = self.indicator_cache.get(symbol, {})
        
        if not indicators:
            self.calculate_momentum_score(symbol)  # Calculate if not cached
            indicators = self.indicator_cache.get(symbol, {})
        
        signals = {
            'entry_signal': 'NEUTRAL',
            'exit_signal': 'HOLD',
            'confidence': 'LOW'
        }
        
        if indicators:
            momentum = indicators.get('momentum_score', 50)
            rsi = indicators.get('rsi', 50)
            macd = indicators.get('macd', 0)
            signal_line = indicators.get('signal', 0)
            
            # Entry signals
            if momentum > 75 and rsi < 70 and macd > signal_line:
                signals['entry_signal'] = 'STRONG_BUY'
                signals['confidence'] = 'HIGH'
            elif momentum > 65 and rsi < 75:
                signals['entry_signal'] = 'BUY'
                signals['confidence'] = 'MEDIUM'
            elif momentum < 35 and rsi > 30:
                signals['entry_signal'] = 'WEAK_SELL'
                signals['confidence'] = 'MEDIUM'
            
            # Exit signals
            if rsi > 80 or momentum < 25:
                signals['exit_signal'] = 'SELL'
                signals['confidence'] = 'HIGH'
            elif rsi > 75 or momentum < 35:
                signals['exit_signal'] = 'CONSIDER_SELL'
                signals['confidence'] = 'MEDIUM'
        
        return signals

# Example usage and testing
if __name__ == "__main__":
    analyzer = MarketAnalyzer()
    
    print("Testing Market Analyzer")
    print("=" * 30)
    
    # Test symbols
    test_symbols = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL']
    
    # Test momentum scoring
    print("Momentum Scores:")
    for symbol in test_symbols:
        score = analyzer.calculate_momentum_score(symbol)
        print(f"  {symbol}: {score:.1f}")
    
    # Test ranking
    print(f"\nRanked by momentum:")
    ranked = analyzer.rank_coins_by_momentum(test_symbols)
    for symbol, score in ranked:
        print(f"  {symbol}: {score:.1f}")
    
    # Test filtering
    print(f"\nFiltered coins (momentum > 60):")
    filtered = analyzer.filter_coins_by_technical_analysis(test_symbols, 60)
    print(f"  {filtered}")
    
    # Test market sentiment
    print(f"\nMarket sentiment:")
    sentiment = analyzer.get_market_sentiment()
    print(f"  {sentiment}")
    
    # Test signals
    if filtered:
        print(f"\nEntry/Exit signals for {filtered[0]}:")
        signals = analyzer.get_entry_exit_signals(filtered[0])
        print(f"  {signals}")