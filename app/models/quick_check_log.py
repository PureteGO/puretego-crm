from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base

class QuickCheckLog(Base):
    __tablename__ = 'quick_check_logs'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    business_name = Column(String(255), nullable=False)
    search_term = Column(String(255), nullable=True)
    
    # Location Data
    location_lat = Column(Float, nullable=True)
    location_lon = Column(Float, nullable=True)
    
    # Analysis Result
    score = Column(Integer, nullable=False)
    report_data = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Conversion Tracking
    converted_client_id = Column(Integer, ForeignKey('clients.id'), nullable=True)
    
    # Relationships
    user = relationship("User")
    converted_client = relationship("Client")

    def __repr__(self):
        return f'<QuickCheckLog {self.business_name} - {self.score}>'
