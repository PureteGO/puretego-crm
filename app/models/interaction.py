from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from config.database import Base
from datetime import datetime

class InteractionType(Base):
    """Types of interactions (Cold Visit, Follow-up Call, etc.)"""
    __tablename__ = 'interaction_types'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    icon = Column(String(50), default='fas fa-circle') # FontAwesome class
    is_call = Column(Boolean, default=False)
    
    # Relationships
    interactions = relationship("Interaction", back_populates="type")
    
    # Relationships for rules (explicit foreign keys needed)
    trigger_rules = relationship("CadenceRule", foreign_keys="CadenceRule.trigger_type_id", back_populates="trigger_type")
    suggested_rules = relationship("CadenceRule", foreign_keys="CadenceRule.suggested_next_type_id", back_populates="suggested_next_type")

    def __repr__(self):
        return f'<InteractionType {self.name}>'

class CadenceRule(Base):
    """Rules for suggesting the next step based on a completed interaction"""
    __tablename__ = 'cadence_rules'

    id = Column(Integer, primary_key=True)
    trigger_type_id = Column(Integer, ForeignKey('interaction_types.id'), nullable=False)
    suggested_next_type_id = Column(Integer, ForeignKey('interaction_types.id'), nullable=False)
    delay_days = Column(Integer, default=2)
    
    trigger_type = relationship("InteractionType", foreign_keys=[trigger_type_id], back_populates="trigger_rules")
    suggested_next_type = relationship("InteractionType", foreign_keys=[suggested_next_type_id], back_populates="suggested_rules")

    def __repr__(self):
        return f'<CadenceRule {self.trigger_type.name} -> {self.suggested_next_type.name} (+{self.delay_days}d)>'

class Interaction(Base):
    """A record of a visit or call (past or future)"""
    __tablename__ = 'interactions'

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    type_id = Column(Integer, ForeignKey('interaction_types.id'), nullable=False)
    
    date = Column(DateTime, default=datetime.now)
    # Status: done=completed, scheduled=future task, skipped=cancelled, missed=overdue
    status = Column(Enum('done', 'scheduled', 'skipped', 'missed', name='interaction_status'), default='done')
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    client = relationship("Client", back_populates="interactions")
    user = relationship("User", back_populates="interactions")
    type = relationship("InteractionType", back_populates="interactions")

    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'client_name': self.client.name if self.client else None,
            'type_name': self.type.name if self.type else None,
            'type_icon': self.type.icon if self.type else None,
            'is_call': self.type.is_call if self.type else False,
            'date': self.date.isoformat() if self.date else None,
            'status': self.status,
            'notes': self.notes
        }

    def __repr__(self):
        return f'<Interaction {self.id} {self.status}>'
