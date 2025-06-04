# services/audience_service.py
"""
Serviço para gerenciamento de audiências
"""

import uuid
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, extract

from models.database import CustomerModel, DatabaseManager
from models.audience import AudienceModel, Audience, AudienceCriteria, AudienceExtractionResult
from models.schemas import Customer
from core.cdp import CustomerDataPlatform

class AudienceService:
    """Serviço para criação e gestão de audiências"""
    
    def __init__(self, cdp: CustomerDataPlatform):
        self.cdp = cdp
        self.db_manager = cdp.db_manager
        
        # Criar tabela de audiências se não existir
        AudienceModel.__table__.create(self.db_manager.engine, checkfirst=True)
    
    def create_audience(self, name: str, description: str, criteria: AudienceCriteria, 
                       created_by: str = 'system') -> str:
        """Cria uma nova audiência"""
        session = self.db_manager.get_session()
        
        try:
            audience_id = str(uuid.uuid4())
            current_time = datetime.now()
            
            # Contar clientes que atendem aos critérios
            customer_count = self._count_customers_by_criteria(criteria)
            
            audience = AudienceModel(
                id=audience_id,
                name=name,
                description=description,
                criteria=json.dumps(criteria.to_dict()),
                is_active=True,
                created_at=current_time,
                updated_at=current_time,
                created_by=created_by,
                customer_count=customer_count
            )
            
            session.add(audience)
            session.commit()
            
            return audience_id
            
        finally:
            session.close()
    
    def update_audience(self, audience_id: str, name: Optional[str] = None, 
                       description: Optional[str] = None, 
                       criteria: Optional[AudienceCriteria] = None) -> bool:
        """Atualiza uma audiência existente"""
        session = self.db_manager.get_session()
        
        try:
            audience = session.query(AudienceModel).filter(
                AudienceModel.id == audience_id
            ).first()
            
            if not audience:
                return False
            
            if name is not None:
                audience.name = name
            if description is not None:
                audience.description = description
            if criteria is not None:
                audience.criteria = json.dumps(criteria.to_dict())
                audience.customer_count = self._count_customers_by_criteria(criteria)
            
            audience.updated_at = datetime.now()
            session.commit()
            
            return True
            
        finally:
            session.close()
    
    def get_audience(self, audience_id: str) -> Optional[Audience]:
        """Retorna uma audiência por ID"""
        session = self.db_manager.get_session()
        
        try:
            model = session.query(AudienceModel).filter(
                AudienceModel.id == audience_id
            ).first()
            
            if not model:
                return None
            
            return self._model_to_audience(model)
            
        finally:
            session.close()
    
    def get_all_audiences(self, active_only: bool = True) -> List[Audience]:
        """Retorna todas as audiências"""
        session = self.db_manager.get_session()
        
        try:
            query = session.query(AudienceModel)
            if active_only:
                query = query.filter(AudienceModel.is_active == True)
            
            models = query.order_by(AudienceModel.created_at.desc()).all()
            return [self._model_to_audience(model) for model in models]
            
        finally:
            session.close()
    
    def delete_audience(self, audience_id: str) -> bool:
        """Deleta uma audiência (soft delete)"""
        session = self.db_manager.get_session()
        
        try:
            audience = session.query(AudienceModel).filter(
                AudienceModel.id == audience_id
            ).first()
            
            if not audience:
                return False
            
            audience.is_active = False
            audience.updated_at = datetime.now()
            session.commit()
            
            return True
            
        finally:
            session.close()
    
    def extract_audience_customers(self, audience_id: str) -> Optional[AudienceExtractionResult]:
        """Extrai clientes de uma audiência e gera CSV"""
        audience = self.get_audience(audience_id)
        if not audience:
            return None
        
        # Buscar clientes que atendem aos critérios
        customers = self._get_customers_by_criteria(audience.criteria)
        
        # Gerar CSV
        csv_data = self._generate_audience_csv(customers)
        
        # Atualizar timestamp de extração
        self._update_extraction_timestamp(audience_id)
        
        return AudienceExtractionResult(
            audience_id=audience_id,
            audience_name=audience.name,
            total_customers=len(customers),
            extraction_timestamp=datetime.now().isoformat(),
            criteria_used=audience.criteria.to_dict(),
            csv_data=csv_data
        )
    
    def refresh_audience_count(self, audience_id: str) -> bool:
        """Atualiza contagem de clientes de uma audiência"""
        audience = self.get_audience(audience_id)
        if not audience:
            return False
        
        new_count = self._count_customers_by_criteria(audience.criteria)
        
        session = self.db_manager.get_session()
        try:
            audience_model = session.query(AudienceModel).filter(
                AudienceModel.id == audience_id
            ).first()
            
            if audience_model:
                audience_model.customer_count = new_count
                audience_model.updated_at = datetime.now()
                session.commit()
                return True
            
            return False
            
        finally:
            session.close()
    
    def get_audience_preview(self, criteria: AudienceCriteria, limit: int = 10) -> List[Customer]:
        """Retorna preview de clientes para critérios específicos"""
        return self._get_customers_by_criteria(criteria, limit=limit)
    
    def _model_to_audience(self, model: AudienceModel) -> Audience:
        """Converte modelo do banco para Audience"""
        criteria_dict = json.loads(model.criteria) if model.criteria else {}
        criteria = AudienceCriteria(**criteria_dict)
        
        return Audience(
            id=model.id,
            name=model.name,
            description=model.description or '',
            criteria=criteria,
            is_active=model.is_active,
            created_at=model.created_at.isoformat(),
            updated_at=model.updated_at.isoformat(),
            created_by=model.created_by,
            customer_count=model.customer_count,
            last_extracted_at=model.last_extracted_at.isoformat() if model.last_extracted_at else None
        )
    
    def _count_customers_by_criteria(self, criteria: AudienceCriteria) -> int:
        """Conta clientes que atendem aos critérios"""
        session = self.db_manager.get_session()
        
        try:
            query = self._build_criteria_query(session, criteria)
            return query.count()
            
        finally:
            session.close()
    
    def _get_customers_by_criteria(self, criteria: AudienceCriteria, limit: Optional[int] = None) -> List[Customer]:
        """Busca clientes que atendem aos critérios"""
        session = self.db_manager.get_session()
        
        try:
            query = self._build_criteria_query(session, criteria)
            
            if limit:
                query = query.limit(limit)
            
            models = query.all()
            return [self.cdp._model_to_customer(model) for model in models]
            
        finally:
            session.close()
    
    def _build_criteria_query(self, session: Session, criteria: AudienceCriteria):
        """Constrói query SQL baseada nos critérios"""
        query = session.query(CustomerModel)
        
        # Critérios de texto
        if criteria.nome_contains:
            query = query.filter(CustomerModel.nome.ilike(f'%{criteria.nome_contains}%'))
        
        if criteria.email_contains:
            query = query.filter(CustomerModel.email.ilike(f'%{criteria.email_contains}%'))
        
        if criteria.documento_equals:
            query = query.filter(CustomerModel.documento == criteria.documento_equals)
        
        if criteria.telefone_contains:
            query = query.filter(CustomerModel.telefone.ilike(f'%{criteria.telefone_contains}%'))
        
        # Critérios geográficos
        if criteria.cidade_equals:
            query = query.filter(CustomerModel.cidade.ilike(f'%{criteria.cidade_equals}%'))
        
        if criteria.estado_equals:
            query = query.filter(CustomerModel.estado.ilike(f'%{criteria.estado_equals}%'))
        
        if criteria.cep_starts_with:
            query = query.filter(CustomerModel.cep.like(f'{criteria.cep_starts_with}%'))
        
        # Critérios profissionais
        if criteria.profissao_contains:
            query = query.filter(CustomerModel.profissao.ilike(f'%{criteria.profissao_contains}%'))
        
        # Critérios de data de nascimento
        if criteria.data_nascimento_from:
            query = query.filter(CustomerModel.data_nascimento >= criteria.data_nascimento_from)
        
        if criteria.data_nascimento_to:
            query = query.filter(CustomerModel.data_nascimento <= criteria.data_nascimento_to)
        
        # Critério de aniversariantes por mês
        if criteria.aniversariantes_mes is not None:
            # Filtrar clientes que fazem aniversário no mês especificado
            # Extrair o mês da data de nascimento (formato YYYY-MM-DD)
            query = query.filter(
                and_(
                    CustomerModel.data_nascimento.isnot(None),
                    CustomerModel.data_nascimento != '',
                    extract('month', CustomerModel.data_nascimento) == criteria.aniversariantes_mes
                )
            )
        
        # Critérios de data de criação
        if criteria.created_from:
            query = query.filter(CustomerModel.created_at >= datetime.fromisoformat(criteria.created_from))
        
        if criteria.created_to:
            query = query.filter(CustomerModel.created_at <= datetime.fromisoformat(criteria.created_to))
        
        # Critérios de score de confiança
        if criteria.confidence_score_min is not None:
            query = query.filter(CustomerModel.confidence_score >= criteria.confidence_score_min)
        
        if criteria.confidence_score_max is not None:
            query = query.filter(CustomerModel.confidence_score <= criteria.confidence_score_max)
        
        # Critérios de presença de dados
        if criteria.has_email is not None:
            if criteria.has_email:
                query = query.filter(CustomerModel.email.isnot(None), CustomerModel.email != '')
            else:
                query = query.filter(or_(CustomerModel.email.is_(None), CustomerModel.email == ''))
        
        if criteria.has_telefone is not None:
            if criteria.has_telefone:
                query = query.filter(CustomerModel.telefone.isnot(None), CustomerModel.telefone != '')
            else:
                query = query.filter(or_(CustomerModel.telefone.is_(None), CustomerModel.telefone == ''))
        
        if criteria.has_endereco is not None:
            if criteria.has_endereco:
                query = query.filter(CustomerModel.endereco.isnot(None), CustomerModel.endereco != '')
            else:
                query = query.filter(or_(CustomerModel.endereco.is_(None), CustomerModel.endereco == ''))
        
        # Critérios de fonte (implementação melhorada com validação)
        if criteria.sources_include and isinstance(criteria.sources_include, list):
            for source in criteria.sources_include:
                query = query.filter(CustomerModel.sources.like(f'%{source}%'))
        
        if criteria.sources_exclude and isinstance(criteria.sources_exclude, list):
            for source in criteria.sources_exclude:
                query = query.filter(~CustomerModel.sources.like(f'%{source}%'))
        
        # Critério de atualização recente
        if criteria.updated_in_last_days:
            cutoff_date = datetime.now() - timedelta(days=criteria.updated_in_last_days)
            query = query.filter(CustomerModel.updated_at >= cutoff_date)
        
        return query
    
    def _generate_audience_csv(self, customers: List[Customer]) -> str:
        """Gera CSV dos clientes da audiência"""
        if not customers:
            return ""
        
        # Preparar dados para CSV
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
                'criado_em': customer.created_at[:10],
                'atualizado_em': customer.updated_at[:10],
                'score_confianca': customer.confidence_score,
                'fontes': ', '.join(customer.sources),
                'numero_alteracoes': len(customer.history)
            }
            export_data.append(row)
        
        df = pd.DataFrame(export_data)
        return df.to_csv(index=False)
    
    def _update_extraction_timestamp(self, audience_id: str):
        """Atualiza timestamp da última extração"""
        session = self.db_manager.get_session()
        
        try:
            audience = session.query(AudienceModel).filter(
                AudienceModel.id == audience_id
            ).first()
            
            if audience:
                audience.last_extracted_at = datetime.now()
                session.commit()
                
        finally:
            session.close()
    
    def analyze_audience_overlap(self, audience1_id: str, audience2_id: str) -> Dict[str, Any]:
        """
        Analisa sobreposição entre duas audiências
        
        Returns:
            Dict com análise detalhada da sobreposição
        """
        audience1 = self.get_audience(audience1_id)
        audience2 = self.get_audience(audience2_id)
        
        if not audience1 or not audience2:
            return {
                'error': 'Uma ou ambas audiências não foram encontradas'
            }
        
        # Obter clientes de cada audiência
        customers1 = self._get_customers_by_criteria(audience1.criteria)
        customers2 = self._get_customers_by_criteria(audience2.criteria)
        
        # Criar sets de IDs para análise
        ids1 = set(c.id for c in customers1)
        ids2 = set(c.id for c in customers2)
        
        # Calcular sobreposições e exclusividades
        overlap_ids = ids1.intersection(ids2)
        exclusive1_ids = ids1 - ids2
        exclusive2_ids = ids2 - ids1
        union_ids = ids1.union(ids2)
        
        # Obter objetos de clientes para cada categoria
        overlap_customers = [c for c in customers1 if c.id in overlap_ids]
        exclusive1_customers = [c for c in customers1 if c.id in exclusive1_ids]
        exclusive2_customers = [c for c in customers2 if c.id in exclusive2_ids]
        
        # Calcular métricas
        overlap_rate = len(overlap_ids) / len(union_ids) * 100 if union_ids else 0
        jaccard_index = len(overlap_ids) / len(union_ids) if union_ids else 0
        
        return {
            'audience1': {
                'id': audience1_id,
                'name': audience1.name,
                'total_customers': len(ids1),
                'exclusive_customers': len(exclusive1_ids)
            },
            'audience2': {
                'id': audience2_id,
                'name': audience2.name,
                'total_customers': len(ids2),
                'exclusive_customers': len(exclusive2_ids)
            },
            'overlap': {
                'customer_count': len(overlap_ids),
                'customer_ids': list(overlap_ids),
                'customers': overlap_customers
            },
            'exclusive1': {
                'customer_count': len(exclusive1_ids),
                'customer_ids': list(exclusive1_ids),
                'customers': exclusive1_customers
            },
            'exclusive2': {
                'customer_count': len(exclusive2_ids),
                'customer_ids': list(exclusive2_ids),
                'customers': exclusive2_customers
            },
            'metrics': {
                'overlap_rate_percent': round(overlap_rate, 2),
                'jaccard_index': round(jaccard_index, 3),
                'total_unique_customers': len(union_ids)
            }
        }
    
    def export_overlap_analysis(self, audience1_id: str, audience2_id: str) -> Dict[str, str]:
        """
        Exporta análise de sobreposição em múltiplos CSVs
        
        Returns:
            Dict com CSVs gerados para cada categoria
        """
        analysis = self.analyze_audience_overlap(audience1_id, audience2_id)
        
        if 'error' in analysis:
            return {'error': analysis['error']}
        
        exports = {}
        
        # CSV da sobreposição
        if analysis['overlap']['customers']:
            exports['overlap'] = self._generate_audience_csv(analysis['overlap']['customers'])
        
        # CSV exclusivos da audiência 1
        if analysis['exclusive1']['customers']:
            exports['exclusive1'] = self._generate_audience_csv(analysis['exclusive1']['customers'])
        
        # CSV exclusivos da audiência 2
        if analysis['exclusive2']['customers']:
            exports['exclusive2'] = self._generate_audience_csv(analysis['exclusive2']['customers'])
        
        # CSV com todos os clientes únicos
        all_customers = (analysis['overlap']['customers'] + 
                        analysis['exclusive1']['customers'] + 
                        analysis['exclusive2']['customers'])
        if all_customers:
            exports['all_unique'] = self._generate_audience_csv(all_customers)
        
        return exports
    
    def get_audience_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas das audiências"""
        session = self.db_manager.get_session()
        
        try:
            total_audiences = session.query(AudienceModel).filter(AudienceModel.is_active == True).count()
            
            # Audiências mais usadas (por número de extrações)
            audiences_with_extractions = session.query(AudienceModel).filter(
                AudienceModel.is_active == True,
                AudienceModel.last_extracted_at.isnot(None)
            ).count()
            
            # Audiência com mais clientes
            largest_audience = session.query(AudienceModel).filter(
                AudienceModel.is_active == True
            ).order_by(AudienceModel.customer_count.desc()).first()
            
            return {
                'total_audiences': total_audiences,
                'audiences_with_extractions': audiences_with_extractions,
                'largest_audience_size': largest_audience.customer_count if largest_audience else 0,
                'largest_audience_name': largest_audience.name if largest_audience else 'N/A'
            }
            
        finally:
            session.close()