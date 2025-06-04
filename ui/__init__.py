"""
Módulo de interface de usuário
"""

from .dashboard import show_dashboard
from .add_customer import show_add_customer
from .import_csv import show_import_csv
from .search_customers import show_search_customers
from .history import show_history
from .statistics import show_statistics

__all__ = [
    'show_dashboard', 'show_add_customer', 'show_import_csv',
    'show_search_customers', 'show_history', 'show_statistics'
]