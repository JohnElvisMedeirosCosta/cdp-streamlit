# models/schemas.py
"""
Schemas e dataclasses para estruturas de dados
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any

@dataclass
class CustomerData:
    """Estrutura de dados do cliente"""
    email: Optional[str] = None
    documento: Optional[str] = None
    nome: Optional[str] = None
    telefone: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    cep: Optional[str] = None
    data_nascimento: Optional[str] = None
    profissao: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def is_empty(self) -> bool:
        """Verifica se todos os campos estão vazios"""
        return all(value is None or str(value).strip() == "" 
                  for value in asdict(self).values())

@dataclass
class MatchResult:
    """Resultado da análise de compatibilidade"""
    customer_id: str
    score: float
    conflicts: Dict[str, str]
    is_safe_match: bool
    reason: str

@dataclass
class HistoryEntry:
    """Entrada do histórico de alterações"""
    timestamp: str
    field: str
    old_value: Any
    new_value: Any
    source: str
    confidence: float

@dataclass
class Customer:
    """Cliente unificado com histórico"""
    id: str
    data: CustomerData
    created_at: str
    updated_at: str
    history: List[HistoryEntry]
    sources: List[str]
    confidence_score: float
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'data': self.data.to_dict(),
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'history': [asdict(entry) for entry in self.history],
            'sources': self.sources,
            'confidence_score': self.confidence_score
        }

@dataclass
class ImportResult:
    """Resultado de uma operação de importação"""
    total_processed: int = 0
    created: int = 0
    updated: int = 0
    conflicts: int = 0
    errors: int = 0
    details: List[Dict] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = []

@dataclass
class SearchCriteria:
    """Critérios de busca de clientes"""
    nome: Optional[str] = None
    email: Optional[str] = None
    documento: Optional[str] = None
    telefone: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    profissao: Optional[str] = None
    
    def to_dict(self) -> Dict[str, str]:
        """Retorna apenas campos não vazios"""
        return {k: v for k, v in asdict(self).items() 
                if v is not None and str(v).strip() != ""}

@dataclass
class SystemStatistics:
    """Estatísticas do sistema"""
    total_customers: int
    customers_with_updates: int
    average_confidence_score: float
    total_history_entries: int