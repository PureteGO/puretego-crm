"""
PURETEGO CRM - Google Connection Model
Stores OAuth tokens for connected Google Business Profile accounts
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base
from cryptography.fernet import Fernet
import os


class GoogleConnection(Base):
    """
    Represents a Google account connected via OAuth for a Company (tenant).
    Each company can have multiple Google connections for managing different
    GMB accounts.
    """
    
    __tablename__ = 'google_connections'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    
    # Google account identifier
    google_account_email = Column(String(255), nullable=True)
    
    # OAuth tokens (encrypted at rest)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    
    # OAuth scopes granted
    scopes = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    last_error = Column(Text, nullable=True)  # Store last API error if any
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    company = relationship('Company', back_populates='google_connections')
    location_links = relationship('GMBLocationLink', back_populates='google_connection', 
                                  cascade='all, delete-orphan')
    
    # Encryption key from environment
    _encryption_key = None
    
    @classmethod
    def _get_fernet(cls):
        """Get Fernet instance for encryption/decryption"""
        if cls._encryption_key is None:
            key = os.environ.get('TOKEN_ENCRYPTION_KEY')
            if key:
                cls._encryption_key = key.encode() if isinstance(key, str) else key
            else:
                # Generate a key if not set (development only)
                cls._encryption_key = Fernet.generate_key()
        return Fernet(cls._encryption_key)
    
    def set_access_token(self, token):
        """Encrypt and store access token"""
        if token:
            fernet = self._get_fernet()
            self.access_token = fernet.encrypt(token.encode()).decode()
    
    def get_access_token(self):
        """Decrypt and return access token"""
        if self.access_token:
            try:
                fernet = self._get_fernet()
                return fernet.decrypt(self.access_token.encode()).decode()
            except Exception:
                return self.access_token  # Fallback for non-encrypted tokens
        return None
    
    def set_refresh_token(self, token):
        """Encrypt and store refresh token"""
        if token:
            fernet = self._get_fernet()
            self.refresh_token = fernet.encrypt(token.encode()).decode()
    
    def get_refresh_token(self):
        """Decrypt and return refresh token"""
        if self.refresh_token:
            try:
                fernet = self._get_fernet()
                return fernet.decrypt(self.refresh_token.encode()).decode()
            except Exception:
                return self.refresh_token  # Fallback for non-encrypted tokens
        return None
    
    def is_token_expired(self):
        """Check if the access token has expired"""
        from datetime import datetime, timedelta
        if self.expires_at:
            # Consider expired 5 minutes before actual expiry
            return datetime.utcnow() >= (self.expires_at - timedelta(minutes=5))
        return True
    
    def to_dict(self):
        """Convert to dictionary (without sensitive data)"""
        return {
            'id': self.id,
            'company_id': self.company_id,
            'google_account_email': self.google_account_email,
            'is_active': self.is_active,
            'scopes': self.scopes,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'locations_count': len(self.location_links) if self.location_links else 0
        }
    
    def __repr__(self):
        return f'<GoogleConnection {self.google_account_email} for Company {self.company_id}>'
