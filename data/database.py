
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
import datetime

Base = declarative_base()

class Asset(Base):
    __tablename__ = 'assets'
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String, unique=True, nullable=False)
    name = Column(String)
    sector = Column(String)
    subsector = Column(String)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    fundamentals = relationship("FundamentalData", back_populates="asset")
    prices = relationship("PriceData", back_populates="asset")

    def __repr__(self):
        return f"<Asset(ticker='{self.ticker}')>"

class FundamentalData(Base):
    """
    Stores fundamental data points. 
    Note: 'fundamentus' often provides current snapshot. 
    We timestamp it to build our own history over time if we run this daily.
    """
    __tablename__ = 'fundamental_data'
    
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False)
    date = Column(Date, nullable=False) # Date of data collection or reference date
    
    # Valuation
    p_l = Column(Float)
    p_vp = Column(Float)
    psr = Column(Float)
    div_yield = Column(Float)
    
    # Profitability
    roe = Column(Float)
    roic = Column(Float)
    net_margin = Column(Float)
    
    # Growth (available from snapshot)
    revenue_growth_5y = Column(Float) # c5y in fundamentus
    
    # Liquidity
    liq_2m = Column(Float) # Average daily liquidity over 2 months
    
    # Absolute values
    market_cap = Column(Float)
    net_debt = Column(Float)
    net_debt_ebitda = Column(Float) # Calculated from details
    
    asset = relationship("Asset", back_populates="fundamentals")

class PriceData(Base):
    """
    Daily price data.
    """
    __tablename__ = 'price_data'
    
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False)
    date = Column(Date, nullable=False)
    
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    
    asset = relationship("Asset", back_populates="prices")

class EconomicSeries(Base):
    __tablename__ = 'economic_series'
    
    code = Column(String, primary_key=True) # e.g. 'PRECOS12_IPCA12'
    name = Column(String)
    source = Column(String) # 'IPEADATA'
    frequency = Column(String) # 'Daily', 'Monthly', etc.
    
    data_points = relationship("EconomicData", back_populates="series")

class EconomicData(Base):
    __tablename__ = 'economic_data'
    
    id = Column(Integer, primary_key=True)
    series_code = Column(String, ForeignKey('economic_series.code'), nullable=False)
    date = Column(Date, nullable=False)
    value = Column(Float)
    
    series = relationship("EconomicSeries", back_populates="data_points")

def init_db(db_path='sqlite:///stocks.db'):
    engine = create_engine(db_path)
    Base.metadata.create_all(engine)
    return engine
