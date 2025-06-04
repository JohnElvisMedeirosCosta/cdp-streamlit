# models/database.py
"""
Modelos do banco de dados SQLAlchemy
"""

import uuid
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from config import DATABASE_URL

Base = declarative_base()

class CustomerModel(Base):
    """Modelo do cliente no banco de dados"""
    __tablename__ = 'customers'
    
    id = Column(String, primary_key=True)
    email = Column(String, index=True)
    documento = Column(String, index=True)
    nome = Column(String, index=True)
    telefone = Column(String, index=True)
    endereco = Column(String)
    cidade = Column(String)
    estado = Column(String)
    cep = Column(String)
    data_nascimento = Column(String)
    profissao = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    sources = Column(Text)  # JSON string
    confidence_score = Column(Float)
    
    # Relacionamento com histórico
    history = relationship("HistoryModel", back_populates="customer", cascade="all, delete-orphan")

class HistoryModel(Base):
    """Modelo do histórico de alterações"""
    __tablename__ = 'customer_history'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String, ForeignKey('customers.id'))
    timestamp = Column(DateTime)
    field = Column(String)
    old_value = Column(Text)
    new_value = Column(Text)
    source = Column(String)
    confidence = Column(Float)
    
    # Relacionamento reverso
    customer = relationship("CustomerModel", back_populates="history")

class DatabaseManager:
    """Gerenciador de conexão com banco de dados"""
    
    def __init__(self, database_url: str = DATABASE_URL):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        
        Session = sessionmaker(bind=self.engine)
        self.session_factory = Session
    
    def get_session(self):
        """Retorna uma nova sessão do banco"""
        return self.session_factory()
    
    def create_tables(self):
        """Cria todas as tabelas"""
        Base.metadata.create_all(self.engine)
    
    def drop_tables(self):
        """Remove todas as tabelas"""
        Base.metadata.drop_all(self.engine)