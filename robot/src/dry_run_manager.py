#!/usr/bin/env python3
"""
Dry-Run Manager for Robot Trading

Implements dry-run mode where robot executes strategy but simulates
all buy/sell/convert operations without real API calls. Includes:
- Virtual portfolio management
- Operation cost simulation
- Transaction rollback on interruption
- Resume capability after restart
"""

import os
import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from decimal import Decimal, ROUND_DOWN

logger = logging.getLogger(__name__)

@dataclass
class DryRunPosition:
    """Virtual position in dry-run mode"""
    symbol: str
    quantity: Decimal
    entry_price: Decimal
    current_price: Decimal
    entry_time: datetime
    last_update: datetime
    
    @property
    def current_value(self) -> Decimal:
        return self.quantity * self.current_price
    
    @property
    def entry_value(self) -> Decimal:
        return self.quantity * self.entry_price
    
    @property
    def performance(self) -> float:
        if self.entry_value == 0:
            return 0.0
        return float((self.current_value - self.entry_value) / self.entry_value)
    
    @property
    def unrealized_pnl(self) -> Decimal:
        return self.current_value - self.entry_value

@dataclass
class DryRunPortfolio:
    """Virtual portfolio for dry-run mode"""
    positions: Dict[str, DryRunPosition]
    reserve_balance: Decimal  # In reserve asset (BNB)
    reserve_asset: str
    total_fees_paid: Decimal
    total_trades: int
    created_at: datetime
    last_update: datetime
    
    @property
    def portfolio_value(self) -> Decimal:
        """Total value of all positions in reserve asset"""
        return sum(pos.current_value for pos in self.positions.values())
    
    @property
    def total_value(self) -> Decimal:
        """Total portfolio value including reserve"""
        return self.portfolio_value + self.reserve_balance
    
    @property
    def unrealized_pnl(self) -> Decimal:
        """Total unrealized profit/loss"""
        return sum(pos.unrealized_pnl for pos in self.positions.values())

@dataclass
class DryRunTransaction:
    """Record of a dry-run transaction"""
    transaction_id: str
    timestamp: datetime
    transaction_type: str  # 'BUY', 'SELL', 'CONVERT'
    from_asset: str
    to_asset: str
    from_quantity: Decimal
    to_quantity: Decimal
    price: Decimal
    fee: Decimal
    fee_asset: str
    status: str  # 'PENDING', 'COMPLETED', 'FAILED', 'ROLLED_BACK'
    cycle_number: Optional[int] = None

