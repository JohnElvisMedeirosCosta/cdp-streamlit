# ui/history.py
"""
Página para visualizar histórico de alterações
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from core.cdp import CustomerDataPlatform
from services.export_service import ExportService
from ui.components import show_history_table

def show_history(cdp: CustomerDataPlatform):
    """Exibe a página de histórico"""
    st.header("📚 Histórico de Alterações")
    
    # Inicializar serviço de exportação
    export_service = ExportService(cdp)
    
    # Seleção de cliente para ver histórico
    customers = cdp.get_all_customers()
    
    if not customers:
        st.info("Nenhum cliente cadastrado")
        return
    
    # Opções para seleção
    customer_options = {}
    for customer in customers:
        name = customer.data.nome or "Nome não informado"
        customer_options[f"{name} - {customer.id[:8]}..."] = customer.id
    
    selected_display = st.selectbox("Selecione um cliente:", list(customer_options.keys()))
    
    if selected_display:
        customer_id = customer_options[selected_display]
        customer = cdp.get_customer(customer_id)
        
        if customer and customer.history:
            st.subheader(f"Histórico de {customer.data.nome or 'Cliente'}")
            
            # Botão para exportar histórico
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("📤 Exportar Histórico"):
                    csv_data = export_service.export_customer_history_csv(customer_id)
                    if csv_data:
                        st.download_button(
                            label="💾 Baixar CSV",
                            data=csv_data,
                            file_name=f"historico_{customer.id[:8]}.csv",
                            mime="text/csv"
                        )
            
            # Exibir tabela de histórico
            show_history_table(customer)
            
            # Gráfico de alterações por campo
            if len(customer.history) > 1:
                field_counts = {}
                for entry in customer.history:
                    field_counts[entry.field] = field_counts.get(entry.field, 0) + 1
                
                fig = px.bar(
                    x=list(field_counts.keys()),
                    y=list(field_counts.values()),
                    title="Alterações por Campo",
                    labels={'x': 'Campo', 'y': 'Número de Alterações'}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Timeline de alterações
            if len(customer.history) > 1:
                history_dates = [pd.to_datetime(entry.timestamp).date() for entry in customer.history]
                date_counts = pd.Series(history_dates).value_counts().sort_index()
                
                fig_timeline = px.line(
                    x=date_counts.index,
                    y=date_counts.values,
                    title="Timeline de Alterações",
                    labels={'x': 'Data', 'y': 'Número de Alterações'}
                )
                st.plotly_chart(fig_timeline, use_container_width=True)
            
        elif customer:
            st.info("Este cliente não possui histórico de alterações")
        else:
            st.error("Cliente não encontrado")