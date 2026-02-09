"""
PURETEGO CRM - GMB Location Link Model
Links CRM Clients to Google Business Profile locations
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base


class GMBLocationLink(Base):
    """
    Represents the link between a Maps2GO Client and a Google Business Profile location.
    This enables mapping multiple locations from different Google accounts to CRM clients.
    """
    
    __tablename__ = 'gmb_location_links'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    
    # Reference to the Google connection (which account to use)
    google_connection_id = Column(Integer, ForeignKey('google_connections.id'), nullable=False, index=True)
    
    # Reference to the CRM client
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=True, index=True)
    
    # Google Business Profile location identifier
    # Format: "accounts/123456789/locations/987654321"
    gmb_location_name = Column(String(255), nullable=False)
    
    # Display name for the location (cached from Google)
    gmb_location_title = Column(String(255), nullable=True)
    
    # Address (cached from Google)
    gmb_location_address = Column(String(500), nullable=True)
    
    # Is this the primary location for this client?
    is_primary = Column(Boolean, default=True, nullable=False)
    
    # Sync status
    last_sync_at = Column(DateTime, nullable=True)
    sync_error = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Unique constraint: one client can only be linked to one location per connection
    __table_args__ = (
        UniqueConstraint('client_id', 'gmb_location_name', name='uq_client_location'),
    )
    
    # Relationships
    company = relationship('Company', back_populates='gmb_location_links')
    google_connection = relationship('GoogleConnection', back_populates='location_links')
    client = relationship('Client', back_populates='gmb_location_links')
    reviews = relationship('GMBReview', back_populates='location_link', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'company_id': self.company_id,
            'google_connection_id': self.google_connection_id,
            'client_id': self.client_id,
            'client_name': self.client.name if self.client else None,
            'gmb_location_name': self.gmb_location_name,
            'gmb_location_title': self.gmb_location_title,
            'gmb_location_address': self.gmb_location_address,
            'is_primary': self.is_primary,
            'last_sync_at': self.last_sync_at.isoformat() if self.last_sync_at else None,
            'sync_error': self.sync_error,
            'reviews_count': len(self.reviews) if self.reviews else 0
        }
    
    def set_as_primary(self, db_session):
        """Sets this location as primary and unsets all other locations for the same client."""
        if not self.client_id:
            return
            
        # Get all links for this client
        other_links = db_session.query(GMBLocationLink).filter(
            GMBLocationLink.client_id == self.client_id,
            GMBLocationLink.id != self.id
        ).all()
        
        for link in other_links:
            link.is_primary = False
            
        self.is_primary = True
        db_session.commit()

    def __repr__(self):
        return f'<GMBLocationLink Client:{self.client_id} -> {self.gmb_location_title}>'
