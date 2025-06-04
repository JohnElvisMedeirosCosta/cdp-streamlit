# ui/components.py
"""
Componentes reutilizáveis da interface Streamlit
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any, Optional
from models.schemas import Customer, SystemStatistics
from config import DATA_SOURCES
from datetime import date

def show_customer_metrics(stats: SystemStatistics):
    """Exibe métricas principais em colunas"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total de Clientes",
            value=stats.total_customers
        )
    
    with col2:
        st.metric(
            label="Clientes com Histórico",
            value=stats.customers_with_updates
        )
    
    with col3:
        st.metric(
            label="Confiança Média",
            value=f"{stats.average_confidence_score:.2f}"
        )
    
    with col4:
        st.metric(
            label="Total de Alterações",
            value=stats.total_history_entries
        )

def show_customer_card(customer: Customer, show_actions: bool = True):
    """Exibe card de informações do cliente"""
    with st.expander(f"👤 {customer.data.nome or 'Nome não informado'} - ID: {customer.id[:8]}..."):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Dados Pessoais:**")
            st.write(f"- Nome: {customer.data.nome or 'N/A'}")
            st.write(f"- Email: {customer.data.email or 'N/A'}")
            st.write(f"- Documento: {customer.data.documento or 'N/A'}")
            st.write(f"- Telefone: {customer.data.telefone or 'N/A'}")
            st.write(f"- Data Nascimento: {customer.data.data_nascimento or 'N/A'}")
            st.write(f"- Profissão: {customer.data.profissao or 'N/A'}")
        
        with col2:
            st.write("**Endereço:**")
            st.write(f"- Endereço: {customer.data.endereco or 'N/A'}")
            st.write(f"- Cidade: {customer.data.cidade or 'N/A'}")
            st.write(f"- Estado: {customer.data.estado or 'N/A'}")
            st.write(f"- CEP: {customer.data.cep or 'N/A'}")
            
            st.write("**Metadados:**")
            st.write(f"- Score de Confiança: {customer.confidence_score:.2f}")
            st.write(f"- Fontes: {', '.join(customer.sources)}")
            st.write(f"- Criado em: {customer.created_at[:10]}")
            st.write(f"- Atualizado em: {customer.updated_at[:10]}")
            st.write(f"- Histórico: {len(customer.history)} alterações")
        
        if show_actions:
            return show_customer_actions(customer)
    
    return None

def show_customer_actions(customer: Customer) -> Dict[str, bool]:
    """Exibe botões de ação para o cliente e retorna quais foram clicados"""
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    actions = {}
    
    with col_btn1:
        actions['view_history'] = st.button(
            f"📋 Ver Histórico", 
            key=f"hist_{customer.id}"
        )
    
    with col_btn2:
        actions['export_json'] = st.button(
            f"📤 Exportar JSON", 
            key=f"export_{customer.id}"
        )
    
    with col_btn3:
        actions['delete'] = st.button(
            f"🗑️ Excluir", 
            key=f"delete_{customer.id}", 
            type="secondary"
        )
    
    return actions

def show_customer_form(key_suffix: str = "") -> Dict[str, Any]:
    """Exibe formulário de cadastro de cliente"""
    with st.form(f"customer_form_{key_suffix}"):
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Nome Completo", key=f"nome_{key_suffix}")
            email = st.text_input("Email", key=f"email_{key_suffix}")
            documento = st.text_input("CPF/CNPJ", key=f"documento_{key_suffix}")
            telefone = st.text_input("Telefone", key=f"telefone_{key_suffix}")
            data_nascimento = st.date_input("Data de Nascimento", value=None, key=f"data_nasc_{key_suffix}", min_value=date(1900, 1, 1), max_value=date.today())
        
        with col2:
            endereco = st.text_input("Endereço", key=f"endereco_{key_suffix}")
            cidade = st.text_input("Cidade", key=f"cidade_{key_suffix}")
            estado = st.text_input("Estado", key=f"estado_{key_suffix}")
            cep = st.text_input("CEP", key=f"cep_{key_suffix}")
            profissao = st.text_input("Profissão", key=f"profissao_{key_suffix}")
        
        source = st.selectbox(
            "Fonte dos Dados", 
            DATA_SOURCES,
            key=f"source_{key_suffix}"
        )
        
        force_merge = st.checkbox(
            "Forçar merge em caso de conflitos", 
            help="Use apenas se tiver certeza de que são a mesma pessoa",
            key=f"force_merge_{key_suffix}"
        )
        
        submitted = st.form_submit_button("Adicionar Cliente")
        
        if submitted:
            return {
                'nome': nome if nome else None,
                'email': email if email else None,
                'documento': documento if documento else None,
                'telefone': telefone if telefone else None,
                'endereco': endereco if endereco else None,
                'cidade': cidade if cidade else None,
                'estado': estado if estado else None,
                'cep': cep if cep else None,
                'data_nascimento': str(data_nascimento) if data_nascimento else None,
                'profissao': profissao if profissao else None,
                'source': source,
                'force_merge': force_merge,
                'submitted': True
            }
        
        return {'submitted': False}

