# ui/dashboard.py
"""
Página do dashboard principal
"""

import streamlit as st
import pandas as pd
from core.cdp import CustomerDataPlatform
from ui.components import show_customer_metrics, show_confidence_chart

def show_dashboard(cdp: CustomerDataPlatform):
    """Exibe a página do dashboard"""
    st.header("📊 Dashboard")
    
    # Estatísticas principais
    stats = cdp.get_statistics()
    show_customer_metrics(stats)
    
    # Lista de clientes recentes
    st.subheader("👥 Clientes Cadastrados")
    
    customers = cdp.get_all_customers()
    
    if customers:
        # Converter para DataFrame para exibição
        customer_data = []
        for customer in customers:
            customer_data.append({
                'ID': customer.id[:8] + '...',
                'Nome': customer.data.nome or 'N/A',
                'Email': customer.data.email or 'N/A',
                'Documento': customer.data.documento or 'N/A',
                'Telefone': customer.data.telefone or 'N/A',
                'Criado em': customer.created_at[:10],  # Apenas a data
                'Confiança': f"{customer.confidence_score:.2f}",
                'Fontes': len(customer.sources)
            })
        
        df = pd.DataFrame(customer_data)
        st.dataframe(df, use_container_width=True)
        
        # Gráfico de confiança
        if len(customers) > 1:
            show_confidence_chart(customers)
    else:
        st.info("Nenhum cliente cadastrado ainda. Use o menu 'Adicionar Cliente' para começar.")