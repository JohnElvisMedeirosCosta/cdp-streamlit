# ui/search_customers.py
"""
Página para buscar e gerenciar clientes
"""

import streamlit as st
import json
from models.schemas import SearchCriteria
from core.cdp import CustomerDataPlatform
from services.export_service import ExportService
from ui.components import show_search_filters, show_customer_card

def show_search_customers(cdp: CustomerDataPlatform):
    """Exibe a página de busca de clientes"""
    st.header("🔍 Buscar Clientes")
    
    # Inicializar serviço de exportação
    export_service = ExportService(cdp)
    
    # Filtros de busca
    filters = show_search_filters()
    
    if st.button("🔍 Buscar") and filters:
        # Criar critérios de busca
        criteria = SearchCriteria(**{k: v for k, v in filters.items() 
                                   if k in SearchCriteria.__dataclass_fields__})
        
        customers = cdp.search_customers(criteria)
        
        if customers:
            st.success(f"Encontrados {len(customers)} cliente(s)")
            
            # Opção de exportar resultados
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("📤 Exportar Resultados"):
                    csv_data = export_service.export_customers_to_csv(customers)
                    st.download_button(
                        label="💾 Baixar CSV",
                        data=csv_data,
                        file_name=f"busca_clientes_{len(customers)}_resultados.csv",
                        mime="text/csv"
                    )
            
            # Exibir clientes encontrados
            for customer in customers:
                actions = show_customer_card(customer)
                
                # Processar ações
                if actions['view_history']:
                    st.session_state.selected_customer_id = customer.id
                    st.rerun()
                
                if actions['export_json']:
                    customer_json = export_service.export_customer_to_json(customer.id)
                    if customer_json:
                        st.download_button(
                            label="💾 Baixar JSON",
                            data=customer_json,
                            file_name=f"cliente_{customer.id[:8]}.json",
                            mime="application/json",
                            key=f"download_{customer.id}"
                        )
                
                if actions['delete']:
                    if cdp.delete_customer(customer.id):
                        st.success("Cliente excluído com sucesso!")
                        st.rerun()
                    else:
                        st.error("Erro ao excluir cliente")
        else:
            st.warning("Nenhum cliente encontrado com os critérios especificados")
    elif not filters:
        st.info("Digite pelo menos um critério de busca")