class DryRunManager:
    """Manages dry-run mode operations"""
    
    def __init__(self):
        self.is_dry_run = self._check_dry_run_mode()
        self.portfolio_file = "data/dry_run_portfolio.json"
        self.transactions_file = "data/dry_run_transactions.json"
        self.state_file = "data/dry_run_state.json"
        
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Initialize or load portfolio
        self.portfolio = self._load_or_create_portfolio()
        self.pending_transactions = []
        
        logger.info(f"Dry-Run Manager initialized: {'DRY-RUN' if self.is_dry_run else 'LIVE'} mode")
    
    def _check_dry_run_mode(self) -> bool:
        """Check if dry-run mode is enabled"""
        dry_run_env = os.getenv('ROBOT_DRY_RUN', 'true').lower()
        return dry_run_env in ['true', '1', 'yes', 'on']
    
    def _load_or_create_portfolio(self) -> DryRunPortfolio:
        """Load existing portfolio or create new one"""
        
        if os.path.exists(self.portfolio_file):
            try:
                with open(self.portfolio_file, 'r') as f:
                    data = json.load(f)
                
                # Convert to DryRunPortfolio
                positions = {}
                for symbol, pos_data in data.get('positions', {}).items():
                    positions[symbol] = DryRunPosition(
                        symbol=pos_data['symbol'],
                        quantity=Decimal(str(pos_data['quantity'])),
                        entry_price=Decimal(str(pos_data['entry_price'])),
                        current_price=Decimal(str(pos_data['current_price'])),
                        entry_time=datetime.fromisoformat(pos_data['entry_time']),
                        last_update=datetime.fromisoformat(pos_data['last_update'])
                    )
                
                portfolio = DryRunPortfolio(
                    positions=positions,
                    reserve_balance=Decimal(str(data['reserve_balance'])),
                    reserve_asset=data['reserve_asset'],
                    total_fees_paid=Decimal(str(data['total_fees_paid'])),
                    total_trades=data['total_trades'],
                    created_at=datetime.fromisoformat(data['created_at']),
                    last_update=datetime.fromisoformat(data['last_update'])
                )
                
                logger.info(f"Loaded existing dry-run portfolio: {portfolio.total_value} {portfolio.reserve_asset}")
                return portfolio
                
            except Exception as e:
                logger.error(f"Error loading portfolio: {e}")
        
        # Create new portfolio
        initial_reserve = Decimal(str(os.getenv('INITIAL_RESERVE', '100')))
        reserve_asset = os.getenv('RESERVE_ASSET', 'BNB')
        
        portfolio = DryRunPortfolio(
            positions={},
            reserve_balance=initial_reserve,
            reserve_asset=reserve_asset,
            total_fees_paid=Decimal('0'),
            total_trades=0,
            created_at=datetime.now(),
            last_update=datetime.now()
        )
        
        logger.info(f"Created new dry-run portfolio: {initial_reserve} {reserve_asset}")
        return portfolio
    
    def _save_portfolio(self):
        """Save portfolio to file"""
        try:
            # Convert to JSON-serializable format
            positions_data = {}
            for symbol, position in self.portfolio.positions.items():
                positions_data[symbol] = {
                    'symbol': position.symbol,
                    'quantity': str(position.quantity),
                    'entry_price': str(position.entry_price),
                    'current_price': str(position.current_price),
                    'entry_time': position.entry_time.isoformat(),
                    'last_update': position.last_update.isoformat()
                }
            
            data = {
                'positions': positions_data,
                'reserve_balance': str(self.portfolio.reserve_balance),
                'reserve_asset': self.portfolio.reserve_asset,
                'total_fees_paid': str(self.portfolio.total_fees_paid),
                'total_trades': self.portfolio.total_trades,
                'created_at': self.portfolio.created_at.isoformat(),
                'last_update': datetime.now().isoformat()
            }
            
            with open(self.portfolio_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving portfolio: {e}")
    
    def _save_transaction(self, transaction: DryRunTransaction):
        """Save transaction to file"""
        try:
            transactions = []
            
            # Load existing transactions
            if os.path.exists(self.transactions_file):
                with open(self.transactions_file, 'r') as f:
                    transactions = json.load(f)
            
            # Add new transaction
            transaction_data = {
                'transaction_id': transaction.transaction_id,
                'timestamp': transaction.timestamp.isoformat(),
                'transaction_type': transaction.transaction_type,
                'from_asset': transaction.from_asset,
                'to_asset': transaction.to_asset,
                'from_quantity': str(transaction.from_quantity),
                'to_quantity': str(transaction.to_quantity),
                'price': str(transaction.price),
                'fee': str(transaction.fee),
                'fee_asset': transaction.fee_asset,
                'status': transaction.status,
                'cycle_number': transaction.cycle_number
            }
            
            transactions.append(transaction_data)
            
            with open(self.transactions_file, 'w') as f:
                json.dump(transactions, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving transaction: {e}")
    
    def get_current_prices(self, symbols: List[str]) -> Dict[str, Decimal]:
        """Get current prices for symbols (simulated in dry-run)"""
        
        if not self.is_dry_run:
            # In live mode, would call real API
            logger.warning("get_current_prices called in live mode - implement real API call")
            return {}
        
        # Simulate price fetching with realistic prices
        simulated_prices = {
            'BTC': Decimal('45000'),
            'ETH': Decimal('2500'),
            'BNB': Decimal('300'),
            'ADA': Decimal('0.5'),
            'SOL': Decimal('100'),
            'DOT': Decimal('7'),
            'MATIC': Decimal('0.8'),
            'AVAX': Decimal('35'),
            'LINK': Decimal('15'),
            'UNI': Decimal('8')
        }
        
        # Add some realistic price movement (±2%)
        import random
        prices = {}
        for symbol in symbols:
            base_price = simulated_prices.get(symbol, Decimal('10'))
            # Simulate ±2% price movement
            movement = Decimal(str(random.uniform(-0.02, 0.02)))
            current_price = base_price * (Decimal('1') + movement)
            prices[symbol] = current_price.quantize(Decimal('0.0001'), rounding=ROUND_DOWN)
        
        return prices
    
    def update_position_prices(self, current_prices: Dict[str, Decimal]):
        """Update current prices for all positions"""
        
        for symbol, position in self.portfolio.positions.items():
            if symbol in current_prices:
                position.current_price = current_prices[symbol]
                position.last_update = datetime.now()
        
        self.portfolio.last_update = datetime.now()
        self._save_portfolio()
    
    def simulate_buy_order(self, symbol: str, quantity: Decimal, price: Decimal, 
                          cycle_number: Optional[int] = None) -> DryRunTransaction:
        """Simulate a buy order in dry-run mode"""
        
        if not self.is_dry_run:
            raise ValueError("simulate_buy_order should only be called in dry-run mode")
        
        # Calculate costs
        total_cost = quantity * price
        trading_fee_rate = Decimal(str(os.getenv('TRADING_FEE', '0.001')))
        fee = total_cost * trading_fee_rate
        total_required = total_cost + fee
        
        # Check if we have enough reserve
        if self.portfolio.reserve_balance < total_required:
            raise ValueError(f"Insufficient reserve: need {total_required}, have {self.portfolio.reserve_balance}")
        
        # Create transaction
        transaction = DryRunTransaction(
            transaction_id=f"BUY_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now(),
            transaction_type='BUY',
            from_asset=self.portfolio.reserve_asset,
            to_asset=symbol,
            from_quantity=total_required,
            to_quantity=quantity,
            price=price,
            fee=fee,
            fee_asset=self.portfolio.reserve_asset,
            status='PENDING',
            cycle_number=cycle_number
        )
        
        # Execute transaction
        self.portfolio.reserve_balance -= total_required
        self.portfolio.total_fees_paid += fee
        self.portfolio.total_trades += 1
        
        # Add or update position
        if symbol in self.portfolio.positions:
            # Average down the position
            existing_pos = self.portfolio.positions[symbol]
            total_quantity = existing_pos.quantity + quantity
            total_value = existing_pos.entry_value + total_cost
            new_avg_price = total_value / total_quantity
            
            existing_pos.quantity = total_quantity
            existing_pos.entry_price = new_avg_price
            existing_pos.current_price = price
            existing_pos.last_update = datetime.now()
        else:
            # Create new position
            self.portfolio.positions[symbol] = DryRunPosition(
                symbol=symbol,
                quantity=quantity,
                entry_price=price,
                current_price=price,
                entry_time=datetime.now(),
                last_update=datetime.now()
            )
        
        transaction.status = 'COMPLETED'
        self._save_transaction(transaction)
        self._save_portfolio()
        
        logger.info(f"DRY-RUN BUY: {quantity} {symbol} @ {price} (fee: {fee})")
        return transaction
    
    def simulate_sell_order(self, symbol: str, quantity: Decimal, price: Decimal,
                           cycle_number: Optional[int] = None) -> DryRunTransaction:
        """Simulate a sell order in dry-run mode"""
        
        if not self.is_dry_run:
            raise ValueError("simulate_sell_order should only be called in dry-run mode")
        
        # Check if we have the position
        if symbol not in self.portfolio.positions:
            raise ValueError(f"No position found for {symbol}")
        
        position = self.portfolio.positions[symbol]
        if position.quantity < quantity:
            raise ValueError(f"Insufficient quantity: need {quantity}, have {position.quantity}")
        
        # Calculate proceeds
        gross_proceeds = quantity * price
        trading_fee_rate = Decimal(str(os.getenv('TRADING_FEE', '0.001')))
        fee = gross_proceeds * trading_fee_rate
        net_proceeds = gross_proceeds - fee
        
        # Create transaction
        transaction = DryRunTransaction(
            transaction_id=f"SELL_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now(),
            transaction_type='SELL',
            from_asset=symbol,
            to_asset=self.portfolio.reserve_asset,
            from_quantity=quantity,
            to_quantity=net_proceeds,
            price=price,
            fee=fee,
            fee_asset=self.portfolio.reserve_asset,
            status='PENDING',
            cycle_number=cycle_number
        )
        
        # Execute transaction
        self.portfolio.reserve_balance += net_proceeds
        self.portfolio.total_fees_paid += fee
        self.portfolio.total_trades += 1
        
        # Update position
        position.quantity -= quantity
        position.last_update = datetime.now()
        
        # Remove position if fully sold
        if position.quantity == 0:
            del self.portfolio.positions[symbol]
        
        transaction.status = 'COMPLETED'
        self._save_transaction(transaction)
        self._save_portfolio()
        
        logger.info(f"DRY-RUN SELL: {quantity} {symbol} @ {price} (fee: {fee})")
        return transaction
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary for display"""
        
        positions_summary = {}
        for symbol, position in self.portfolio.positions.items():
            positions_summary[symbol] = {
                'quantity': float(position.quantity),
                'entry_price': float(position.entry_price),
                'current_price': float(position.current_price),
                'current_value': float(position.current_value),
                'unrealized_pnl': float(position.unrealized_pnl),
                'performance': position.performance,
                'entry_time': position.entry_time.isoformat()
            }
        
        return {
            'mode': 'DRY-RUN' if self.is_dry_run else 'LIVE',
            'total_value': float(self.portfolio.total_value),
            'reserve_balance': float(self.portfolio.reserve_balance),
            'reserve_asset': self.portfolio.reserve_asset,
            'portfolio_value': float(self.portfolio.portfolio_value),
            'unrealized_pnl': float(self.portfolio.unrealized_pnl),
            'total_fees_paid': float(self.portfolio.total_fees_paid),
            'total_trades': self.portfolio.total_trades,
            'positions': positions_summary,
            'created_at': self.portfolio.created_at.isoformat(),
            'last_update': self.portfolio.last_update.isoformat()
        }
    
    def begin_transaction_group(self, cycle_number: int):
        """Begin a transaction group (for rollback capability)"""
        self.pending_transactions = []
        logger.info(f"Started transaction group for cycle {cycle_number}")
    
    def commit_transaction_group(self):
        """Commit all pending transactions"""
        for transaction in self.pending_transactions:
            transaction.status = 'COMPLETED'
            self._save_transaction(transaction)
        
        self.pending_transactions = []
        self._save_portfolio()
        logger.info("Committed transaction group")
    
    def rollback_transaction_group(self):
        """Rollback all pending transactions"""
        logger.warning("Rolling back transaction group")
        
        # Mark transactions as rolled back
        for transaction in self.pending_transactions:
            transaction.status = 'ROLLED_BACK'
            self._save_transaction(transaction)
        
        # Reload portfolio from last saved state
        self.portfolio = self._load_or_create_portfolio()
        self.pending_transactions = []
        
        logger.info("Transaction group rolled back")

# Global dry-run manager instance
dry_run_manager = DryRunManager()

def is_dry_run_mode() -> bool:
    """Check if robot is in dry-run mode"""
    return dry_run_manager.is_dry_run

def get_dry_run_portfolio() -> Dict[str, Any]:
    """Get dry-run portfolio summary"""
    return dry_run_manager.get_portfolio_summary()

if __name__ == "__main__":
    # Test dry-run manager
    print("🧪 DRY-RUN MANAGER TEST")
    print("=" * 40)
    
    manager = DryRunManager()
    
    print(f"Mode: {'DRY-RUN' if manager.is_dry_run else 'LIVE'}")
    print(f"Portfolio: {manager.get_portfolio_summary()}")
    
    if manager.is_dry_run:
        # Test buy order
        try:
            prices = manager.get_current_prices(['BTC', 'ETH'])
            print(f"Current prices: {prices}")
            
            if 'BTC' in prices:
                transaction = manager.simulate_buy_order('BTC', Decimal('0.01'), prices['BTC'])
                print(f"Buy transaction: {transaction.transaction_id}")
            
            summary = manager.get_portfolio_summary()
            print(f"Updated portfolio: {summary}")
            
        except Exception as e:
            print(f"Test error: {e}")
    
    print("\n✅ Dry-run manager ready!")