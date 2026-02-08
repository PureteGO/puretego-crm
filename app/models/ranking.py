from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base

class KeywordRanking(Base):
    """
    Ranks a specific keyword for a client.
    Tracks the target website/GMB profile and current position.
    """
    __tablename__ = 'keyword_rankings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, index=True)
    
    keyword = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True) # e.g. "Asunción, Paraguay"
    target_url = Column(String(255), nullable=True) # Domain to look for
    
    current_position_organic = Column(Integer, nullable=True) # 0 = Not found
    current_position_local = Column(Integer, nullable=True) # 0 = Not found
    
    last_check_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    client = relationship('Client', back_populates='rankings')
    history = relationship('RankHistory', back_populates='keyword_ranking', cascade='all, delete-orphan')

class RankHistory(Base):
    """
    Historical data points for a keyword ranking.
    """
    __tablename__ = 'rank_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword_ranking_id = Column(Integer, ForeignKey('keyword_rankings.id'), nullable=False, index=True)
    
    position_organic = Column(Integer, nullable=True)
    position_local = Column(Integer, nullable=True)
    
    check_date = Column(DateTime, server_default=func.now())
    
    keyword_ranking = relationship('KeywordRanking', back_populates='history')

class GMBInsight(Base):
    """
    Performance metrics for a Google Business Profile location.
    Tracks views, calls, clicks, etc. over time.
    """
    __tablename__ = 'gmb_insights'

    id = Column(Integer, primary_key=True, autoincrement=True)
    location_link_id = Column(Integer, ForeignKey('gmb_location_links.id'), nullable=False, index=True)
    
    date = Column(DateTime, nullable=False, index=True)
    metric = Column(String(50), nullable=False) # impressions, calls, website_clicks, etc.
    value = Column(Integer, default=0)
    
    synced_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    location_link = relationship('GMBLocationLink', backref='insights')
