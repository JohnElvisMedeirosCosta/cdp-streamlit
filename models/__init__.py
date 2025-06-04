"""
Módulo de modelos de dados
"""

from .database import CustomerModel, HistoryModel, DatabaseManager
from .schemas import CustomerData, Customer, MatchResult, HistoryEntry, ImportResult, SearchCriteria, SystemStatistics

__all__ = [
    'CustomerModel', 'HistoryModel', 'DatabaseManager',
    'CustomerData', 'Customer', 'MatchResult', 'HistoryEntry', 
    'ImportResult', 'SearchCriteria', 'SystemStatistics'
]