def show_search_filters() -> Dict[str, str]:
    """Exibe filtros de busca"""
    col1, col2, col3 = st.columns(3)
    
    filters = {}
    
    with col1:
        filters['nome'] = st.text_input("Buscar por Nome")
        filters['email'] = st.text_input("Buscar por Email")
    
    with col2:
        filters['documento'] = st.text_input("Buscar por Documento")
        filters['telefone'] = st.text_input("Buscar por Telefone")
    
    with col3:
        filters['cidade'] = st.text_input("Buscar por Cidade")
        filters['profissao'] = st.text_input("Buscar por Profissão")
    
    # Remover filtros vazios
    return {k: v for k, v in filters.items() if v and v.strip()}

def show_confidence_chart(customers: List[Customer]) -> None:
    """Exibe gráfico de distribuição de confiança"""
    if not customers:
        st.info("Nenhum cliente para análise")
        return
    
    confidence_scores = [c.confidence_score for c in customers]
    
    fig = px.histogram(
        x=confidence_scores,
        nbins=10,
        title="Distribuição de Scores de Confiança",
        labels={'x': 'Score de Confiança', 'y': 'Quantidade de Clientes'}
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_sources_chart(customers: List[Customer]) -> None:
    """Exibe gráfico de clientes por fonte"""
    if not customers:
        st.info("Nenhum cliente para análise")
        return
    
    all_sources = []
    for customer in customers:
        all_sources.extend(customer.sources)
    
    if not all_sources:
        st.info("Nenhuma fonte de dados registrada")
        return
    
    sources_df = pd.DataFrame({'fonte': all_sources})
    source_counts = sources_df['fonte'].value_counts()
    
    fig = px.pie(
        values=source_counts.values,
        names=source_counts.index,
        title="Clientes por Fonte de Dados"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_completeness_chart(customers: List[Customer]) -> None:
    """Exibe gráfico de completude dos dados"""
    if not customers:
        st.info("Nenhum cliente para análise")
        return
    
    fields = ['nome', 'email', 'documento', 'telefone', 'endereco', 
             'cidade', 'estado', 'cep', 'data_nascimento', 'profissao']
    
    completeness = {}
    for field in fields:
        count = sum(1 for c in customers if getattr(c.data, field) is not None)
        completeness[field] = (count / len(customers)) * 100
    
    fig = px.bar(
        x=list(completeness.keys()),
        y=list(completeness.values()),
        title="Completude dos Dados (%)",
        labels={'x': 'Campo', 'y': 'Percentual Preenchido'}
    )
    fig.update_xaxes(tickangle=45)
    
    st.plotly_chart(fig, use_container_width=True)

def show_monthly_creation_chart(customers: List[Customer]) -> None:
    """Exibe gráfico de criações por mês"""
    if not customers:
        st.info("Nenhum cliente para análise")
        return
    
    from datetime import datetime
    
    creation_dates = [datetime.fromisoformat(c.created_at).date() for c in customers]
    df_dates = pd.DataFrame({'data': creation_dates})
    df_dates['mes_ano'] = df_dates['data'].apply(lambda x: f"{x.year}-{x.month:02d}")
    monthly_counts = df_dates['mes_ano'].value_counts().sort_index()
    
    fig = px.line(
        x=monthly_counts.index,
        y=monthly_counts.values,
        title="Clientes Criados por Mês",
        labels={'x': 'Mês/Ano', 'y': 'Novos Clientes'}
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_history_table(customer: Customer) -> None:
    """Exibe tabela de histórico do cliente"""
    if not customer.history:
        st.info("Este cliente não possui histórico de alterações")
        return
    
    history_data = []
    for entry in customer.history:
        history_data.append({
            'Data/Hora': entry.timestamp[:19].replace('T', ' '),
            'Campo': entry.field,
            'Valor Anterior': entry.old_value or 'N/A',
            'Novo Valor': entry.new_value or 'N/A',
            'Fonte': entry.source,
            'Confiança': f"{entry.confidence:.2f}"
        })
    
    df_history = pd.DataFrame(history_data)
    st.dataframe(df_history, use_container_width=True)

def show_result_message(result: Dict[str, Any]) -> None:
    """Exibe mensagem de resultado de operação"""
    if result['status'] == 'created':
        st.success(f"✅ {result['message']}")
        st.balloons()
    elif result['status'] == 'updated':
        st.success(f"🔄 {result['message']}")
        if result.get('changes_made', 0) > 0:
            st.info(f"Foram feitas {result['changes_made']} alterações no cliente")
    elif result['status'] == 'conflict_detected':
        st.error("⚠️ Conflitos detectados!")
        st.write("**Conflitos encontrados:**")
        for campo, detalhe in result['conflicts'].items():
            st.write(f"- **{campo}**: {detalhe}")
        
        st.write("**Ações sugeridas:**")
        for acao in result['suggested_actions']:
            st.write(f"- {acao}")
        
        if 'match_details' in result:
            st.write(f"**Score de similaridade**: {result['match_details']['score']:.2f}")
    else:
        st.error(f"❌ Erro: {result['message']}")

def show_import_progress(current: int, total: int, message: str = "") -> None:
    """Exibe barra de progresso para importação"""
    progress = current / total if total > 0 else 0
    st.progress(progress)
    if message:
        st.text(message)

def show_data_quality_metrics(customers: List[Customer]) -> None:
    """Exibe métricas de qualidade dos dados"""
    if not customers:
        st.info("Nenhum cliente para análise")
        return
    
    quality_metrics = {
        'Clientes com email': sum(1 for c in customers if c.data.email),
        'Clientes com documento': sum(1 for c in customers if c.data.documento),
        'Clientes com telefone': sum(1 for c in customers if c.data.telefone),
        'Clientes com endereço completo': sum(1 for c in customers 
                                           if c.data.endereco and c.data.cidade and c.data.estado),
        'Clientes com alta confiança (>0.8)': sum(1 for c in customers if c.confidence_score > 0.8),
        'Clientes com múltiplas fontes': sum(1 for c in customers if len(c.sources) > 1)
    }
    
    quality_df = pd.DataFrame(list(quality_metrics.items()), columns=['Métrica', 'Quantidade'])
    quality_df['Percentual'] = (quality_df['Quantidade'] / len(customers) * 100).round(1)
    
    st.dataframe(quality_df, use_container_width=True)

def show_geographic_distribution(customers: List[Customer]) -> None:
    """Exibe distribuição geográfica dos clientes"""
    if not customers:
        st.info("Nenhum cliente para análise")
        return
    
    geo_data = []
    for customer in customers:
        cidade = customer.data.cidade or 'Não informado'
        estado = customer.data.estado or 'Não informado'
        geo_data.append({'Cidade': cidade, 'Estado': estado})
    
    geo_df = pd.DataFrame(geo_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        city_counts = geo_df['Cidade'].value_counts().head(10)
        st.write("**Top 10 Cidades:**")
        st.dataframe(city_counts.to_frame('Clientes'))
    
    with col2:
        state_counts = geo_df['Estado'].value_counts()
        st.write("**Por Estado:**")
        st.dataframe(state_counts.to_frame('Clientes'))

def show_sidebar_info():
    """Exibe informações na sidebar"""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📖 Como usar:")
    st.sidebar.markdown("""
    1. **Dashboard**: Visão geral do sistema
    2. **Adicionar Cliente**: Cadastrar novos clientes
    3. **Importar CSV**: Importação em lote via arquivo
    4. **Buscar Clientes**: Encontrar e gerenciar clientes
    5. **Audiências**: Criar e gerenciar segmentações
    6. **Histórico**: Ver alterações dos clientes
    7. **Estatísticas**: Análises detalhadas dos dados
    """)
    
    st.sidebar.markdown("### ⚙️ Configurações:")
    if st.sidebar.button("🗑️ Limpar Cache"):
        st.cache_data.clear()
        st.success("Cache limpo!")

def show_technical_info(cdp):
    """Exibe informações técnicas na sidebar"""
    with st.sidebar.expander("ℹ️ Informações Técnicas"):
        stats = cdp.get_statistics()
        st.write(f"**Total de clientes**: {stats.total_customers}")
        st.write(f"**Banco de dados**: SQLite")
        st.write(f"**Threshold de match**: {cdp.match_threshold}")
        
        if st.button("📊 Recarregar Estatísticas"):
            st.rerun()