# config.py
"""
Configurações globais do sistema CDP
"""

import os
from typing import List

# Configurações do banco de dados
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///customer_data.db")

# Configurações do matching
MATCH_THRESHOLD = 0.7
SIMILARITY_THRESHOLD = 0.8
LOW_SIMILARITY_THRESHOLD = 0.3

# Pesos para cálculo de similaridade
FIELD_WEIGHTS = {
    'documento': 0.40,
    'email': 0.25,
    'telefone': 0.20,
    'nome': 0.05,
    'endereco': 0.05,
    'data_nascimento': 0.05
}

# Configurações da interface
PAGE_TITLE = "Customer Data Platform"
PAGE_ICON = "👥"
LAYOUT = "wide"

# Campos válidos para CustomerData
VALID_CUSTOMER_FIELDS = [
    'nome', 'email', 'documento', 'telefone', 'endereco',
    'cidade', 'estado', 'cep', 'data_nascimento', 'profissao'
]

# Opções de fonte de dados
DATA_SOURCES = [
    "website", "mobile_app", "crm", "call_center", 
    "email_marketing", "social_media", "csv_import",
    "data_migration", "bulk_upload", "external_system", 
    "manual_import", "manual"
]

# Configurações de importação CSV
CSV_MAX_PREVIEW_ROWS = 10
CSV_ENCODING = "utf-8"
CSV_SEPARATOR = ","

# Configurações de paginação
DEFAULT_PAGE_SIZE = 50
MAX_DISPLAY_CUSTOMERS = 1000