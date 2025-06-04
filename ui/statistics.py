# ui/statistics.py
"""
Página de estatísticas detalhadas
"""

import streamlit as st
import json
from datetime import datetime
from core.cdp import CustomerDataPlatform
from services.export_service import ExportService
from ui.components import (
    show_customer_metrics, show_confidence_chart, show_sources_chart,
    show_completeness_chart, show_monthly_creation_chart, 
    show_data_quality_metrics, show_geographic_distribution
)

def show_statistics(cdp: CustomerDataPlatform):
    """Exibe a página de estatísticas"""
    st.header("📈 Estatísticas Detalhadas")
    
    # Inicializar serviços
    export_service = ExportService(cdp)
    
    stats = cdp.get_statistics()
    customers = cdp.get_all_customers()
    
    if not customers:
        st.info("Nenhum cliente cadastrado para análise")
        return
    
    # Métricas principais
    show_customer_metrics(stats)
    
    # Botão para exportar relatório completo
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("📊 Gerar Relatório Completo"):
            report = export_service.export_statistics_report()
            report_json = json.dumps(report, indent=2, ensure_ascii=False)
            st.download_button(
                label="💾 Baixar Relatório JSON",
                data=report_json,
                file_name=f"relatorio_estatisticas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    # Análises em colunas
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribuição de scores de confiança
        show_confidence_chart(customers)
        
        # Clientes por fonte
        show_sources_chart(customers)
    
    with col2:
        # Completude dos dados
        show_completeness_chart(customers)
        
        # Criações por mês
        show_monthly_creation_chart(customers)
    
    # Distribuição geográfica
    st.subheader("📍 Distribuição Geográfica")
    show_geographic_distribution(customers)
    
    # Qualidade dos dados
    st.subheader("🔍 Qualidade dos Dados")
    show_data_quality_metrics(customers)