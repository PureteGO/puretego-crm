"""
PURETEGO CRM - Health Check Model
Modelo de análise do Google Meu Negócio
"""

from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base
import json


class HealthCheck(Base):
    """Modelo de Health Check do perfil Google Meu Negócio"""
    
    __tablename__ = 'health_checks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey('clients.id', ondelete='CASCADE'), nullable=False, index=True)
    score = Column(Integer, nullable=False, index=True)
    report_data = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relacionamentos
    client = relationship('Client', back_populates='health_checks')
    
    def __init__(self, client_id, score, report_data=None):
        self.client_id = client_id
        self.score = score
        self.report_data = report_data if report_data else {}
    
    def set_report_data(self, data):
        """Define os dados do relatório"""
        if isinstance(data, dict):
            self.report_data = data
        elif isinstance(data, str):
            self.report_data = json.loads(data)
    
    def get_report_data(self):
        """Retorna os dados do relatório"""
        return self.report_data if self.report_data else {}
    
    def get_score_color(self):
        """Retorna a cor baseada na pontuação"""
        if self.score >= 70:
            return 'success'
        elif self.score >= 40:
            return 'warning'
        else:
            return 'danger'
    
    def get_score_status(self):
        """Retorna o status baseado na pontuação"""
        if self.score >= 70:
            return 'Excelente'
        elif self.score >= 40:
            return 'Moderado'
        else:
            return 'Crítico'
    
    def to_dict(self, include_relations=False):
        """Converte o objeto para dicionário"""
        data = {
            'id': self.id,
            'client_id': self.client_id,
            'score': self.score,
            'score_color': self.get_score_color(),
            'score_status': self.get_score_status(),
            'report_data': self.get_report_data(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_relations:
            data['client'] = self.client.to_dict() if self.client else None
        
        return data
    
    def __repr__(self):
        return f'<HealthCheck {self.id} - Score: {self.score}>'
