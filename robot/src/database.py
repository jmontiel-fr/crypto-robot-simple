"""
Database models for the crypto trading robot using SQLAlchemy 1.4
Supports both PostgreSQL and SQLite databases
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from sqlalchemy.types import TypeDecorator, TEXT
import json
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

Base = declarative_base()

# Custom JSON type that works with both PostgreSQL and SQLite
class JSON(TypeDecorator):
    """JSON type for cross-database compatibility"""
    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value, cls=DateTimeEncoder)
        return value

    def process_result_value(self, value, dialect):
        if value is not None and value != '':
            try:
                value = json.loads(value)
            except (json.JSONDecodeError, ValueError):
                # Handle invalid JSON by returning None
                value = None
        else:
            value = None
        return value

class Portfolio(Base):
    """Portfolio table - stores current portfolio state"""
    __tablename__ = 'portfolios'
    
    id = Column(Integer, primary_key=True)
    bnb_reserve = Column(Float, nullable=False, default=0.0)
    current_cycle = Column(Integer, nullable=False, default=0)
    is_frozen = Column(Boolean, nullable=False, default=False)
    freeze_reason = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    positions = relationship("Position", back_populates="portfolio", cascade="all, delete-orphan")
    cycles = relationship("TradingCycle", back_populates="portfolio", cascade="all, delete-orphan")

class Position(Base):
    """Position table - stores individual cryptocurrency positions"""
    __tablename__ = 'positions'
    
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=False)
    symbol = Column(String(20), nullable=False)
    quantity = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    entry_date = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="positions")
    
    @property
    def current_value(self) -> float:
        """Calculate current value of the position"""
        return self.quantity * self.current_price
    
    @property
    def entry_value(self) -> float:
        """Calculate entry value of the position"""
        return self.quantity * self.entry_price
    
    @property
    def pnl(self) -> float:
        """Calculate profit/loss"""
        return self.current_value - self.entry_value
    
    @property
    def pnl_percentage(self) -> float:
        """Calculate P&L percentage"""
        if self.entry_value == 0:
            return 0.0
        return (self.pnl / self.entry_value) * 100

class TradingCycle(Base):
    """Trading cycle table - stores historical cycle data"""
    __tablename__ = 'trading_cycles'
    
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=False)
    cycle_number = Column(Integer, nullable=False)
    bnb_reserve = Column(Float, nullable=False)
    portfolio_value = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)
    actions_taken = Column(JSON, nullable=True)  # Store as JSON array
    portfolio_breakdown = Column(JSON, nullable=True)  # Store individual crypto holdings
    cycle_date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="cycles")
    cycle_positions = relationship("CyclePosition", back_populates="cycle", cascade="all, delete-orphan")

class CyclePosition(Base):
    """Cycle position table - stores position snapshots for each cycle"""
    __tablename__ = 'cycle_positions'
    
    id = Column(Integer, primary_key=True)
    cycle_id = Column(Integer, ForeignKey('trading_cycles.id'), nullable=False)
    symbol = Column(String(20), nullable=False)
    quantity = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    current_value = Column(Float, nullable=False)
    pnl_percentage = Column(Float, nullable=False)
    entry_date = Column(DateTime(timezone=True), nullable=False)
    
    # Relationships
    cycle = relationship("TradingCycle", back_populates="cycle_positions")

class Simulation(Base):
    """Simulation table - stores simulation runs and parameters"""
    __tablename__ = 'simulations'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    duration_days = Column(Integer, nullable=False)
    cycle_length_minutes = Column(Integer, nullable=False)
    starting_reserve = Column(Float, nullable=False)
    final_portfolio_value = Column(Float, nullable=True)
    final_reserve_value = Column(Float, nullable=True)
    final_total_value = Column(Float, nullable=True)
    total_cycles = Column(Integer, nullable=True)
    data_source = Column(String(50), nullable=True, default='simulated')  # 'historical' or 'simulated'
    engine_version = Column(String(50), nullable=True, default='fixed_sim6_v3.0')  # Engine strategy version
    status = Column(String(20), nullable=False, default='pending')  # 'pending', 'running', 'completed', 'failed'
    error_message = Column(Text, nullable=True)
    # New performance analytics metrics (optional, may be null if older simulations)
    turnover_notional = Column(Float, nullable=True)
    turnover_ratio = Column(Float, nullable=True)
    realized_pnl = Column(Float, nullable=True)
    fee_estimate = Column(Float, nullable=True)
    # Enhanced realistic mode columns
    realistic_mode = Column(Boolean, default=False, nullable=True)
    total_trading_costs = Column(Float, default=0.0, nullable=True)
    failed_trades = Column(Integer, default=0, nullable=True)
    average_execution_delay = Column(Float, default=0.0, nullable=True)
    success_rate = Column(Float, default=100.0, nullable=True)
    calibration_profile = Column(String(100), nullable=True)  # Name of calibration profile used
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    simulation_cycles = relationship("SimulationCycle", back_populates="simulation", cascade="all, delete-orphan")

class SimulationCycle(Base):
    """Simulation cycle table - stores cycle data for simulations"""
    __tablename__ = 'simulation_cycles'
    
    id = Column(Integer, primary_key=True)
    simulation_id = Column(Integer, ForeignKey('simulations.id'), nullable=False)
    cycle_number = Column(Integer, nullable=False)
    portfolio_value = Column(Float, nullable=False)
    bnb_reserve = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)
    actions_taken = Column(JSON, nullable=True)
    portfolio_breakdown = Column(JSON, nullable=True)  # Store individual crypto holdings
    # Enhanced realistic mode columns
    trading_costs = Column(Float, default=0.0, nullable=True)
    execution_delay = Column(Float, default=0.0, nullable=True)
    failed_orders = Column(Integer, default=0, nullable=True)
    market_conditions = Column(Text, nullable=True)
    cycle_date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    simulation = relationship("Simulation", back_populates="simulation_cycles")

class StrategyPerformance(Base):
    """Strategy performance table - tracks performance metrics for each strategy"""
    __tablename__ = 'strategy_performance'
    
    id = Column(Integer, primary_key=True)
    strategy_name = Column(String(50), nullable=False)
    cycle_return = Column(Float, nullable=True)
    portfolio_value = Column(Float, nullable=True)
    market_regime = Column(String(20), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<StrategyPerformance(strategy='{self.strategy_name}', return={self.cycle_return:.2%})>"

class StrategySwitch(Base):
    """Strategy switches table - logs when strategies are switched"""
    __tablename__ = 'strategy_switches'
    
    id = Column(Integer, primary_key=True)
    old_strategy = Column(String(50), nullable=True)
    new_strategy = Column(String(50), nullable=False)
    reason = Column(String(200), nullable=True)
    market_conditions = Column(JSON, nullable=True)  # JSON field for market analysis data
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<StrategySwitch('{self.old_strategy}' -> '{self.new_strategy}')>"

class DatabaseManager:
    """Database manager for handling connections and operations"""
    
    def __init__(self, database_url: str = None, db_type: str = None):
        """
        Initialize database manager
        
        Args:
            database_url: Full database URL
            db_type: Database type ('postgresql' or 'sqlite'). If not provided, inferred from DATABASE_TYPE env var or URL
        """
        # Determine database type
        if db_type is None:
            db_type = os.getenv('DATABASE_TYPE', 'sqlite').lower()
        
        self.db_type = db_type
        
        if database_url is None:
            database_url = self._build_database_url(db_type)
            
        # Detect database type from URL if not explicitly provided
        if database_url.startswith('sqlite'):
            self.db_type = 'sqlite'
        elif database_url.startswith('postgresql'):
            self.db_type = 'postgresql'
        
        # Configure engine based on database type
        engine_kwargs = {'echo': False}
        
        if self.db_type == 'sqlite':
            # SQLite specific configurations
            engine_kwargs.update({
                'pool_pre_ping': True,
                'connect_args': {'check_same_thread': False}
            })
        elif self.db_type == 'postgresql':
            # PostgreSQL specific configurations
            engine_kwargs.update({
                'pool_pre_ping': True,
                'pool_recycle': 300
            })
        
        self.engine = create_engine(database_url, **engine_kwargs)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def _build_database_url(self, db_type: str) -> str:
        """Build database URL based on type and environment variables"""
        if db_type == 'sqlite':
            # SQLite configuration - support new DATABASE_PATH and DATABASE_FILE variables
            database_path = os.getenv('DATABASE_PATH', 'data')
            database_file = os.getenv('DATABASE_FILE', 'cryptorobot.db')
            
            # Fallback to legacy SQLITE_FILE if new variables not set
            if database_path == 'data' and database_file == 'cryptorobot.db':
                legacy_sqlite_file = os.getenv('SQLITE_FILE')
                if legacy_sqlite_file:
                    db_file = legacy_sqlite_file
                else:
                    # Use forward slashes for cross-platform compatibility (especially in containers)
                    db_file = f"{database_path}/{database_file}"
            else:
                # Use forward slashes for cross-platform compatibility (especially in containers)
                db_file = f"{database_path}/{database_file}"
            
            # Ensure directory exists
            db_dir = os.path.dirname(db_file)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
                
            return f"sqlite:///{db_file}"
            
        elif db_type == 'postgresql':
            # PostgreSQL configuration
            db_host = os.getenv('DB_HOST', 'localhost')
            db_port = os.getenv('DB_PORT', '5432')
            db_name = os.getenv('DB_NAME', 'cryptorobot_db')
            db_user = os.getenv('DB_USER', 'postgres')
            db_password = os.getenv('DB_PASSWORD', '')
            
            return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
        
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
        # After creating tables, attempt lightweight schema upgrades (non-destructive)
        try:
            self.upgrade_schema_add_simulation_metrics()
        except Exception as e:
            # Don't crash application if upgrade fails; just log
            print(f"Schema upgrade (simulation metrics) skipped/failed: {e}")
        
    def get_session(self):
        """Get a database session"""
        return self.SessionLocal()
    
    def drop_tables(self):
        """Drop all database tables (use with caution)"""
        Base.metadata.drop_all(bind=self.engine)
    
    def get_database_info(self) -> dict:
        """Get information about the current database configuration"""
        return {
            'type': self.db_type,
            'url': str(self.engine.url).replace(self.engine.url.password or '', '***') if self.engine.url.password else str(self.engine.url),
            'driver': self.engine.dialect.name
        }
        return self.SessionLocal()
    
    def drop_tables(self):
        """Drop all database tables (use with caution)"""
        Base.metadata.drop_all(bind=self.engine)

    # ------------------ Lightweight Schema Upgrades ------------------ #
    def upgrade_schema_add_simulation_metrics(self):
        """Ensure new simulation metric columns exist (idempotent).

        Adds the following nullable REAL columns to simulations if missing:
          - turnover_notional
          - turnover_ratio
          - realized_pnl
          - fee_estimate

        Works for SQLite and PostgreSQL.
        """
        required_columns = {
            'turnover_notional': 'turnover_notional REAL NULL',
            'turnover_ratio': 'turnover_ratio REAL NULL',
            'realized_pnl': 'realized_pnl REAL NULL',
            'fee_estimate': 'fee_estimate REAL NULL'
        }

        if self.db_type == 'sqlite':
            with self.engine.connect() as conn:
                existing = {row[1] for row in conn.execute(text('PRAGMA table_info(simulations)'))}
                added = []
                for col_name, ddl in required_columns.items():
                    if col_name not in existing:
                        conn.execute(text(f'ALTER TABLE simulations ADD COLUMN {ddl}'))
                        added.append(col_name)
                if added:
                    print(f"Added simulation metric columns: {', '.join(added)}")
        elif self.db_type == 'postgresql':
            with self.engine.connect() as conn:
                for col_name in required_columns.keys():
                    # PostgreSQL IF NOT EXISTS syntax for add column
                    conn.execute(text(f'ALTER TABLE simulations ADD COLUMN IF NOT EXISTS {col_name} DOUBLE PRECISION'))
        else:
            # Unsupported DB type for automatic upgrade; ignore silently
            pass

# Global database manager instance
db_manager = None

def get_db_manager() -> DatabaseManager:
    """Get global database manager instance"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager

def init_database():
    """Initialize database with tables"""
    manager = get_db_manager()
    manager.create_tables()
    return manager
