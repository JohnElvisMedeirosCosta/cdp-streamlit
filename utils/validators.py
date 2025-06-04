# utils/validators.py
"""
Validadores de dados específicos do domínio
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from models.schemas import CustomerData

class CustomerDataValidator:
    """Validador para dados de cliente"""
    
    @staticmethod
    def validate_customer_data(data: CustomerData) -> Tuple[bool, List[str]]:
        """
        Valida dados do cliente
        Retorna: (is_valid, list_of_errors)
        """
        errors = []
        
        # Validar email
        if data.email and not CustomerDataValidator._is_valid_email(data.email):
            errors.append("Formato de email inválido")
        
        # Validar documento
        if data.documento and not CustomerDataValidator._is_valid_document(data.documento):
            errors.append("Documento deve ter 11 dígitos (CPF) ou 14 dígitos (CNPJ)")
        
        # Validar telefone
        if data.telefone and not CustomerDataValidator._is_valid_phone(data.telefone):
            errors.append("Telefone deve ter 10 ou 11 dígitos")
        
        # Validar CEP
        if data.cep and not CustomerDataValidator._is_valid_cep(data.cep):
            errors.append("CEP deve ter 8 dígitos")
        
        # Validar data de nascimento
        if data.data_nascimento and not CustomerDataValidator._is_valid_birth_date(data.data_nascimento):
            errors.append("Data de nascimento deve estar no formato YYYY-MM-DD")
        
        # Verificar se pelo menos um campo está preenchido
        if data.is_empty():
            errors.append("Pelo menos um campo deve ser preenchido")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Valida formato de email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email.strip()))
    
    @staticmethod
    def _is_valid_document(document: str) -> bool:
        """Valida documento (CPF/CNPJ)"""
        # Remove caracteres não numéricos
        clean_doc = re.sub(r'[^\d]', '', document)
        
        # Verifica tamanho
        if len(clean_doc) not in [11, 14]:
            return False
        
        # Validação básica: não pode ser todos iguais
        if len(set(clean_doc)) == 1:
            return False
        
        return True
    
    @staticmethod
    def _is_valid_phone(phone: str) -> bool:
        """Valida telefone"""
        # Remove caracteres não numéricos
        clean_phone = re.sub(r'[^\d]', '', phone)
        
        # Verifica tamanho (10 para fixo, 11 para celular)
        return len(clean_phone) in [10, 11]
    
    @staticmethod
    def _is_valid_cep(cep: str) -> bool:
        """Valida CEP"""
        # Remove caracteres não numéricos
        clean_cep = re.sub(r'[^\d]', '', cep)
        
        # Verifica tamanho
        return len(clean_cep) == 8
    
    @staticmethod
    def _is_valid_birth_date(date_str: str) -> bool:
        """Valida data de nascimento"""
        pattern = r'^\d{4}-\d{2}-\d{2}$'
        if not re.match(pattern, date_str):
            return False
        
        try:
            from datetime import datetime
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False

class CSVDataValidator:
    """Validador para dados de CSV"""
    
    @staticmethod
    def validate_csv_structure(df) -> Dict[str, Any]:
        """Valida estrutura do CSV"""
        from config import VALID_CUSTOMER_FIELDS
        
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'recognized_columns': [],
            'ignored_columns': []
        }
        
        # Verificar se está vazio
        if df.empty:
            result['is_valid'] = False
            result['errors'].append("CSV está vazio")
            return result
        
        # Analisar colunas
        for col in df.columns:
            if col.lower() in VALID_CUSTOMER_FIELDS:
                result['recognized_columns'].append(col)
            else:
                result['ignored_columns'].append(col)
        
        # Verificar se há colunas reconhecidas
        if not result['recognized_columns']:
            result['is_valid'] = False
            result['errors'].append("Nenhuma coluna reconhecida encontrada")
        
        # Verificar duplicatas
        CSVDataValidator._check_duplicates(df, result)
        
        return result
    
    @staticmethod
    def _check_duplicates(df, result: Dict[str, Any]):
        """Verifica duplicatas no CSV"""
        # Verificar documentos duplicados
        if 'documento' in df.columns:
            doc_col = df['documento'].dropna()
            if len(doc_col) != len(doc_col.unique()):
                duplicates = len(doc_col) - len(doc_col.unique())
                result['warnings'].append(f"{duplicates} documento(s) duplicado(s)")
        
        # Verificar emails duplicados
        if 'email' in df.columns:
            email_col = df['email'].dropna()
            if len(email_col) != len(email_col.unique()):
                duplicates = len(email_col) - len(email_col.unique())
                result['warnings'].append(f"{duplicates} email(s) duplicado(s)")

class ImportDataValidator:
    """Validador para dados de importação"""
    
    @staticmethod
    def validate_import_batch(customers_data: List[Dict[str, str]]) -> Dict[str, Any]:
        """Valida lote de dados para importação"""
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'valid_records': 0,
            'invalid_records': 0,
            'record_errors': {}
        }
        
        for i, customer_dict in enumerate(customers_data):
            try:
                # Criar CustomerData para validação
                from config import VALID_CUSTOMER_FIELDS
                valid_fields = {k: v for k, v in customer_dict.items() 
                              if k in VALID_CUSTOMER_FIELDS}
                customer_data = CustomerData(**valid_fields)
                
                # Validar dados
                is_valid, errors = CustomerDataValidator.validate_customer_data(customer_data)
                
                if is_valid:
                    result['valid_records'] += 1
                else:
                    result['invalid_records'] += 1
                    result['record_errors'][i + 1] = errors
                    
            except Exception as e:
                result['invalid_records'] += 1
                result['record_errors'][i + 1] = [str(e)]
        
        # Se há muitos registros inválidos, marcar como inválido
        if result['invalid_records'] > result['valid_records'] * 0.5:
            result['is_valid'] = False
            result['errors'].append("Muitos registros inválidos encontrados")
        
        return result

class BusinessRuleValidator:
    """Validador de regras de negócio"""
    
    @staticmethod
    def validate_merge_operation(existing_customer: CustomerData, 
                                new_customer: CustomerData) -> Tuple[bool, List[str]]:
        """Valida se a operação de merge é segura"""
        warnings = []
        
        # Verificar conflitos críticos
        critical_conflicts = BusinessRuleValidator._check_critical_conflicts(
            existing_customer, new_customer
        )
        
        if critical_conflicts:
            return False, critical_conflicts
        
        # Verificar mudanças significativas
        significant_changes = BusinessRuleValidator._check_significant_changes(
            existing_customer, new_customer
        )
        
        warnings.extend(significant_changes)
        
        return True, warnings
    
    @staticmethod
    def _check_critical_conflicts(existing: CustomerData, new: CustomerData) -> List[str]:
        """Verifica conflitos críticos que impedem merge"""
        conflicts = []
        
        # Conflito de documento
        if (existing.documento and new.documento and 
            existing.documento != new.documento):
            conflicts.append("Conflito de documento: valores diferentes")
        
        # Conflito de email com domínios muito diferentes
        if (existing.email and new.email and 
            existing.email != new.email):
            existing_domain = existing.email.split('@')[1] if '@' in existing.email else ''
            new_domain = new.email.split('@')[1] if '@' in new.email else ''
            
            if existing_domain and new_domain and existing_domain != new_domain:
                conflicts.append("Conflito de email: domínios diferentes")
        
        return conflicts
    
    @staticmethod
    def _check_significant_changes(existing: CustomerData, new: CustomerData) -> List[str]:
        """Verifica mudanças significativas que merecem atenção"""
        changes = []
        
        # Mudança de nome significativa
        if existing.nome and new.nome:
            from core.matcher import CustomerMatcher
            similarity = CustomerMatcher.similarity_score(
                existing.nome.lower(), new.nome.lower()
            )
            if similarity < 0.7:
                changes.append("Mudança significativa no nome")
        
        # Mudança de telefone
        if (existing.telefone and new.telefone and 
            existing.telefone != new.telefone):
            changes.append("Mudança de telefone")
        
        # Mudança de endereço
        if (existing.endereco and new.endereco and 
            existing.endereco != new.endereco):
            changes.append("Mudança de endereço")
        
        return changes

class SystemIntegrityValidator:
    """Validador de integridade do sistema"""
    
    @staticmethod
    def validate_customer_consistency(customer) -> Tuple[bool, List[str]]:
        """Valida consistência interna do cliente"""
        issues = []
        
        # Verificar se ID existe
        if not customer.id:
            issues.append("Cliente sem ID")
        
        # Verificar se tem pelo menos dados básicos
        if customer.data.is_empty():
            issues.append("Cliente sem dados preenchidos")
        
        # Verificar consistência de timestamps
        try:
            from datetime import datetime
            created = datetime.fromisoformat(customer.created_at)
            updated = datetime.fromisoformat(customer.updated_at)
            
            if updated < created:
                issues.append("Data de atualização anterior à criação")
                
        except Exception:
            issues.append("Timestamps inválidos")
        
        # Verificar score de confiança
        if not (0.0 <= customer.confidence_score <= 1.0):
            issues.append("Score de confiança fora do intervalo válido")
        
        # Verificar se fontes existem
        if not customer.sources:
            issues.append("Cliente sem fontes de dados")
        
        return len(issues) == 0, issues
    
    @staticmethod
    def validate_database_integrity(cdp) -> Dict[str, Any]:
        """Valida integridade geral do banco de dados"""
        result = {
            'is_healthy': True,
            'issues': [],
            'statistics': {},
            'recommendations': []
        }
        
        try:
            # Obter todos os clientes
            customers = cdp.get_all_customers()
            stats = cdp.get_statistics()
            
            result['statistics'] = {
                'total_customers': len(customers),
                'customers_with_issues': 0,
                'orphaned_history': 0,
                'duplicate_documents': 0,
                'duplicate_emails': 0
            }
            
            # Verificar cada cliente
            customers_with_issues = 0
            duplicate_docs = set()
            duplicate_emails = set()
            seen_docs = set()
            seen_emails = set()
            
            for customer in customers:
                is_consistent, issues = SystemIntegrityValidator.validate_customer_consistency(customer)
                if not is_consistent:
                    customers_with_issues += 1
                    result['issues'].extend([f"Cliente {customer.id[:8]}: {issue}" for issue in issues])
                
                # Verificar duplicatas
                if customer.data.documento:
                    if customer.data.documento in seen_docs:
                        duplicate_docs.add(customer.data.documento)
                    seen_docs.add(customer.data.documento)
                
                if customer.data.email:
                    if customer.data.email in seen_emails:
                        duplicate_emails.add(customer.data.email)
                    seen_emails.add(customer.data.email)
            
            result['statistics']['customers_with_issues'] = customers_with_issues
            result['statistics']['duplicate_documents'] = len(duplicate_docs)
            result['statistics']['duplicate_emails'] = len(duplicate_emails)
            
            # Gerar recomendações
            if customers_with_issues > 0:
                result['recommendations'].append("Revisar clientes com problemas de consistência")
            
            if len(duplicate_docs) > 0:
                result['recommendations'].append("Investigar documentos duplicados")
            
            if len(duplicate_emails) > 0:
                result['recommendations'].append("Investigar emails duplicados")
            
            # Marcar como não saudável se há muitos problemas
            if (customers_with_issues > len(customers) * 0.1 or 
                len(duplicate_docs) > 0 or len(duplicate_emails) > 0):
                result['is_healthy'] = False
            
        except Exception as e:
            result['is_healthy'] = False
            result['issues'].append(f"Erro ao validar integridade: {str(e)}")
        
        return result