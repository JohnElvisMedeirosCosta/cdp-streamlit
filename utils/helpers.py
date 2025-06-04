# utils/helpers.py
"""
Funções auxiliares e utilitárias
"""

import re
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

def generate_unique_id() -> str:
    """Gera um ID único"""
    return str(uuid.uuid4())

def format_timestamp(timestamp: str) -> str:
    """Formata timestamp para exibição"""
    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime("%d/%m/%Y %H:%M:%S")
    except:
        return timestamp

def format_date(date_str: str) -> str:
    """Formata data para exibição"""
    try:
        if 'T' in date_str:
            dt = datetime.fromisoformat(date_str)
            return dt.strftime("%d/%m/%Y")
        else:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.strftime("%d/%m/%Y")
    except:
        return date_str

def clean_document(document: str) -> str:
    """Remove caracteres especiais de documentos"""
    if not document:
        return ""
    return re.sub(r'[^\d]', '', document)

def clean_phone(phone: str) -> str:
    """Remove caracteres especiais de telefones"""
    if not phone:
        return ""
    return re.sub(r'[^\d]', '', phone)

def format_document(document: str) -> str:
    """Formata documento para exibição (CPF/CNPJ)"""
    if not document:
        return ""
    
    clean_doc = clean_document(document)
    
    if len(clean_doc) == 11:  # CPF
        return f"{clean_doc[:3]}.{clean_doc[3:6]}.{clean_doc[6:9]}-{clean_doc[9:]}"
    elif len(clean_doc) == 14:  # CNPJ
        return f"{clean_doc[:2]}.{clean_doc[2:5]}.{clean_doc[5:8]}/{clean_doc[8:12]}-{clean_doc[12:]}"
    
    return document

def format_phone(phone: str) -> str:
    """Formata telefone para exibição"""
    if not phone:
        return ""
    
    clean_phone_num = clean_phone(phone)
    
    if len(clean_phone_num) == 11:  # Celular
        return f"({clean_phone_num[:2]}) {clean_phone_num[2]} {clean_phone_num[3:7]}-{clean_phone_num[7:]}"
    elif len(clean_phone_num) == 10:  # Fixo
        return f"({clean_phone_num[:2]}) {clean_phone_num[2:6]}-{clean_phone_num[6:]}"
    
    return phone

def format_cep(cep: str) -> str:
    """Formata CEP para exibição"""
    if not cep:
        return ""
    
    clean_cep = re.sub(r'[^\d]', '', cep)
    
    if len(clean_cep) == 8:
        return f"{clean_cep[:5]}-{clean_cep[5:]}"
    
    return cep

def validate_email(email: str) -> bool:
    """Valida formato de email"""
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_document(document: str) -> bool:
    """Valida documento (CPF/CNPJ)"""
    if not document:
        return False
    
    clean_doc = clean_document(document)
    
    # Validação simples de tamanho
    return len(clean_doc) in [11, 14]

def validate_phone(phone: str) -> bool:
    """Valida telefone"""
    if not phone:
        return False
    
    clean_phone_num = clean_phone(phone)
    
    # Validação simples de tamanho
    return len(clean_phone_num) in [10, 11]

def validate_cep(cep: str) -> bool:
    """Valida CEP"""
    if not cep:
        return False
    
    clean_cep = re.sub(r'[^\d]', '', cep)
    return len(clean_cep) == 8

def truncate_text(text: str, max_length: int = 50) -> str:
    """Trunca texto para exibição"""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."

def safe_get(dictionary: Dict, key: str, default: Any = None) -> Any:
    """Get seguro de dicionário"""
    return dictionary.get(key, default)

def calculate_percentage(part: int, total: int) -> float:
    """Calcula percentual"""
    if total == 0:
        return 0.0
    return round((part / total) * 100, 2)

def group_by_field(items: List[Dict], field: str) -> Dict[str, List[Dict]]:
    """Agrupa lista de dicionários por campo"""
    groups = {}
    for item in items:
        key = item.get(field, 'Unknown')
        if key not in groups:
            groups[key] = []
        groups[key].append(item)
    return groups

def sort_dict_by_value(dictionary: Dict, reverse: bool = True) -> Dict:
    """Ordena dicionário por valor"""
    return dict(sorted(dictionary.items(), key=lambda x: x[1], reverse=reverse))

def sanitize_filename(filename: str) -> str:
    """Sanitiza nome de arquivo"""
    # Remove caracteres especiais
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Remove espaços extras
    filename = re.sub(r'\s+', '_', filename.strip())
    return filename

def get_current_timestamp() -> str:
    """Retorna timestamp atual formatado"""
    return datetime.now().isoformat()

def parse_date(date_str: str) -> Optional[datetime]:
    """Parse flexível de data"""
    if not date_str:
        return None
    
    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y %H:%M:%S"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None

def is_empty_or_whitespace(value: Any) -> bool:
    """Verifica se valor está vazio ou apenas espaços"""
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    return False

def merge_dicts(*dicts: Dict) -> Dict:
    """Merge múltiplos dicionários"""
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result