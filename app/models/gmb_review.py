"""
PURETEGO CRM - GMB Review Model
Cache for synced Google Business Profile reviews
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base


class GMBReview(Base):
    """
    Cached Google Business Profile review.
    Stores reviews synced from Google for display in the CRM and analytics.
    """
    
    __tablename__ = 'gmb_reviews'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Reference to the location link
    location_link_id = Column(Integer, ForeignKey('gmb_location_links.id'), nullable=False, index=True)
    
    # Google's unique review identifier
    # Format: "accounts/123/locations/456/reviews/789"
    google_review_id = Column(String(255), unique=True, nullable=False)
    
    # Reviewer information
    reviewer_name = Column(String(255), nullable=True)
    reviewer_photo_url = Column(String(500), nullable=True)
    
    # Review content
    star_rating = Column(Integer, nullable=False)  # 1-5 stars
    comment = Column(Text, nullable=True)
    review_date = Column(DateTime, nullable=False)
    
    # Reply information
    reply_text = Column(Text, nullable=True)
    reply_date = Column(DateTime, nullable=True)
    
    # Sync metadata
    synced_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    location_link = relationship('GMBLocationLink', back_populates='reviews')
    
    def has_reply(self):
        """Check if the review has been replied to"""
        return self.reply_text is not None and len(self.reply_text.strip()) > 0
    
    def get_star_display(self):
        """Return star rating as emoji string"""
        return '⭐' * self.star_rating + '☆' * (5 - self.star_rating)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'location_link_id': self.location_link_id,
            'google_review_id': self.google_review_id,
            'reviewer_name': self.reviewer_name,
            'reviewer_photo_url': self.reviewer_photo_url,
            'star_rating': self.star_rating,
            'star_display': self.get_star_display(),
            'comment': self.comment,
            'review_date': self.review_date.isoformat() if self.review_date else None,
            'has_reply': self.has_reply(),
            'reply_text': self.reply_text,
            'reply_date': self.reply_date.isoformat() if self.reply_date else None,
            'synced_at': self.synced_at.isoformat() if self.synced_at else None
        }
    
    def __repr__(self):
        return f'<GMBReview {self.star_rating}★ by {self.reviewer_name}>'
