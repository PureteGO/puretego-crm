from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base

class ProjectNote(Base):
    """Notes/Chat messages for a specific project."""
    __tablename__ = 'project_notes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True) # Author
    
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    project = relationship('Project', back_populates='notes')
    author = relationship('User')

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'user_id': self.user_id,
            'user_name': self.author.name if self.author else 'Unknown',
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
