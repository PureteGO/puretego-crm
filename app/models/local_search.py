from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base

class LocalSearchKeyword(Base):
    """
    Keywords to be monitored for a client in Local Pack/Maps.
    """
    __tablename__ = 'local_search_keywords'

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, index=True)
    
    keyword = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True) # Override client Default location if needed
    
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    client = relationship('Client', backref='local_keywords')
    scan_results = relationship('LocalScanResult', back_populates='keyword_obj')


class LocalScanResult(Base):
    """
    Raw results from a SerpAPI Local Pack scan for a specific keyword.
    Stores data for both the client and competitors found in the same scan.
    """
    __tablename__ = 'local_scan_results'

    id = Column(Integer, primary_key=True, autoincrement=True)
    search_keyword_id = Column(Integer, ForeignKey('local_search_keywords.id'), nullable=False, index=True)
    
    scan_date = Column(DateTime, server_default=func.now(), index=True)
    
    # Data from SerpAPI local_results
    place_id = Column(String(255), nullable=True) # CID or Place ID
    title = Column(String(255), nullable=True)
    position = Column(Integer, nullable=True)
    rating = Column(Float, nullable=True)
    reviews = Column(Integer, nullable=True)
    type = Column(String(100), nullable=True)
    address = Column(String(255), nullable=True)
    
    is_client = Column(Boolean, default=False) # True if this result row matches the Client being tracked
    
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    keyword_obj = relationship('LocalSearchKeyword', back_populates='scan_results')


class LocalMetricsAggregated(Base):
    """
    Daily aggregated metrics for the 4-axis Radar Chart.
    Calculated from LocalScanResult data.
    """
    __tablename__ = 'local_metrics_aggregated'

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, index=True)
    
    scan_date = Column(DateTime, nullable=False, index=True) # Usually just the date part
    
    # The 4 Axes (0-100)
    visibility_score = Column(Float, default=0)
    avg_position_score = Column(Float, default=0)
    reviews_score = Column(Float, default=0)
    local_authority_score = Column(Float, default=0)
    
    # Market Averages (0-100) - Calculated from top competitors in the same scans
    market_avg_visibility = Column(Float, default=0)
    market_avg_position = Column(Float, default=0)
    market_avg_reviews = Column(Float, default=0)
    market_avg_authority = Column(Float, default=0)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    client = relationship('Client', backref='local_metrics')
