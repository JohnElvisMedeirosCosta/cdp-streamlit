# ui/add_customer.py
"""
Página para adicionar novos clientes
"""

import streamlit as st
from models.schemas import CustomerData
from core.cdp import CustomerDataPlatform
from ui.components import show_customer_form, show_result_message

def show_add_customer(cdp: CustomerDataPlatform):
    """Exibe a página de adicionar cliente"""
    st.header("➕ Adicionar Novo Cliente")
    
    # Formulário de cliente
    form_data = show_customer_form("add_customer")
    
    if form_data['submitted']:
        # Criar objeto CustomerData
        customer_data = CustomerData(
            nome=form_data['nome'],
            email=form_data['email'],
            documento=form_data['documento'],
            telefone=form_data['telefone'],
            endereco=form_data['endereco'],
            cidade=form_data['cidade'],
            estado=form_data['estado'],
            cep=form_data['cep'],
            data_nascimento=form_data['data_nascimento'],
            profissao=form_data['profissao']
        )
        
        # Adicionar cliente
        result = cdp.add_customer_data(
            customer_data, 
            source=form_data['source'], 
            force_merge=form_data['force_merge']
        )
        
        # Mostrar resultado
        show_result_message(result)