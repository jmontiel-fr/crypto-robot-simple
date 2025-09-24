"""
Portfolio Manager for crypto trading robot using SQLAlchemy ORM
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.database import (
    get_db_manager, Portfolio, Position, TradingCycle,
    CyclePosition, init_database
)

logger = logging.getLogger(__name__)

@dataclass
class PortfolioPosition:
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    entry_date: datetime
    
    @property
    def current_value(self) -> float:
        return self.quantity * self.current_price
    
    @property
    def entry_value(self) -> float:
        return self.quantity * self.entry_price
    
    @property
    def pnl(self) -> float:
        return self.current_value - self.entry_value
    
    @property
    def pnl_percentage(self) -> float:
        if self.entry_value == 0:
            return 0.0
        return (self.pnl / self.entry_value) * 100

@dataclass
class CycleData:
    cycle_number: int
    date: datetime
    bnb_reserve: float
    portfolio_value: float
    total_value: float
    positions: List[PortfolioPosition] = None
    actions_taken: List[str] = None
    
    def __post_init__(self):
        if self.positions is None:
            self.positions = []
        if self.actions_taken is None:
            self.actions_taken = []
    positions: List[PortfolioPosition]
    actions_taken: List[str]

class PortfolioManager:
    def __init__(self):
        """Initialize portfolio manager with database"""
        self.db_manager = get_db_manager()
        self.db_manager.create_tables()
        self.portfolio_id = None
        self.trading_fee = 0.001  # 0.10% trading fee

        # Load or create portfolio
        self._load_or_create_portfolio()

        logger.info("Portfolio Manager initialized with database")
    
    def _load_or_create_portfolio(self):
        """Load existing portfolio or create new one"""
        with self.db_manager.get_session() as session:
            # Try to get the latest portfolio
            portfolio = session.query(Portfolio).order_by(desc(Portfolio.id)).first()
            
            if portfolio is None:
                # Create new portfolio
                portfolio = Portfolio(
                    bnb_reserve=0.0,
                    current_cycle=0,
                    is_frozen=False
                )
                session.add(portfolio)
                session.commit()
                session.refresh(portfolio)
            
            self.portfolio_id = portfolio.id
            logger.info(f"Using portfolio ID: {self.portfolio_id}")
    
    def initialize_portfolio(self, initial_reserve: float):
        """Initialize portfolio with initial reserve (in configured base asset)"""
        with self.db_manager.get_session() as session:
            portfolio = session.query(Portfolio).filter_by(id=self.portfolio_id).first()
            if portfolio:
                portfolio.bnb_reserve = initial_reserve
                portfolio.current_cycle = 0
                portfolio.is_frozen = False
                portfolio.freeze_reason = None
                session.commit()
                
                # Clear existing positions
                session.query(Position).filter_by(portfolio_id=self.portfolio_id, is_active=True).update({
                    'is_active': False
                })
                session.commit()
        
        logger.info(f"Portfolio initialized with {initial_reserve} reserve units")
    
    def add_position(self, symbol: str, quantity: float, price: float):
        """Add a new position to the portfolio"""
        with self.db_manager.get_session() as session:
            # Check if position already exists
            existing_position = session.query(Position).filter_by(
                portfolio_id=self.portfolio_id,
                symbol=symbol,
                is_active=True
            ).first()
            
            if existing_position:
                # Average the position
                total_quantity = existing_position.quantity + quantity
                total_value = existing_position.entry_value + (quantity * price)
                avg_price = total_value / total_quantity
                
                existing_position.quantity = total_quantity
                existing_position.entry_price = avg_price
                existing_position.current_price = price
            else:
                # Create new position
                new_position = Position(
                    portfolio_id=self.portfolio_id,
                    symbol=symbol,
                    quantity=quantity,
                    entry_price=price,
                    current_price=price,
                    entry_date=datetime.now(),
                    is_active=True
                )
                session.add(new_position)
            
            session.commit()
            
        logger.info(f"Added position: {quantity} {symbol} at {price}")
    
    def remove_position(self, symbol: str) -> bool:
        """Remove a position from the portfolio"""
        with self.db_manager.get_session() as session:
            position = session.query(Position).filter_by(
                portfolio_id=self.portfolio_id,
                symbol=symbol,
                is_active=True
            ).first()
            
            if position:
                position.is_active = False
                session.commit()
                logger.info(f"Removed position: {symbol}")
                return True
            
        return False
    
    def update_prices(self, price_data: Dict[str, float]):
        """Update current prices for all positions"""
        with self.db_manager.get_session() as session:
            positions = session.query(Position).filter_by(
                portfolio_id=self.portfolio_id,
                is_active=True
            ).all()
            
            for position in positions:
                if position.symbol in price_data:
                    position.current_price = price_data[position.symbol]
            
            session.commit()
    
    def get_portfolio_value(self) -> float:
        """Calculate total portfolio value in base asset"""
        with self.db_manager.get_session() as session:
            positions = session.query(Position).filter_by(
                portfolio_id=self.portfolio_id,
                is_active=True
            ).all()
            
            total_value = sum(pos.current_value for pos in positions)
            return total_value
    
    def get_total_value(self) -> float:
        """Calculate total value (portfolio + reserve) in base asset"""
        portfolio_value = self.get_portfolio_value()
        bnb_reserve = self.get_bnb_reserve()
        return portfolio_value + bnb_reserve
    
    def get_bnb_reserve(self) -> float:
        """Get current reserve (base asset)"""
        with self.db_manager.get_session() as session:
            portfolio = session.query(Portfolio).filter_by(id=self.portfolio_id).first()
            return portfolio.bnb_reserve if portfolio else 0.0
    
    def update_bnb_reserve(self, new_reserve: float):
        """Update reserve amount (base asset)"""
        with self.db_manager.get_session() as session:
            portfolio = session.query(Portfolio).filter_by(id=self.portfolio_id).first()
            if portfolio:
                portfolio.bnb_reserve = new_reserve
                session.commit()
    
    @property
    def bnb_reserve(self) -> float:
        """Property to get reserve amount (base asset)"""
        return self.get_bnb_reserve()
    
    @bnb_reserve.setter
    def bnb_reserve(self, value: float):
        """Property setter for reserve amount (base asset)"""
        self.update_bnb_reserve(value)
    
    @property
    def positions(self) -> Dict[str, PortfolioPosition]:
        """Get current positions as dictionary"""
        positions_dict = {}
        
        with self.db_manager.get_session() as session:
            positions = session.query(Position).filter_by(
                portfolio_id=self.portfolio_id,
                is_active=True
            ).all()
            
            for pos in positions:
                positions_dict[pos.symbol] = PortfolioPosition(
                    symbol=pos.symbol,
                    quantity=pos.quantity,
                    entry_price=pos.entry_price,
                    current_price=pos.current_price,
                    entry_date=pos.entry_date
                )
        
        return positions_dict
    
    def get_position_weights(self) -> Dict[str, float]:
        """Get position weights as percentage of total portfolio"""
        portfolio_value = self.get_portfolio_value()
        if portfolio_value == 0:
            return {}
        
        weights = {}
        positions = self.positions
        
        for symbol, position in positions.items():
            weights[symbol] = (position.current_value / portfolio_value) * 100
        
        return weights
    
    def get_underperforming_positions(self, threshold: float = -2.0) -> List[str]:
        """Get positions that underperformed by more than threshold percentage"""
        underperforming = []
        positions = self.positions
        
        for symbol, position in positions.items():
            if position.pnl_percentage < threshold:
                underperforming.append(symbol)
        
        return underperforming
    
    def execute_trade(self, symbol: str, action: str, quantity: float, price: float) -> float:
        """
        Execute a trade and update portfolio
        
        Returns:
            Cost of the trade including fees
        """
        trade_value = quantity * price
        fee = trade_value * self.trading_fee
        
        with self.db_manager.get_session() as session:
            portfolio = session.query(Portfolio).filter_by(id=self.portfolio_id).first()
            
            if action == "BUY":
                total_cost = trade_value + fee
                if total_cost <= portfolio.bnb_reserve:
                    portfolio.bnb_reserve -= total_cost
                    session.commit()
                    
                    # Add position after committing reserve change
                    self.add_position(symbol, quantity, price)
                    
                    logger.info(f"Bought {quantity} {symbol} at {price} (Fee: {fee})")
                    return total_cost
                else:
                    logger.warning(f"Insufficient reserve for buying {symbol}")
                    return 0.0
            
            elif action == "SELL":
                position = session.query(Position).filter_by(
                    portfolio_id=self.portfolio_id,
                    symbol=symbol,
                    is_active=True
                ).first()
                
                if position and position.quantity >= quantity:
                    proceeds = trade_value - fee
                    portfolio.bnb_reserve += proceeds
                    
                    # Update or remove position
                    if position.quantity == quantity:
                        position.is_active = False
                    else:
                        position.quantity -= quantity
                    
                    session.commit()
                    
                    logger.info(f"Sold {quantity} {symbol} at {price} (Fee: {fee})")
                    return fee  # Return only the fee as cost
                else:
                    logger.warning(f"Insufficient quantity to sell {symbol}")
                    return 0.0
    
    def execute_swap(self, from_symbol: str, to_symbol: str, from_quantity: float, 
                     binance_client) -> Tuple[bool, float, str]:
        """
        Execute a direct crypto-to-crypto swap
        
        Args:
            from_symbol: Symbol to swap from (e.g., 'ADA')
            to_symbol: Symbol to swap to (e.g., 'ETH') 
            from_quantity: Quantity of from_symbol to swap
            binance_client: Binance client for executing the swap
            
        Returns:
            Tuple of (success, to_quantity_received, error_message)
        """
        try:
            with self.db_manager.get_session() as session:
                # Check if we have enough of the from_symbol
                from_position = session.query(Position).filter_by(
                    portfolio_id=self.portfolio_id,
                    symbol=from_symbol,
                    is_active=True
                ).first()
                
                if not from_position or from_position.quantity < from_quantity:
                    return False, 0.0, f"Insufficient {from_symbol} quantity for swap"
                
                # Execute the direct swap via Binance
                swap_result = binance_client.execute_direct_swap(
                    from_symbol, to_symbol, from_quantity
                )
                
                if not swap_result['success']:
                    return False, 0.0, swap_result.get('error', 'Swap failed')
                
                to_quantity_received = swap_result['to_quantity']
                
                # Update the from_position (reduce or remove)
                if from_position.quantity == from_quantity:
                    from_position.is_active = False
                else:
                    from_position.quantity -= from_quantity
                
                # Add or update the to_position
                to_position = session.query(Position).filter_by(
                    portfolio_id=self.portfolio_id,
                    symbol=to_symbol,
                    is_active=True
                ).first()
                
                if to_position:
                    # Update existing position (weighted average entry price)
                    old_value = to_position.quantity * to_position.entry_price
                    new_value = to_quantity_received * swap_result['price']
                    total_quantity = to_position.quantity + to_quantity_received
                    
                    if total_quantity > 0:
                        to_position.entry_price = (old_value + new_value) / total_quantity
                        to_position.quantity = total_quantity
                else:
                    # Create new position
                    new_position = Position(
                        portfolio_id=self.portfolio_id,
                        symbol=to_symbol,
                        quantity=to_quantity_received,
                        entry_price=swap_result['price'],
                        current_price=swap_result['price'],
                        is_active=True
                    )
                    session.add(new_position)
                
                session.commit()
                
                logger.info(f"Swap executed: {from_quantity} {from_symbol} -> {to_quantity_received} {to_symbol}")
                return True, to_quantity_received, ""
                
        except Exception as e:
            logger.error(f"Error executing swap {from_symbol}->{to_symbol}: {e}")
            return False, 0.0, str(e)
        
        return 0.0
    
    def record_cycle(self, actions_taken: List[str] = None):
        """Record current cycle data"""
        with self.db_manager.get_session() as session:
            portfolio = session.query(Portfolio).filter_by(id=self.portfolio_id).first()
            portfolio.current_cycle += 1
            
            # Create cycle record
            cycle = TradingCycle(
                portfolio_id=self.portfolio_id,
                cycle_number=portfolio.current_cycle,
                bnb_reserve=portfolio.bnb_reserve,
                portfolio_value=self.get_portfolio_value(),
                total_value=self.get_total_value(),
                actions_taken=actions_taken or [],
                cycle_date=datetime.now()
            )
            session.add(cycle)
            session.commit()
            session.refresh(cycle)
            
            # Record position snapshots
            positions = session.query(Position).filter_by(
                portfolio_id=self.portfolio_id,
                is_active=True
            ).all()
            
            for position in positions:
                cycle_position = CyclePosition(
                    cycle_id=cycle.id,
                    symbol=position.symbol,
                    quantity=position.quantity,
                    entry_price=position.entry_price,
                    current_price=position.current_price,
                    current_value=position.current_value,
                    pnl_percentage=position.pnl_percentage,
                    entry_date=position.entry_date
                )
                session.add(cycle_position)
            
            session.commit()
            
        logger.info(f"Cycle {portfolio.current_cycle} recorded")
    
    @property
    def cycle_history(self) -> List[CycleData]:
        """Get cycle history"""
        history = []
        
        with self.db_manager.get_session() as session:
            cycles = session.query(TradingCycle).filter_by(
                portfolio_id=self.portfolio_id
            ).order_by(TradingCycle.cycle_number).all()
            
            for cycle in cycles:
                # Get positions for this cycle
                cycle_positions = session.query(CyclePosition).filter_by(
                    cycle_id=cycle.id
                ).all()
                
                positions = []
                for cp in cycle_positions:
                    positions.append(PortfolioPosition(
                        symbol=cp.symbol,
                        quantity=cp.quantity,
                        entry_price=cp.entry_price,
                        current_price=cp.current_price,
                        entry_date=cp.entry_date
                    ))
                
                cycle_data = CycleData(
                    cycle_number=cycle.cycle_number,
                    date=cycle.cycle_date,
                    bnb_reserve=cycle.bnb_reserve,
                    portfolio_value=cycle.portfolio_value,
                    total_value=cycle.total_value,
                    positions=positions,
                    actions_taken=cycle.actions_taken or []
                )
                history.append(cycle_data)
        
        return history
    
    @property
    def current_cycle(self) -> int:
        """Get current cycle number"""
        with self.db_manager.get_session() as session:
            portfolio = session.query(Portfolio).filter_by(id=self.portfolio_id).first()
            return portfolio.current_cycle if portfolio else 0
    
    def get_portfolio_summary(self) -> Dict:
        """Get a summary of the current portfolio"""
        positions_data = {}
        for symbol, pos in self.positions.items():
            positions_data[symbol] = {
                'quantity': pos.quantity,
                'current_price': pos.current_price,
                'current_value': pos.current_value,
                'pnl_percentage': pos.pnl_percentage
            }
        
        return {
            'cycle': self.current_cycle,
            'bnb_reserve': self.bnb_reserve,
            'portfolio_value': self.get_portfolio_value(),
            'total_value': self.get_total_value(),
            'positions_count': len(self.positions),
            'positions': positions_data
        }
    
    def clear_all_positions(self):
        """Clear all positions from the database"""
        try:
            db_manager = get_db_manager()
            with db_manager.get_session() as session:
                # Delete all positions
                session.query(Position).delete()
                
                # Delete all cycle positions
                session.query(CyclePosition).delete()
                
                session.commit()
                logger.info("All positions cleared from database")
                
        except Exception as e:
            logger.error(f"Error clearing positions: {e}")
            raise
    
    def clear_trading_history(self):
        """Clear all trading history from the database"""
        try:
            db_manager = get_db_manager()
            with db_manager.get_session() as session:
                # Delete all trading cycles
                session.query(TradingCycle).delete()
                
                session.commit()
                logger.info("All trading history cleared from database")
                
        except Exception as e:
            logger.error(f"Error clearing trading history: {e}")
            raise

    # -------- Helpers for cycle-based progress analysis -------- #
    def get_last_cycles(self, k: int = 5) -> List[TradingCycle]:
        """Return the last k TradingCycle rows for this portfolio (desc order)."""
        with self.db_manager.get_session() as session:
            return session.query(TradingCycle) \
                .filter_by(portfolio_id=self.portfolio_id) \
                .order_by(TradingCycle.cycle_number.desc()) \
                .limit(k) \
                .all()

    def get_symbol_recent_cycle_prices(self, symbol: str, max_cycles: int = 5) -> List[float]:
        """Return recent snapshot prices for a symbol from last trading cycles (ascending by cycle)."""
        with self.db_manager.get_session() as session:
            cycles = session.query(TradingCycle) \
                .filter_by(portfolio_id=self.portfolio_id) \
                .order_by(TradingCycle.cycle_number.desc()) \
                .limit(max_cycles) \
                .all()
            cycles = list(reversed(cycles))
            prices: List[float] = []
            for c in cycles:
                cp = session.query(CyclePosition) \
                    .filter_by(cycle_id=c.id, symbol=symbol) \
                    .first()
                if cp:
                    prices.append(float(cp.current_price))
        return prices

    def compute_symbol_cycle_returns(self, symbol: str, lookback: int = 4) -> List[float]:
        """Compute up to last `lookback` cycle returns (%) for a symbol using cycle snapshots."""
        prices = self.get_symbol_recent_cycle_prices(symbol, max_cycles=lookback + 1)
        returns: List[float] = []
        if len(prices) >= 2:
            for i in range(1, len(prices)):
                prev, cur = prices[i-1], prices[i]
                if prev and prev > 0:
                    returns.append(((cur - prev) / prev) * 100.0)
        return returns[-lookback:]
