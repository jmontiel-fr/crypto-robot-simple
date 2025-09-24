"""
Enhanced Binance API Client with Advanced Technical Analysis
"""
import os
import logging
import numpy as np
from typing import List, Dict, Optional, Tuple
from binance.client import Client
from binance.exceptions import BinanceAPIException
import pandas as pd
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class EnhancedBinanceClient:
    def __init__(self, api_key: str = None, secret_key: str = None):
        """
        Initialize Enhanced Binance API client with advanced features
        """
        self.client = Client(api_key, secret_key)
        self.trading_fee = 0.001  # 0.10% VIP fee default
        self.base_asset = os.getenv('RESERVE_ASSET', 'BNB')
        
    def get_account_balance(self, asset: str = None) -> float:
        """Get account balance for specific asset"""
        try:
            if asset is None:
                asset = self.base_asset
            account = self.client.get_account()
            for balance in account['balances']:
                if balance['asset'] == asset:
                    return float(balance['free'])
            return 0.0
        except BinanceAPIException as e:
            logger.error(f"Error getting account balance: {e}")
            return 0.0
    
    def get_top_market_cap_coins(self, limit: int = 100) -> List[str]:
        """Get top cryptocurrencies by volume (proxy for market cap)"""
        try:
            # Get all trading pairs
            exchange_info = self.client.get_exchange_info()
            
            # Filter pairs quoted in the configured base asset
            bnb_pairs = []
            for symbol in exchange_info['symbols']:
                if (symbol['quoteAsset'] == self.base_asset and 
                    symbol['status'] == 'TRADING' and
                    symbol['baseAsset'] not in [self.base_asset]):
                    bnb_pairs.append(symbol['baseAsset'])
            
            # Get 24hr ticker statistics
            tickers = self.client.get_ticker()
            bnb_tickers = [t for t in tickers if t['symbol'].endswith(self.base_asset)]
            
            # Sort by quote volume (better proxy for market cap than base volume)
            bnb_tickers.sort(key=lambda x: float(x['quoteVolume']), reverse=True)
            
            # Return top coins
            base_len = len(self.base_asset)
            top_coins = [ticker['symbol'][:-base_len] for ticker in bnb_tickers[:limit]]
            
            # Filter out stable coins and problematic pairs
            filtered_coins = []
            stable_coins = ['USDT', 'USDC', 'BUSD', 'DAI', 'TUSD', 'PAX', 'USDN']
            problem_coins = ['LUNC', 'USTC']  # Problematic coins to avoid
            
            for coin in top_coins:
                if coin not in stable_coins and coin not in problem_coins:
                    filtered_coins.append(coin)
            
            return filtered_coins
            
        except BinanceAPIException as e:
            logger.error(f"Error getting top market cap coins: {e}")
            return []
    
    def get_enhanced_historical_prices(self, symbol: str, interval: str, lookback_periods: int) -> pd.DataFrame:
        """Get enhanced historical price data with additional metrics"""
        try:
            klines = self.client.get_historical_klines(
                symbol, interval, f"{lookback_periods} {interval[1:]} ago UTC"
            )
            
            if not klines:
                return pd.DataFrame()
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # Convert to proper data types
            numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'quote_asset_volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Add technical indicators
            df = self._add_technical_indicators(df)
            
            return df
            
        except BinanceAPIException as e:
            logger.error(f"Error getting historical prices for {symbol}: {e}")
            return pd.DataFrame()
    
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to price data"""
        try:
            # Moving averages
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['ema_12'] = df['close'].ewm(span=12).mean()
            df['ema_26'] = df['close'].ewm(span=26).mean()
            
            # MACD
            df['macd'] = df['ema_12'] - df['ema_26']
            df['macd_signal'] = df['macd'].ewm(span=9).mean()
            df['macd_histogram'] = df['macd'] - df['macd_signal']
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # Bollinger Bands
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            bb_std = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
            df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
            df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
            
            # Volume indicators
            df['volume_sma'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_sma']
            
            # Price change indicators
            df['price_change_pct'] = df['close'].pct_change() * 100
            df['volatility'] = df['price_change_pct'].rolling(window=20).std()
            
            return df
            
        except Exception as e:
            logger.error(f"Error adding technical indicators: {e}")
            return df
    
    def get_historical_prices(self, symbol: str, interval: str, lookback_periods: int) -> pd.DataFrame:
        """Legacy method for compatibility"""
        df = self.get_enhanced_historical_prices(symbol, interval, lookback_periods)
        return df[['timestamp', 'open', 'close']] if not df.empty else df
    
    def calculate_advanced_performance(self, symbol: str, periods: int = 7) -> Dict[str, float]:
        """Calculate comprehensive performance metrics"""
        try:
            df = self.get_enhanced_historical_prices(f"{symbol}{self.base_asset}", "1d", periods + 5)
            if len(df) < periods:
                return {
                    'performance': 0.0,
                    'volatility': 0.0,
                    'rsi': 50.0,
                    'macd_signal': 'neutral',
                    'bb_position': 0.5,
                    'volume_trend': 'neutral'
                }
            
            # Basic performance
            start_price = df.iloc[0]['close']
            end_price = df.iloc[-1]['close']
            performance = ((end_price - start_price) / start_price) * 100
            
            # Volatility
            volatility = df['price_change_pct'].std()
            
            # RSI
            rsi = df['rsi'].iloc[-1] if not df['rsi'].isna().all() else 50.0
            
            # MACD signal
            macd = df['macd'].iloc[-1] if not df['macd'].isna().all() else 0
            macd_signal = df['macd_signal'].iloc[-1] if not df['macd_signal'].isna().all() else 0
            
            if macd > macd_signal:
                macd_trend = 'bullish'
            elif macd < macd_signal:
                macd_trend = 'bearish'
            else:
                macd_trend = 'neutral'
            
            # Bollinger Bands position
            bb_position = df['bb_position'].iloc[-1] if not df['bb_position'].isna().all() else 0.5
            
            # Volume trend
            recent_volume = df['volume'].tail(3).mean()
            avg_volume = df['volume'].mean()
            volume_trend = 'high' if recent_volume > avg_volume * 1.2 else ('low' if recent_volume < avg_volume * 0.8 else 'normal')
            
            return {
                'performance': performance,
                'volatility': volatility,
                'rsi': rsi,
                'macd_signal': macd_trend,
                'bb_position': bb_position,
                'volume_trend': volume_trend
            }
            
        except Exception as e:
            logger.error(f"Error calculating advanced performance for {symbol}: {e}")
            return {
                'performance': 0.0,
                'volatility': 0.0,
                'rsi': 50.0,
                'macd_signal': 'neutral',
                'bb_position': 0.5,
                'volume_trend': 'neutral'
            }
    
    def calculate_performance(self, symbol: str, periods: int = 1) -> float:
        """Legacy method for compatibility"""
        result = self.calculate_advanced_performance(symbol, periods)
        return result['performance']
    
    def get_smart_coin_ranking(self, coin_list: List[str], analysis_periods: int = 7) -> List[Tuple[str, float, Dict]]:
        """Get intelligent coin ranking with comprehensive analysis"""
        coin_analyses = []
        
        for coin in coin_list:
            try:
                analysis = self.calculate_advanced_performance(coin, analysis_periods)
                
                # Calculate composite score
                score = 0.0
                
                # Performance weight (40%)
                performance = analysis['performance']
                performance_score = min(max(performance / 2, -20), 20)  # Cap between -20 and 20
                score += performance_score * 0.4
                
                # RSI weight (20%) - prefer 30-70 range
                rsi = analysis['rsi']
                if 30 <= rsi <= 70:
                    rsi_score = 10
                elif rsi < 30:
                    rsi_score = 8  # Oversold can be opportunity
                else:
                    rsi_score = 2  # Overbought is risky
                score += rsi_score * 0.2
                
                # MACD weight (15%)
                macd_signal = analysis['macd_signal']
                macd_score = 10 if macd_signal == 'bullish' else (5 if macd_signal == 'neutral' else 0)
                score += macd_score * 0.15
                
                # Bollinger Bands weight (15%)
                bb_position = analysis['bb_position']
                if 0.2 <= bb_position <= 0.8:
                    bb_score = 10  # Good position
                elif bb_position < 0.2:
                    bb_score = 7   # Oversold opportunity
                else:
                    bb_score = 3   # Overbought risk
                score += bb_score * 0.15
                
                # Volume weight (10%)
                volume_trend = analysis['volume_trend']
                volume_score = 10 if volume_trend == 'high' else (7 if volume_trend == 'normal' else 4)
                score += volume_score * 0.1
                
                coin_analyses.append((coin, score, analysis))
                
            except Exception as e:
                logger.error(f"Error analyzing {coin}: {e}")
                continue
        
        # Sort by score descending
        coin_analyses.sort(key=lambda x: x[1], reverse=True)
        
        return coin_analyses
    
    def get_best_performing_coins(self, coin_list: List[str], periods: int = 7, limit: int = 10) -> List[str]:
        """Get best performing coins using smart ranking"""
        coin_analyses = self.get_smart_coin_ranking(coin_list, periods)
        
        # Return top coins
        best_coins = [coin for coin, score, analysis in coin_analyses[:limit]]
        
        # Log analysis for top coins
        for i, (coin, score, analysis) in enumerate(coin_analyses[:5]):
            logger.info(f"Rank {i+1}: {coin} (Score: {score:.2f}) - "
                       f"Perf: {analysis['performance']:.2f}%, "
                       f"RSI: {analysis['rsi']:.1f}, "
                       f"MACD: {analysis['macd_signal']}, "
                       f"Volume: {analysis['volume_trend']}")
        
        return best_coins
    
    def get_market_overview(self) -> Dict:
        """Get comprehensive market overview"""
        try:
            # Get Bitcoin metrics as market proxy
            btc_analysis = self.calculate_advanced_performance('BTC', 7)
            
            # Get top 10 coins average metrics
            top_coins = self.get_top_market_cap_coins(10)
            if len(top_coins) >= 5:
                top_5_performances = []
                for coin in top_coins[:5]:
                    perf = self.calculate_performance(coin, 7)
                    top_5_performances.append(perf)
                
                avg_performance = np.mean(top_5_performances)
                market_volatility = np.std(top_5_performances)
            else:
                avg_performance = 0.0
                market_volatility = 0.0
            
            # Determine market sentiment
            if btc_analysis['performance'] > 10 and avg_performance > 5:
                sentiment = 'bullish'
            elif btc_analysis['performance'] < -10 and avg_performance < -5:
                sentiment = 'bearish'
            else:
                sentiment = 'neutral'
            
            return {
                'btc_performance_7d': btc_analysis['performance'],
                'btc_rsi': btc_analysis['rsi'],
                'btc_macd_signal': btc_analysis['macd_signal'],
                'market_avg_performance': avg_performance,
                'market_volatility': market_volatility,
                'market_sentiment': sentiment,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting market overview: {e}")
            return {
                'btc_performance_7d': 0.0,
                'btc_rsi': 50.0,
                'btc_macd_signal': 'neutral',
                'market_avg_performance': 0.0,
                'market_volatility': 0.0,
                'market_sentiment': 'neutral',
                'analysis_timestamp': datetime.now().isoformat()
            }
    
    def place_market_order(self, symbol: str, side: str, quantity: float) -> Dict:
        """Place a market order"""
        try:
            order = self.client.order_market(
                symbol=symbol,
                side=side,
                quantity=quantity
            )
            logger.info(f"Order placed: {side} {quantity} {symbol}")
            return order
        except BinanceAPIException as e:
            logger.error(f"Error placing order: {e}")
            return {}
    
    def get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol"""
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except BinanceAPIException as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
            return 0.0
    
    def get_24hr_stats(self, symbol: str) -> Dict:
        """Get 24hr statistics for a symbol"""
        try:
            stats = self.client.get_24hr_ticker(symbol=symbol)
            return {
                'price_change': float(stats['priceChange']),
                'price_change_percent': float(stats['priceChangePercent']),
                'high_price': float(stats['highPrice']),
                'low_price': float(stats['lowPrice']),
                'volume': float(stats['volume']),
                'quote_volume': float(stats['quoteVolume']),
                'count': int(stats['count'])
            }
        except BinanceAPIException as e:
            logger.error(f"Error getting 24hr stats for {symbol}: {e}")
            return {}
    
    def is_market_favorable_for_buying(self) -> bool:
        """Determine if market conditions are favorable for buying"""
        try:
            market_overview = self.get_market_overview()
            
            # Favorable conditions:
            # 1. Market sentiment is not bearish
            # 2. BTC RSI is not extremely overbought
            # 3. Recent performance is not extremely negative
            
            sentiment_ok = market_overview['market_sentiment'] != 'bearish'
            rsi_ok = market_overview['btc_rsi'] < 75
            performance_ok = market_overview['btc_performance_7d'] > -15
            
            return sentiment_ok and rsi_ok and performance_ok
            
        except Exception as e:
            logger.error(f"Error checking market conditions: {e}")
            return True  # Default to allowing trades
    
    def get_current_price_in_bnb(self, asset: str) -> float:
        """Get current price of asset in base asset (configurable)."""
        symbol = f"{asset}{self.base_asset}"
        return self.get_current_price(symbol)
