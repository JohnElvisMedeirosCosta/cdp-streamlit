# services/export_service.py
"""
Serviços para exportação de dados
"""

import json
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
from models.schemas import Customer, SystemStatistics
from core.cdp import CustomerDataPlatform

class ExportService:
    """Serviço para exportação de dados de clientes"""
    
    def __init__(self, cdp: CustomerDataPlatform):
        self.cdp = cdp
    
    def export_customers_to_csv(self, customers: List[Customer] = None) -> str:
        """Exporta clientes para formato CSV"""
        if customers is None:
            customers = self.cdp.get_all_customers()
        
        if not customers:
            return ""
        
        # Preparar dados para o DataFrame
        export_data = []
        for customer in customers:
            row = {
                'id': customer.id,
                'nome': customer.data.nome or '',
                'email': customer.data.email or '',
                'documento': customer.data.documento or '',
                'telefone': customer.data.telefone or '',
                'endereco': customer.data.endereco or '',
                'cidade': customer.data.cidade or '',
                'estado': customer.data.estado or '',
                'cep': customer.data.cep or '',
                'data_nascimento': customer.data.data_nascimento or '',
                'profissao': customer.data.profissao or '',
                'criado_em': customer.created_at[:10],  # Apenas data
                'atualizado_em': customer.updated_at[:10],
                'score_confianca': customer.confidence_score,
                'fontes': ', '.join(customer.sources),
                'numero_alteracoes': len(customer.history)
            }
            export_data.append(row)
        
        df = pd.DataFrame(export_data)
        return df.to_csv(index=False)
    
    def export_customer_to_json(self, customer_id: str) -> Optional[str]:
        """Exporta um cliente específico para JSON"""
        customer = self.cdp.get_customer(customer_id)
        if not customer:
            return None
        
        return json.dumps(customer.to_dict(), indent=2, ensure_ascii=False)
    
    def export_customers_to_json(self, customers: List[Customer] = None) -> str:
        """Exporta múltiplos clientes para JSON"""
        if customers is None:
            customers = self.cdp.get_all_customers()
        
        customers_data = [customer.to_dict() for customer in customers]
        
        export_data = {
            'export_info': {
                'timestamp': datetime.now().isoformat(),
                'total_customers': len(customers),
                'format_version': '1.0'
            },
            'customers': customers_data
        }
        
        return json.dumps(export_data, indent=2, ensure_ascii=False)
    
    def export_statistics_report(self) -> Dict[str, Any]:
        """Exporta relatório completo de estatísticas"""
        stats = self.cdp.get_statistics()
        customers = self.cdp.get_all_customers()
        
        # Análises adicionais
        source_analysis = self._analyze_sources(customers)
        completeness_analysis = self._analyze_data_completeness(customers)
        confidence_analysis = self._analyze_confidence_scores(customers)
        history_analysis = self._analyze_history_data(customers)
        
        report = {
            'report_info': {
                'generated_at': datetime.now().isoformat(),
                'report_type': 'statistics_full'
            },
            'basic_statistics': {
                'total_customers': stats.total_customers,
                'customers_with_updates': stats.customers_with_updates,
                'average_confidence_score': stats.average_confidence_score,
                'total_history_entries': stats.total_history_entries
            },
            'source_analysis': source_analysis,
            'data_completeness': completeness_analysis,
            'confidence_analysis': confidence_analysis,
            'history_analysis': history_analysis
        }
        
        return report
    
    def _analyze_sources(self, customers: List[Customer]) -> Dict[str, Any]:
        """Analisa distribuição de fontes de dados"""
        source_counts = {}
        multiple_sources = 0
        
        for customer in customers:
            if len(customer.sources) > 1:
                multiple_sources += 1
            
            for source in customer.sources:
                source_counts[source] = source_counts.get(source, 0) + 1
        
        return {
            'sources_distribution': source_counts,
            'customers_with_multiple_sources': multiple_sources,
            'unique_sources': len(source_counts)
        }
    
    def _analyze_data_completeness(self, customers: List[Customer]) -> Dict[str, Any]:
        """Analisa completude dos dados"""
        fields = ['nome', 'email', 'documento', 'telefone', 'endereco', 
                 'cidade', 'estado', 'cep', 'data_nascimento', 'profissao']
        
        completeness = {}
        total_customers = len(customers)
        
        if total_customers == 0:
            return completeness
        
        for field in fields:
            filled_count = sum(1 for customer in customers 
                             if getattr(customer.data, field) is not None)
            completeness[field] = {
                'filled': filled_count,
                'total': total_customers,
                'percentage': round((filled_count / total_customers) * 100, 2)
            }
        
        return completeness
    
    def _analyze_confidence_scores(self, customers: List[Customer]) -> Dict[str, Any]:
        """Analisa distribuição de scores de confiança"""
        if not customers:
            return {}
        
        scores = [customer.confidence_score for customer in customers]
        
        # Distribuição por faixas
        score_ranges = {
            'high (0.8-1.0)': sum(1 for score in scores if score >= 0.8),
            'medium (0.5-0.8)': sum(1 for score in scores if 0.5 <= score < 0.8),
            'low (0.0-0.5)': sum(1 for score in scores if score < 0.5)
        }
        
        return {
            'distribution': score_ranges,
            'average': round(sum(scores) / len(scores), 3),
            'min': round(min(scores), 3),
            'max': round(max(scores), 3)
        }
    
    def _analyze_history_data(self, customers: List[Customer]) -> Dict[str, Any]:
        """Analisa dados do histórico"""
        total_changes = 0
        customers_with_history = 0
        field_changes = {}
        source_changes = {}
        
        for customer in customers:
            if customer.history:
                customers_with_history += 1
                total_changes += len(customer.history)
                
                for entry in customer.history:
                    # Contar mudanças por campo
                    field_changes[entry.field] = field_changes.get(entry.field, 0) + 1
                    
                    # Contar mudanças por fonte
                    source_changes[entry.source] = source_changes.get(entry.source, 0) + 1
        
        return {
            'total_changes': total_changes,
            'customers_with_history': customers_with_history,
            'average_changes_per_customer': round(total_changes / len(customers), 2) if customers else 0,
            'changes_by_field': field_changes,
            'changes_by_source': source_changes
        }
    
    def export_customer_history_csv(self, customer_id: str) -> Optional[str]:
        """Exporta histórico de um cliente para CSV"""
        customer = self.cdp.get_customer(customer_id)
        if not customer or not customer.history:
            return None
        
        history_data = []
        for entry in customer.history:
            history_data.append({
                'timestamp': entry.timestamp,
                'field': entry.field,
                'old_value': entry.old_value or '',
                'new_value': entry.new_value or '',
                'source': entry.source,
                'confidence': entry.confidence
            })
        
        df = pd.DataFrame(history_data)
        return df.to_csv(index=False)
    
    def create_backup_export(self) -> Dict[str, Any]:
        """Cria export completo para backup"""
        customers = self.cdp.get_all_customers()
        stats = self.cdp.get_statistics()
        
        backup_data = {
            'backup_info': {
                'created_at': datetime.now().isoformat(),
                'total_customers': len(customers),
                'system_statistics': {
                    'total_customers': stats.total_customers,
                    'customers_with_updates': stats.customers_with_updates,
                    'average_confidence_score': stats.average_confidence_score,
                    'total_history_entries': stats.total_history_entries
                }
            },
            'customers': [customer.to_dict() for customer in customers]
        }
        
        return backup_data