# core/matcher.py
"""
Classe responsável pela detecção de clientes duplicados
"""

import re
from difflib import SequenceMatcher
from typing import Dict, Tuple
from models.schemas import CustomerData
from config import FIELD_WEIGHTS, SIMILARITY_THRESHOLD, LOW_SIMILARITY_THRESHOLD

class CustomerMatcher:
    """Classe para identificar clientes duplicados"""
    
    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or FIELD_WEIGHTS
        self.similarity_threshold = SIMILARITY_THRESHOLD
        self.low_similarity_threshold = LOW_SIMILARITY_THRESHOLD
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normaliza texto para comparação"""
        if not text:
            return ""
        text = text.lower().strip()
        text = re.sub(r'\s+', ' ', text)
        return text
    
    @staticmethod
    def normalize_document(doc: str) -> str:
        """Normaliza documento removendo caracteres especiais"""
        if not doc:
            return ""
        return re.sub(r'[^\d]', '', doc)
    
    @staticmethod
    def normalize_phone(phone: str) -> str:
        """Normaliza telefone removendo caracteres especiais"""
        if not phone:
            return ""
        return re.sub(r'[^\d]', '', phone)
    
    @staticmethod
    def similarity_score(str1: str, str2: str) -> float:
        """Calcula similaridade entre duas strings"""
        if not str1 or not str2:
            return 0.0
        return SequenceMatcher(None, str1, str2).ratio()
    
    def _check_document_match(self, doc1: str, doc2: str) -> Tuple[float, Dict[str, str]]:
        """Verifica compatibilidade de documentos"""
        conflicts = {}
        
        if not doc1 or not doc2:
            return 0.0, conflicts
        
        normalized_doc1 = self.normalize_document(doc1)
        normalized_doc2 = self.normalize_document(doc2)
        
        if normalized_doc1 == normalized_doc2 and normalized_doc1:
            return self.weights['documento'], conflicts
        elif normalized_doc1 and normalized_doc2 and normalized_doc1 != normalized_doc2:
            conflicts['documento'] = f"Doc1: {normalized_doc1} vs Doc2: {normalized_doc2}"
            return 0.0, conflicts
        
        return 0.0, conflicts
    
    def _check_email_match(self, email1: str, email2: str) -> float:
        """Verifica compatibilidade de emails"""
        if not email1 or not email2:
            return 0.0
        
        if email1.lower() == email2.lower():
            return self.weights['email']
        
        return 0.0
    
    def _check_name_match(self, name1: str, name2: str) -> Tuple[float, Dict[str, str]]:
        """Verifica compatibilidade de nomes"""
        conflicts = {}
        
        if not name1 or not name2:
            return 0.0, conflicts
        
        normalized_name1 = self.normalize_text(name1)
        normalized_name2 = self.normalize_text(name2)
        
        similarity = self.similarity_score(normalized_name1, normalized_name2)
        
        if similarity > self.similarity_threshold:
            return self.weights['nome'] * similarity, conflicts
        elif similarity < self.low_similarity_threshold:
            conflicts['nome'] = f"Nome1: {name1} vs Nome2: {name2}"
        
        return 0.0, conflicts
    
    def _check_phone_match(self, phone1: str, phone2: str) -> Tuple[float, Dict[str, str]]:
        """Verifica compatibilidade de telefones"""
        conflicts = {}
        
        if not phone1 or not phone2:
            return 0.0, conflicts
        
        normalized_phone1 = self.normalize_phone(phone1)
        normalized_phone2 = self.normalize_phone(phone2)
        
        if normalized_phone1 == normalized_phone2 and normalized_phone1:
            return self.weights['telefone'], conflicts
        elif normalized_phone1 and normalized_phone2 and normalized_phone1 != normalized_phone2:
            conflicts['telefone'] = f"Tel1: {normalized_phone1} vs Tel2: {normalized_phone2}"
        
        return 0.0, conflicts
    
    def _check_birthdate_match(self, date1: str, date2: str) -> Tuple[float, Dict[str, str]]:
        """Verifica compatibilidade de datas de nascimento"""
        conflicts = {}
        
        if not date1 or not date2:
            return 0.0, conflicts
        
        if date1 == date2:
            return self.weights['data_nascimento'], conflicts
        else:
            conflicts['data_nascimento'] = f"Data1: {date1} vs Data2: {date2}"
        
        return 0.0, conflicts
    
    def _check_address_match(self, addr1: str, addr2: str) -> float:
        """Verifica compatibilidade de endereços"""
        if not addr1 or not addr2:
            return 0.0
        
        normalized_addr1 = self.normalize_text(addr1)
        normalized_addr2 = self.normalize_text(addr2)
        
        similarity = self.similarity_score(normalized_addr1, normalized_addr2)
        
        if similarity > 0.7:
            return self.weights['endereco'] * similarity
        
        return 0.0
    
    def calculate_match_score(self, customer1: CustomerData, customer2: CustomerData) -> Tuple[float, Dict[str, str]]:
        """Calcula score de compatibilidade entre dois clientes"""
        total_score = 0.0
        total_weight = 0.0
        all_conflicts = {}
        
        # Documento - critério mais importante
        doc_score, doc_conflicts = self._check_document_match(
            customer1.documento, customer2.documento
        )
        if doc_conflicts:
            return 0.0, doc_conflicts  # Conflito de documento é eliminatório
        
        total_score += doc_score
        if customer1.documento and customer2.documento:
            total_weight += self.weights['documento']
        
        # Email
        email_score = self._check_email_match(customer1.email, customer2.email)
        total_score += email_score
        if customer1.email and customer2.email:
            total_weight += self.weights['email']
        
        # Nome
        name_score, name_conflicts = self._check_name_match(customer1.nome, customer2.nome)
        total_score += name_score
        all_conflicts.update(name_conflicts)
        if customer1.nome and customer2.nome:
            total_weight += self.weights['nome']
        
        # Telefone
        phone_score, phone_conflicts = self._check_phone_match(
            customer1.telefone, customer2.telefone
        )
        total_score += phone_score
        all_conflicts.update(phone_conflicts)
        if customer1.telefone and customer2.telefone:
            total_weight += self.weights['telefone']
        
        # Data de nascimento
        birthdate_score, birthdate_conflicts = self._check_birthdate_match(
            customer1.data_nascimento, customer2.data_nascimento
        )
        total_score += birthdate_score
        all_conflicts.update(birthdate_conflicts)
        
        # Endereço
        address_score = self._check_address_match(customer1.endereco, customer2.endereco)
        total_score += address_score
        if customer1.endereco and customer2.endereco:
            total_weight += self.weights['endereco']
        
        # Calcular score final
        final_score = total_score / total_weight if total_weight > 0 else 0.0
        
        # Penalizar múltiplos conflitos
        if len(all_conflicts) > 1:
            final_score *= 0.5
        
        return final_score, all_conflicts