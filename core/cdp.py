# core/cdp.py
"""
Classe principal do Customer Data Platform
"""

import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from models.database import DatabaseManager, CustomerModel, HistoryModel
from models.schemas import CustomerData, Customer, MatchResult, HistoryEntry, SystemStatistics, SearchCriteria
from core.matcher import CustomerMatcher
from config import MATCH_THRESHOLD, VALID_CUSTOMER_FIELDS

class CustomerDataPlatform:
    """Sistema principal de Customer Data Platform"""
    
    def __init__(self, database_url: str = None):
        self.db_manager = DatabaseManager(database_url) if database_url else DatabaseManager()
        self.matcher = CustomerMatcher()
        self.match_threshold = MATCH_THRESHOLD
    
    def _get_session(self) -> Session:
        """Retorna uma nova sessão do banco"""
        return self.db_manager.get_session()
    
    def _generate_id(self) -> str:
        """Gera ID único para cliente"""
        return str(uuid.uuid4())
    
    def _get_current_timestamp(self) -> datetime:
        """Retorna timestamp atual"""
        return datetime.now()
    
    def _model_to_customer_data(self, model: CustomerModel) -> CustomerData:
        """Converte modelo do banco para CustomerData"""
        return CustomerData(
            email=model.email,
            documento=model.documento,
            nome=model.nome,
            telefone=model.telefone,
            endereco=model.endereco,
            cidade=model.cidade,
            estado=model.estado,
            cep=model.cep,
            data_nascimento=model.data_nascimento,
            profissao=model.profissao
        )
    
    def _model_to_customer(self, model: CustomerModel) -> Customer:
        """Converte modelo do banco para Customer completo"""
        customer_data = self._model_to_customer_data(model)
        
        # Converte histórico
        history = []
        for h in model.history:
            history.append(HistoryEntry(
                timestamp=h.timestamp.isoformat(),
                field=h.field,
                old_value=h.old_value,
                new_value=h.new_value,
                source=h.source,
                confidence=h.confidence
            ))
        
        sources = json.loads(model.sources) if model.sources else []
        
        return Customer(
            id=model.id,
            data=customer_data,
            created_at=model.created_at.isoformat(),
            updated_at=model.updated_at.isoformat(),
            history=history,
            sources=sources,
            confidence_score=model.confidence_score
        )
    
    def _find_potential_matches_in_db(self, customer_data: CustomerData) -> List[CustomerModel]:
        """Busca no banco clientes que podem ser o mesmo baseado em campos chave"""
        session = self._get_session()
        
        try:
            candidates = []
            
            # Busca por documento
            if customer_data.documento:
                doc_normalized = self.matcher.normalize_document(customer_data.documento)
                if doc_normalized:
                    doc_matches = session.query(CustomerModel).filter(
                        CustomerModel.documento.like(f'%{doc_normalized}%')
                    ).all()
                    candidates.extend(doc_matches)
            
            # Busca por email
            if customer_data.email:
                email_matches = session.query(CustomerModel).filter(
                    CustomerModel.email == customer_data.email
                ).all()
                candidates.extend(email_matches)
            
            # Busca por nome similar
            if customer_data.nome:
                nome_normalized = self.matcher.normalize_text(customer_data.nome)
                if nome_normalized:
                    nome_parts = nome_normalized.split()
                    for part in nome_parts:
                        if len(part) > 2:
                            name_matches = session.query(CustomerModel).filter(
                                CustomerModel.nome.ilike(f'%{part}%')
                            ).all()
                            candidates.extend(name_matches)
            
            # Busca por telefone
            if customer_data.telefone:
                tel_normalized = self.matcher.normalize_phone(customer_data.telefone)
                if tel_normalized:
                    tel_matches = session.query(CustomerModel).filter(
                        CustomerModel.telefone.like(f'%{tel_normalized}%')
                    ).all()
                    candidates.extend(tel_matches)
            
            # Remove duplicatas mantendo a ordem
            unique_candidates = []
            seen_ids = set()
            for candidate in candidates:
                if candidate.id not in seen_ids:
                    unique_candidates.append(candidate)
                    seen_ids.add(candidate.id)
            
            return unique_candidates
            
        finally:
            session.close()
    
    def _find_matching_customers(self, customer_data: CustomerData) -> List[MatchResult]:
        """Encontra clientes que podem ser o mesmo com análise de conflitos"""
        potential_matches = self._find_potential_matches_in_db(customer_data)
        
        matches = []
        
        for customer_model in potential_matches:
            existing_data = self._model_to_customer_data(customer_model)
            score, conflicts = self.matcher.calculate_match_score(customer_data, existing_data)
            
            if score < self.match_threshold:
                continue
            
            is_safe_match = True
            reason = "Match seguro"
            
            if conflicts:
                is_safe_match = False
                conflict_details = ", ".join([f"{k}: {v}" for k, v in conflicts.items()])
                reason = f"Conflitos detectados: {conflict_details}"
            
            matches.append(MatchResult(
                customer_id=customer_model.id,
                score=score,
                conflicts=conflicts,
                is_safe_match=is_safe_match,
                reason=reason
            ))
        
        matches.sort(key=lambda x: x.score, reverse=True)
        return matches
    
    def _merge_customer_data(self, existing: CustomerData, new_data: CustomerData, 
                           source: str) -> tuple[CustomerData, List[HistoryEntry]]:
        """Merge dados do cliente mantendo os mais recentes"""
        merged = CustomerData()
        history = []
        current_time = self._get_current_timestamp()
        
        for field in VALID_CUSTOMER_FIELDS:
            existing_value = getattr(existing, field)
            new_value = getattr(new_data, field)
            
            if new_value is not None and str(new_value).strip():
                if existing_value != new_value:
                    history.append(HistoryEntry(
                        timestamp=current_time.isoformat(),
                        field=field,
                        old_value=existing_value,
                        new_value=new_value,
                        source=source,
                        confidence=1.0
                    ))
                    setattr(merged, field, new_value)
                else:
                    setattr(merged, field, new_value)
            else:
                setattr(merged, field, existing_value)
        
        return merged, history
    
    def add_customer_data(self, customer_data: CustomerData, source: str = "unknown", 
                         force_merge: bool = False) -> Dict[str, Any]:
        """Adiciona ou atualiza dados do cliente com detecção de conflitos"""
        session = self._get_session()
        
        try:
            current_time = self._get_current_timestamp()
            
            # Procura por clientes existentes que possam ser o mesmo
            matches = self._find_matching_customers(customer_data)
            
            if matches:
                best_match = matches[0]
                
                # Se há conflitos e não foi forçado o merge
                if not best_match.is_safe_match and not force_merge:
                    return {
                        'status': 'conflict_detected',
                        'customer_id': None,
                        'action': 'no_action',
                        'message': f"Conflitos detectados com cliente {best_match.customer_id}",
                        'conflicts': best_match.conflicts,
                        'suggested_actions': [
                            f"Revisar manualmente o cliente {best_match.customer_id}",
                            "Usar force_merge=True se tiver certeza",
                            "Criar cliente separado se forem pessoas diferentes"
                        ],
                        'match_details': {
                            'score': best_match.score,
                            'reason': best_match.reason
                        }
                    }
                
                # Merge seguro ou forçado
                existing_model = session.query(CustomerModel).filter(
                    CustomerModel.id == best_match.customer_id
                ).first()
                
                if not existing_model:
                    return {
                        'status': 'error',
                        'message': f"Cliente {best_match.customer_id} não encontrado no banco"
                    }
                
                existing_data = self._model_to_customer_data(existing_model)
                merged_data, new_history = self._merge_customer_data(
                    existing_data, customer_data, source
                )
                
                # Atualiza dados no banco
                for field in VALID_CUSTOMER_FIELDS:
                    setattr(existing_model, field, getattr(merged_data, field))
                
                existing_model.updated_at = current_time
                existing_model.confidence_score = max(existing_model.confidence_score, best_match.score)
                
                # Atualiza sources
                existing_sources = json.loads(existing_model.sources) if existing_model.sources else []
                if source not in existing_sources:
                    existing_sources.append(source)
                existing_model.sources = json.dumps(existing_sources)
                
                # Adiciona entradas de histórico
                for hist_entry in new_history:
                    history_model = HistoryModel(
                        customer_id=best_match.customer_id,
                        timestamp=datetime.fromisoformat(hist_entry.timestamp),
                        field=hist_entry.field,
                        old_value=str(hist_entry.old_value) if hist_entry.old_value else None,
                        new_value=str(hist_entry.new_value) if hist_entry.new_value else None,
                        source=hist_entry.source,
                        confidence=hist_entry.confidence
                    )
                    session.add(history_model)
                
                session.commit()
                
                action_type = "forced_merge" if force_merge and not best_match.is_safe_match else "safe_merge"
                
                return {
                    'status': 'updated',
                    'customer_id': best_match.customer_id,
                    'action': action_type,
                    'message': f"Cliente {best_match.customer_id} atualizado",
                    'confidence_score': best_match.score,
                    'conflicts': best_match.conflicts if not best_match.is_safe_match else {},
                    'changes_made': len(new_history)
                }
            
            else:
                # Cria novo cliente
                customer_id = self._generate_id()
                
                new_customer = CustomerModel(
                    id=customer_id,
                    email=customer_data.email,
                    documento=customer_data.documento,
                    nome=customer_data.nome,
                    telefone=customer_data.telefone,
                    endereco=customer_data.endereco,
                    cidade=customer_data.cidade,
                    estado=customer_data.estado,
                    cep=customer_data.cep,
                    data_nascimento=customer_data.data_nascimento,
                    profissao=customer_data.profissao,
                    created_at=current_time,
                    updated_at=current_time,
                    sources=json.dumps([source]),
                    confidence_score=1.0
                )
                
                session.add(new_customer)
                session.commit()
                
                return {
                    'status': 'created',
                    'customer_id': customer_id,
                    'action': 'new_customer',
                    'message': f"Novo cliente {customer_id} criado",
                    'confidence_score': 1.0,
                    'conflicts': {},
                    'changes_made': 0
                }
                
        except Exception as e:
            session.rollback()
            return {
                'status': 'error',
                'message': f"Erro ao processar cliente: {str(e)}"
            }
        finally:
            session.close()
    
    def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Retorna cliente por ID"""
        session = self._get_session()
        
        try:
            model = session.query(CustomerModel).filter(
                CustomerModel.id == customer_id
            ).first()
            
            return self._model_to_customer(model) if model else None
            
        finally:
            session.close()
    
    def search_customers(self, criteria: SearchCriteria = None, **kwargs) -> List[Customer]:
        """Busca clientes por critérios"""
        session = self._get_session()
        
        try:
            query = session.query(CustomerModel)
            
            # Usar SearchCriteria se fornecido, senão usar kwargs
            search_dict = criteria.to_dict() if criteria else kwargs
            
            for field, value in search_dict.items():
                if hasattr(CustomerModel, field) and value:
                    column = getattr(CustomerModel, field)
                    query = query.filter(column.ilike(f'%{value}%'))
            
            models = query.all()
            return [self._model_to_customer(model) for model in models]
            
        finally:
            session.close()
    
    def get_all_customers(self, limit: int = None) -> List[Customer]:
        """Retorna todos os clientes"""
        session = self._get_session()
        
        try:
            query = session.query(CustomerModel)
            if limit:
                query = query.limit(limit)
            
            models = query.all()
            return [self._model_to_customer(model) for model in models]
            
        finally:
            session.close()
    
    def get_customer_history(self, customer_id: str) -> List[HistoryEntry]:
        """Retorna histórico de alterações do cliente"""
        customer = self.get_customer(customer_id)
        return customer.history if customer else []
    
    def export_customer_data(self, customer_id: str) -> Optional[Dict]:
        """Exporta dados do cliente em formato JSON"""
        customer = self.get_customer(customer_id)
        return customer.to_dict() if customer else None
    
    def get_statistics(self) -> SystemStatistics:
        """Retorna estatísticas do sistema"""
        session = self._get_session()
        
        try:
            total_customers = session.query(CustomerModel).count()
            customers_with_history = session.query(CustomerModel).join(HistoryModel).distinct().count()
            
            avg_confidence = session.query(CustomerModel.confidence_score).all()
            avg_confidence = sum(score[0] for score in avg_confidence) / len(avg_confidence) if avg_confidence else 0
            
            total_history = session.query(HistoryModel).count()
            
            return SystemStatistics(
                total_customers=total_customers,
                customers_with_updates=customers_with_history,
                average_confidence_score=round(avg_confidence, 2),
                total_history_entries=total_history
            )
            
        finally:
            session.close()
    
    def delete_customer(self, customer_id: str) -> bool:
        """Deleta cliente por ID"""
        session = self._get_session()
        
        try:
            customer = session.query(CustomerModel).filter(
                CustomerModel.id == customer_id
            ).first()
            
            if customer:
                session.delete(customer)
                session.commit()
                return True
            return False
            
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()
    
    def update_match_threshold(self, new_threshold: float):
        """Atualiza o threshold de matching"""
        if 0.0 <= new_threshold <= 1.0:
            self.match_threshold = new_threshold
        else:
            raise ValueError("Threshold deve estar entre 0.0 e 1.0")