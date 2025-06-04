# services/import_service.py
"""
Serviços para importação de dados em lote
"""

import pandas as pd
from typing import List, Dict, Any, Tuple
from models.schemas import CustomerData, ImportResult
from core.cdp import CustomerDataPlatform
from config import VALID_CUSTOMER_FIELDS, CSV_MAX_PREVIEW_ROWS

class ImportService:
    """Serviço para importação de clientes via CSV"""
    
    def __init__(self, cdp: CustomerDataPlatform):
        self.cdp = cdp
    
    def validate_csv_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Valida dados do CSV e retorna relatório"""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'statistics': {},
            'recognized_columns': [],
            'ignored_columns': []
        }
        
        # Verificar se o DataFrame não está vazio
        if df.empty:
            validation_result['is_valid'] = False
            validation_result['errors'].append("O arquivo CSV está vazio")
            return validation_result
        
        # Analisar colunas
        for col in df.columns:
            if col.lower() in VALID_CUSTOMER_FIELDS:
                validation_result['recognized_columns'].append(col)
            else:
                validation_result['ignored_columns'].append(col)
        
        # Verificar se há pelo menos uma coluna reconhecida
        if not validation_result['recognized_columns']:
            validation_result['is_valid'] = False
            validation_result['errors'].append("Nenhuma coluna reconhecida encontrada")
            return validation_result
        
        # Estatísticas de completude
        for col in validation_result['recognized_columns']:
            non_null_count = df[col].notna().sum()
            percentage = (non_null_count / len(df)) * 100
            validation_result['statistics'][col] = {
                'filled': non_null_count,
                'total': len(df),
                'percentage': round(percentage, 1)
            }
        
        # Verificar registros completamente vazios
        empty_rows = df.isnull().all(axis=1).sum()
        if empty_rows > 0:
            validation_result['warnings'].append(
                f"{empty_rows} linha(s) completamente vazia(s) serão ignoradas"
            )
        
        # Verificar documentos duplicados
        if 'documento' in df.columns:
            doc_col = df['documento'].dropna()
            if len(doc_col) != len(doc_col.unique()):
                duplicates = len(doc_col) - len(doc_col.unique())
                validation_result['warnings'].append(
                    f"{duplicates} documento(s) duplicado(s) encontrado(s)"
                )
        
        # Verificar emails duplicados
        if 'email' in df.columns:
            email_col = df['email'].dropna()
            if len(email_col) != len(email_col.unique()):
                duplicates = len(email_col) - len(email_col.unique())
                validation_result['warnings'].append(
                    f"{duplicates} email(s) duplicado(s) encontrado(s)"
                )
        
        return validation_result
    
    def process_csv_data(self, df: pd.DataFrame) -> List[Dict[str, str]]:
        """Processa dados do CSV para formato interno"""
        processed_data = []
        
        for index, row in df.iterrows():
            # Pular linhas completamente vazias
            if row.isnull().all():
                continue
            
            # Mapear colunas para o formato interno
            customer_data = {}
            
            for col in df.columns:
                col_lower = col.lower()
                if col_lower in VALID_CUSTOMER_FIELDS:
                    value = row[col]
                    if pd.notna(value) and str(value).strip():
                        customer_data[col_lower] = str(value).strip()
            
            if customer_data:  # Só adicionar se tiver pelo menos um campo
                processed_data.append(customer_data)
        
        return processed_data
    
    def analyze_potential_conflicts(self, customers: List[Dict[str, str]]) -> Dict[str, Any]:
        """Analisa conflitos potenciais antes da importação"""
        conflicts = []
        total_conflicts = 0
        
        for i, customer_dict in enumerate(customers):
            # Criar CustomerData apenas com campos válidos
            valid_fields = {k: v for k, v in customer_dict.items() 
                          if k in VALID_CUSTOMER_FIELDS}
            customer_data = CustomerData(**valid_fields)
            
            # Buscar matches
            matches = self.cdp._find_matching_customers(customer_data)
            
            if matches:
                best_match = matches[0]
                if not best_match.is_safe_match:
                    conflicts.append({
                        'row': i + 1,
                        'customer': customer_dict.get('nome', 'Nome não informado'),
                        'reason': best_match.reason,
                        'score': best_match.score,
                        'existing_customer_id': best_match.customer_id
                    })
                    total_conflicts += 1
        
        return {
            'potential_conflicts': total_conflicts,
            'details': conflicts
        }
    
    def execute_import(self, customers: List[Dict[str, str]], source: str, 
                      force_merge: bool = False, progress_callback=None) -> ImportResult:
        """Executa a importação dos clientes"""
        result = ImportResult()
        
        total_customers = len(customers)
        
        for i, customer_dict in enumerate(customers):
            try:
                # Callback de progresso se fornecido
                if progress_callback:
                    progress = (i + 1) / total_customers
                    progress_callback(progress, f"Processando cliente {i + 1} de {total_customers}")
                
                # Criar objeto CustomerData apenas com campos válidos
                valid_fields = {k: v for k, v in customer_dict.items() 
                              if k in VALID_CUSTOMER_FIELDS}
                customer_data = CustomerData(**valid_fields)
                
                # Adicionar cliente
                add_result = self.cdp.add_customer_data(
                    customer_data, 
                    source=source, 
                    force_merge=force_merge
                )
                
                result.total_processed += 1
                
                # Categorizar resultado
                if add_result['status'] == 'created':
                    result.created += 1
                elif add_result['status'] == 'updated':
                    result.updated += 1
                elif add_result['status'] == 'conflict_detected':
                    result.conflicts += 1
                else:
                    result.errors += 1
                
                # Salvar detalhes
                result.details.append({
                    'row': i + 1,
                    'customer': customer_dict.get('nome', 'Nome não informado'),
                    'status': add_result['status'],
                    'message': add_result['message'],
                    'customer_id': add_result.get('customer_id'),
                    'changes_made': add_result.get('changes_made', 0)
                })
                
            except Exception as e:
                result.errors += 1
                result.total_processed += 1
                result.details.append({
                    'row': i + 1,
                    'customer': customer_dict.get('nome', 'Nome não informado'),
                    'status': 'error',
                    'message': str(e),
                    'customer_id': None,
                    'changes_made': 0
                })
        
        return result
    
    def create_template_csv(self) -> str:
        """Cria um CSV template para download"""
        template_data = {
            'nome': ['João Silva', 'Maria Santos', 'Pedro Oliveira'],
            'email': ['joao@email.com', 'maria@email.com', 'pedro@email.com'],
            'documento': ['12345678901', '98765432100', '11122233344'],
            'telefone': ['11999887766', '11888776655', '11777665544'],
            'endereco': ['Rua A, 123', 'Av. B, 456', 'Rua C, 789'],
            'cidade': ['São Paulo', 'Rio de Janeiro', 'Belo Horizonte'],
            'estado': ['SP', 'RJ', 'MG'],
            'cep': ['01234567', '12345678', '23456789'],
            'data_nascimento': ['1985-05-15', '1990-08-20', '1975-12-10'],
            'profissao': ['Engenheiro', 'Médica', 'Professor']
        }
        
        template_df = pd.DataFrame(template_data)
        return template_df.to_csv(index=False)
    
    def generate_import_report(self, result: ImportResult, 
                             additional_info: Dict = None) -> Dict[str, Any]:
        """Gera relatório completo da importação"""
        report = {
            'summary': {
                'total_processed': result.total_processed,
                'created': result.created,
                'updated': result.updated,
                'conflicts': result.conflicts,
                'errors': result.errors,
                'success_rate': round((result.created + result.updated) / result.total_processed * 100, 2) if result.total_processed > 0 else 0
            },
            'details': result.details,
            'timestamp': pd.Timestamp.now().isoformat()
        }
        
        if additional_info:
            report['additional_info'] = additional_info
        
        return report