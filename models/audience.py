# models/audience.py
"""
Modelos para sistema de audiências
"""

import uuid
import json
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Union
from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean
from models.database import Base

class AudienceModel(Base):
    """Modelo de audiência no banco de dados"""
    __tablename__ = 'audiences'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    criteria = Column(Text)  # JSON string com critérios
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    created_by = Column(String, default='system')
    customer_count = Column(Integer, default=0)
    last_extracted_at = Column(DateTime)

@dataclass
class AudienceCriteria:
    """Critérios para definir uma audiência"""
    # Critérios básicos
    nome_contains: Optional[str] = None
    email_contains: Optional[str] = None
    documento_equals: Optional[str] = None
    telefone_contains: Optional[str] = None
    
    # Critérios geográficos
    cidade_equals: Optional[str] = None
    estado_equals: Optional[str] = None
    cep_starts_with: Optional[str] = None
    
    # Critérios profissionais
    profissao_contains: Optional[str] = None
    
    # Critérios de data
    data_nascimento_from: Optional[str] = None
    data_nascimento_to: Optional[str] = None
    aniversariantes_mes: Optional[int] = None  # 1-12 para filtrar por mês de aniversário
    created_from: Optional[str] = None
    created_to: Optional[str] = None
    
    # Critérios de qualidade
    confidence_score_min: Optional[float] = None
    confidence_score_max: Optional[float] = None
    has_email: Optional[bool] = None
    has_telefone: Optional[bool] = None
    has_endereco: Optional[bool] = None
    
    # Critérios de fonte
    sources_include: Optional[List[str]] = None
    sources_exclude: Optional[List[str]] = None
    
    # Critérios de histórico
    has_history: Optional[bool] = None
    updated_in_last_days: Optional[int] = None
    
    def to_dict(self) -> Dict:
        """Converte para dicionário removendo valores None"""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    def is_empty(self) -> bool:
        """Verifica se não há critérios definidos"""
        return len(self.to_dict()) == 0

@dataclass
class Audience:
    """Audiência completa com metadados"""
    id: str
    name: str
    description: str
    criteria: AudienceCriteria
    is_active: bool
    created_at: str
    updated_at: str
    created_by: str
    customer_count: int
    last_extracted_at: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'criteria': self.criteria.to_dict(),
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'created_by': self.created_by,
            'customer_count': self.customer_count,
            'last_extracted_at': self.last_extracted_at
        }

@dataclass
class AudienceExtractionResult:
    """Resultado de extração de audiência"""
    audience_id: str
    audience_name: str
    total_customers: int
    extraction_timestamp: str
    criteria_used: Dict[str, Any]
    csv_data: str
    
    def to_dict(self) -> Dict:
        return asdict(self)