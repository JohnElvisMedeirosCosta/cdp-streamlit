# main.py
"""
Arquivo principal da aplicação Streamlit CDP
"""

import streamlit as st
from config import PAGE_TITLE, PAGE_ICON, LAYOUT
from core.cdp import CustomerDataPlatform
from ui.components import show_sidebar_info, show_technical_info

# Importar páginas
from ui.dashboard import show_dashboard
from ui.add_customer import show_add_customer
from ui.import_csv import show_import_csv
from ui.search_customers import show_search_customers
from ui.history import show_history
from ui.statistics import show_statistics
from ui.audience import show_audience_management

# Configuração da página
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state="expanded"
)

# Inicialização da sessão
@st.cache_resource
def init_cdp():
    """Inicializa o CDP (cached para performance)"""
    return CustomerDataPlatform()

def main():
    """Função principal da aplicação"""
    st.title(f"{PAGE_ICON} {PAGE_TITLE}")
    st.markdown("Sistema completo de gestão unificada de dados de clientes")
    
    # Inicializar CDP
    if 'cdp' not in st.session_state:
        st.session_state.cdp = init_cdp()
    
    # Sidebar com navegação
    st.sidebar.title("📋 Menu")
    page = st.sidebar.selectbox(
        "Escolha uma página:",
        ["Dashboard", "Adicionar Cliente", "Importar CSV", "Buscar Clientes", "Audiências", "Histórico", "Estatísticas"]
    )
    
    # Roteamento de páginas
    if page == "Dashboard":
        show_dashboard(st.session_state.cdp)
    elif page == "Adicionar Cliente":
        show_add_customer(st.session_state.cdp)
    elif page == "Importar CSV":
        show_import_csv(st.session_state.cdp)
    elif page == "Buscar Clientes":
        show_search_customers(st.session_state.cdp)
    elif page == "Audiências":
        show_audience_management(st.session_state.cdp)
    elif page == "Histórico":
        show_history(st.session_state.cdp)
    elif page == "Estatísticas":
        show_statistics(st.session_state.cdp)
    
    # Sidebar com informações
    show_sidebar_info()
    show_technical_info(st.session_state.cdp)

if __name__ == "__main__":
    main()