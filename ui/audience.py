# ui/audience.py
"""
Interface para gerenciamento de audiências
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import time
from datetime import datetime, date, timedelta
from typing import Dict, Any

from core.cdp import CustomerDataPlatform
from services.audience_service import AudienceService
from models.audience import AudienceCriteria
from config import DATA_SOURCES
from utils.ui_helpers import (
    force_refresh_with_message, 
    handle_operation_with_refresh,
    confirm_action,
    auto_refresh_data,
    mark_for_refresh,
    batch_operation_progress
)

def show_audience_management(cdp: CustomerDataPlatform):
    """Exibe o sistema de gerenciamento de audiências"""
    st.header("🎯 Gerenciamento de Audiências")
    
    # Inicializar serviço de audiências
    if 'audience_service' not in st.session_state:
        st.session_state.audience_service = AudienceService(cdp)
    
    audience_service = st.session_state.audience_service
    
    # Sistema automático de refresh
    auto_refresh_data("audiences")
    
    # Tabs para organizar funcionalidades
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Minhas Audiências", "➕ Criar Audiência", "📊 Estatísticas", "🔧 Ferramentas"])
    
    with tab1:
        show_audience_list(audience_service)
    
    with tab2:
        show_create_audience(audience_service)
    
    with tab3:
        show_audience_statistics(audience_service)
    
    with tab4:
        show_audience_tools(audience_service)

def show_audience_list(audience_service: AudienceService):
    """Exibe lista de audiências criadas"""
    st.subheader("📋 Suas Audiências")
    
    audiences = audience_service.get_all_audiences()
    
    if not audiences:
        st.info("Nenhuma audiência criada ainda. Use a aba 'Criar Audiência' para começar.")
        return
    
    # Estatísticas rápidas
    total_customers_in_audiences = sum(aud.customer_count for aud in audiences)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total de Audiências", len(audiences))
    with col2:
        st.metric("Total de Clientes", total_customers_in_audiences)
    with col3:
        avg_size = total_customers_in_audiences / len(audiences) if audiences else 0
        st.metric("Tamanho Médio", f"{avg_size:.0f}")
    
    # Lista de audiências
    for audience in audiences:
        with st.expander(f"🎯 {audience.name} ({audience.customer_count} clientes)"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Descrição:** {audience.description}")
                st.write(f"**Criada em:** {audience.created_at[:10]}")
                st.write(f"**Última atualização:** {audience.updated_at[:10]}")
                if audience.last_extracted_at:
                    st.write(f"**Última extração:** {audience.last_extracted_at[:10]}")
                
                # Mostrar critérios resumidos
                criteria_summary = _get_criteria_summary(audience.criteria)
                if criteria_summary:
                    st.write("**Critérios:**")
                    for criterion in criteria_summary:
                        st.write(f"- {criterion}")
            
            with col2:
                # Botões de ação
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    if st.button(f"📤 Extrair", key=f"extract_{audience.id}"):
                        with st.spinner("Extraindo audiência..."):
                            result = audience_service.extract_audience_customers(audience.id)
                            if result:
                                st.success(f"✅ {result.total_customers} clientes extraídos!")
                                st.download_button(
                                    label="💾 Baixar CSV",
                                    data=result.csv_data,
                                    file_name=f"audiencia_{audience.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                    mime="text/csv",
                                    key=f"download_{audience.id}"
                                )
                            else:
                                st.error("Erro ao extrair audiência")
                
                with col_btn2:
                    if st.button(f"🔄 Atualizar", key=f"refresh_{audience.id}"):
                        if audience_service.refresh_audience_count(audience.id):
                            st.success("Contagem atualizada!")
                            st.rerun()
                        else:
                            st.error("Erro ao atualizar")
                
                # Botão de exclusão
                if st.button(f"🗑️ Excluir", key=f"delete_{audience.id}", type="secondary"):
                    if confirm_action("excluir", audience.name, f"delete_audience_{audience.id}"):
                        def delete_operation():
                            return audience_service.delete_audience(audience.id)
                        
                        if handle_operation_with_refresh(
                            operation=delete_operation,
                            success_message="Audiência excluída!",
                            error_message="Erro ao excluir audiência",
                            spinner_message="Excluindo audiência..."
                        ):
                            mark_for_refresh("audiences")

def show_create_audience(audience_service: AudienceService):
    """Exibe formulário para criar nova audiência"""
    st.subheader("➕ Criar Nova Audiência")
    
    with st.form("create_audience_form"):
        # Informações básicas
        st.write("### 📝 Informações Básicas")
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Nome da Audiência*", placeholder="Ex: Clientes Premium SP")
        with col2:
            created_by = st.text_input("Criado por", value="usuário", placeholder="Seu nome/ID")
        
        description = st.text_area("Descrição", placeholder="Descreva o objetivo desta audiência...")
        
        # Critérios de segmentação
        st.write("### 🎯 Critérios de Segmentação")
        
        # Critérios básicos
        with st.expander("👤 Dados Pessoais", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                nome_contains = st.text_input("Nome contém")
                email_contains = st.text_input("Email contém")
                documento_equals = st.text_input("Documento exato")
            with col2:
                telefone_contains = st.text_input("Telefone contém")
                profissao_contains = st.text_input("Profissão contém")
        
        # Critérios geográficos
        with st.expander("📍 Localização"):
            col1, col2, col3 = st.columns(3)
            with col1:
                cidade_equals = st.text_input("Cidade")
            with col2:
                estado_equals = st.text_input("Estado")
            with col3:
                cep_starts_with = st.text_input("CEP inicia com")
        
        # Critérios de data
        with st.expander("📅 Datas"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write("**Data de Nascimento**")
                data_nascimento_from = st.date_input("De", value=None, key="birth_from")
                data_nascimento_to = st.date_input("Até", value=None, key="birth_to")
            with col2:
                st.write("**Aniversariantes**")
                meses = {
                    0: "Todos os meses",
                    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
                    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
                    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
                }
                mes_selecionado = st.selectbox(
                    "Mês de aniversário",
                    options=list(meses.keys()),
                    format_func=lambda x: meses[x],
                    help="Selecione um mês para filtrar aniversariantes"
                )
                aniversariantes_mes = mes_selecionado if mes_selecionado > 0 else None
            with col3:
                st.write("**Data de Cadastro**")
                created_from = st.date_input("De", value=None, key="created_from")
                created_to = st.date_input("Até", value=None, key="created_to")
        
        # Critérios de qualidade
        with st.expander("⭐ Qualidade dos Dados"):
            col1, col2 = st.columns(2)
            with col1:
                confidence_min = st.slider("Score mínimo de confiança", 0.0, 1.0, 0.0, 0.1)
                confidence_max = st.slider("Score máximo de confiança", 0.0, 1.0, 1.0, 0.1)
            with col2:
                has_email = st.selectbox("Tem email?", [None, True, False], format_func=lambda x: "Qualquer" if x is None else ("Sim" if x else "Não"))
                has_telefone = st.selectbox("Tem telefone?", [None, True, False], format_func=lambda x: "Qualquer" if x is None else ("Sim" if x else "Não"))
                has_endereco = st.selectbox("Tem endereço?", [None, True, False], format_func=lambda x: "Qualquer" if x is None else ("Sim" if x else "Não"))
        
        # Critérios de fonte
        with st.expander("🔗 Fontes de Dados"):
            col1, col2 = st.columns(2)
            with col1:
                sources_include = st.multiselect("Incluir fontes", DATA_SOURCES)
            with col2:
                sources_exclude = st.multiselect("Excluir fontes", DATA_SOURCES)
        
        # Critérios avançados
        with st.expander("🔧 Critérios Avançados"):
            col1, col2 = st.columns(2)
            with col1:
                has_history = st.selectbox("Tem histórico?", [None, True, False], format_func=lambda x: "Qualquer" if x is None else ("Sim" if x else "Não"))
            with col2:
                updated_in_last_days = st.number_input("Atualizado nos últimos X dias", min_value=0, value=0, help="0 = ignorar este critério")
        
        # Botões
        col1, col2, col3 = st.columns(3)
        
        with col1:
            preview_button = st.form_submit_button("👀 Preview", type="secondary")
        with col2:
            create_button = st.form_submit_button("✅ Criar Audiência", type="primary")
        with col3:
            clear_button = st.form_submit_button("🧹 Limpar")
        
        if clear_button:
            st.rerun()
        
        if preview_button or create_button:
            # Criar objeto de critérios
            criteria = AudienceCriteria(
                nome_contains=nome_contains if nome_contains else None,
                email_contains=email_contains if email_contains else None,
                documento_equals=documento_equals if documento_equals else None,
                telefone_contains=telefone_contains if telefone_contains else None,
                cidade_equals=cidade_equals if cidade_equals else None,
                estado_equals=estado_equals if estado_equals else None,
                cep_starts_with=cep_starts_with if cep_starts_with else None,
                profissao_contains=profissao_contains if profissao_contains else None,
                data_nascimento_from=str(data_nascimento_from) if data_nascimento_from else None,
                data_nascimento_to=str(data_nascimento_to) if data_nascimento_to else None,
                aniversariantes_mes=aniversariantes_mes,
                created_from=str(created_from) if created_from else None,
                created_to=str(created_to) if created_to else None,
                confidence_score_min=confidence_min if confidence_min > 0 else None,
                confidence_score_max=confidence_max if confidence_max < 1 else None,
                has_email=has_email,
                has_telefone=has_telefone,
                has_endereco=has_endereco,
                sources_include=sources_include if sources_include else None,
                sources_exclude=sources_exclude if sources_exclude else None,
                has_history=has_history,
                updated_in_last_days=updated_in_last_days if updated_in_last_days > 0 else None
            )
            
            if criteria.is_empty():
                st.error("❌ Defina pelo menos um critério para a audiência!")
                return
            
            if preview_button:
                # Mostrar preview
                with st.spinner("Gerando preview..."):
                    preview_customers = audience_service.get_audience_preview(criteria, limit=10)
                    total_count = audience_service._count_customers_by_criteria(criteria)
                
                st.success(f"✅ {total_count} clientes encontrados")
                
                if preview_customers:
                    st.write("**Preview dos primeiros 10 clientes:**")
                    preview_data = []
                    for customer in preview_customers:
                        preview_data.append({
                            'Nome': customer.data.nome or 'N/A',
                            'Email': customer.data.email or 'N/A',
                            'Cidade': customer.data.cidade or 'N/A',
                            'Estado': customer.data.estado or 'N/A',
                            'Confiança': f"{customer.confidence_score:.2f}"
                        })
                    
                    df = pd.DataFrame(preview_data)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("Nenhum cliente encontrado com estes critérios.")
            
            elif create_button:
                if not name:
                    st.error("❌ Nome da audiência é obrigatório!")
                    return
                
                # Criar audiência
                with st.spinner("Criando audiência..."):
                    try:
                        audience_id = audience_service.create_audience(
                            name=name,
                            description=description,
                            criteria=criteria,
                            created_by=created_by
                        )
                        
                        # Criar audiência
                        def create_operation():
                            return audience_service.create_audience(
                                name=name,
                                description=description,
                                criteria=criteria,
                                created_by=created_by
                            )
                        
                        with st.spinner("Criando audiência..."):
                            try:
                                audience_id = create_operation()
                                
                                # Mostrar informações da audiência criada
                                audience = audience_service.get_audience(audience_id)
                                if audience:
                                    st.info(f"📊 {audience.customer_count} clientes incluídos na audiência")
                                
                                # Marcar para refresh e fazer rerun
                                mark_for_refresh("audiences")
                                force_refresh_with_message(f"✅ Audiência '{name}' criada com sucesso!", delay=1.0)
                                st.balloons()
                                
                            except Exception as e:
                                st.error(f"❌ Erro ao criar audiência: {str(e)}")
                    except Exception as e:
                        st.error(f"❌ Erro ao criar audiência: {str(e)}")
        # Verificar se precisa limpar o formulário após rerun
        if st.session_state.get('audience_created'):
            st.session_state.audience_created = False
            # Forçar rerun para limpar formulário
            st.rerun()

def show_audience_statistics(audience_service: AudienceService):
    """Exibe estatísticas das audiências"""
    st.subheader("📊 Estatísticas de Audiências")
    
    # Obter dados
    audiences = audience_service.get_all_audiences()
    stats = audience_service.get_audience_statistics()
    
    if not audiences:
        st.info("Nenhuma audiência criada para análise.")
        return
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Audiências", stats['total_audiences'])
    with col2:
        st.metric("Com Extrações", stats['audiences_with_extractions'])
    with col3:
        st.metric("Maior Audiência", stats['largest_audience_size'])
    with col4:
        extracted_rate = (stats['audiences_with_extractions'] / stats['total_audiences'] * 100) if stats['total_audiences'] > 0 else 0
        st.metric("Taxa de Uso", f"{extracted_rate:.1f}%")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribuição de tamanhos de audiência
        sizes = [aud.customer_count for aud in audiences]
        names = [aud.name for aud in audiences]
        
        fig = px.bar(
            x=names,
            y=sizes,
            title="Tamanho das Audiências",
            labels={'x': 'Audiência', 'y': 'Número de Clientes'}
        )
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Status de uso das audiências
        used_count = sum(1 for aud in audiences if aud.last_extracted_at)
        unused_count = len(audiences) - used_count
        
        fig = px.pie(
            values=[used_count, unused_count],
            names=['Já extraídas', 'Nunca extraídas'],
            title="Status de Uso das Audiências"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Tabela detalhada
    st.subheader("📋 Detalhes das Audiências")
    
    audience_data = []
    for aud in audiences:
        audience_data.append({
            'Nome': aud.name,
            'Clientes': aud.customer_count,
            'Criada em': aud.created_at[:10],
            'Última extração': aud.last_extracted_at[:10] if aud.last_extracted_at else 'Nunca',
            'Criado por': aud.created_by
        })
    
    df = pd.DataFrame(audience_data)
    st.dataframe(df, use_container_width=True)

def show_audience_tools(audience_service: AudienceService):
    """Exibe ferramentas para audiências"""
    st.subheader("🔧 Ferramentas de Audiência")
    
    # Ferramenta 1: Atualização em lote
    with st.expander("🔄 Atualizar Todas as Audiências"):
        st.write("Atualiza a contagem de clientes de todas as audiências ativas.")
        
        if st.button("🔄 Executar Atualização em Lote"):
            audiences = audience_service.get_all_audiences()
            
            if not audiences:
                st.info("Nenhuma audiência para atualizar.")
            else:
                def refresh_audience(audience):
                    return audience_service.refresh_audience_count(audience.id)
                
                def on_success():
                    mark_for_refresh("audiences")
                    force_refresh_with_message("Todas as audiências foram atualizadas!", delay=1.0)
                
                success_count, error_count, total = batch_operation_progress(
                    items=audiences,
                    operation=refresh_audience,
                    operation_name="Atualizando",
                    success_callback=on_success
                )
    
    # Ferramenta 2: Exportação em lote
    with st.expander("📤 Exportação em Lote"):
        st.write("Extrai e baixa dados de múltiplas audiências de uma vez.")
        
        audiences = audience_service.get_all_audiences()
        if audiences:
            selected_audiences = st.multiselect(
                "Selecione as audiências para exportar:",
                options=[aud.id for aud in audiences],
                format_func=lambda x: next(aud.name for aud in audiences if aud.id == x)
            )
            
            if selected_audiences and st.button("📤 Exportar Selecionadas"):
                results = []
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, audience_id in enumerate(selected_audiences):
                    audience = next(aud for aud in audiences if aud.id == audience_id)
                    status_text.text(f"Extraindo {audience.name}...")
                    
                    result = audience_service.extract_audience_customers(audience_id)
                    if result:
                        results.append(result)
                    
                    progress_bar.progress((i + 1) / len(selected_audiences))
                
                progress_bar.empty()
                status_text.empty()
                
                if results:
                    st.success(f"✅ {len(results)} audiências extraídas!")
                    
                    # Oferecer downloads individuais
                    for result in results:
                        st.download_button(
                            label=f"💾 Baixar {result.audience_name} ({result.total_customers} clientes)",
                            data=result.csv_data,
                            file_name=f"audiencia_{result.audience_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            key=f"bulk_download_{result.audience_id}"
                        )
        else:
            st.info("Nenhuma audiência disponível para exportação.")
    
    # Ferramenta 3: Análise de sobreposição
    with st.expander("🔍 Análise de Sobreposição"):
        st.write("Analisa quantos clientes aparecem em múltiplas audiências.")
        
        audiences = audience_service.get_all_audiences()
        if len(audiences) >= 2:
            aud1_id = st.selectbox(
                "Primeira audiência:",
                options=[aud.id for aud in audiences],
                format_func=lambda x: next(aud.name for aud in audiences if aud.id == x),
                key="overlap_aud1"
            )
            
            aud2_id = st.selectbox(
                "Segunda audiência:",
                options=[aud.id for aud in audiences if aud.id != aud1_id],
                format_func=lambda x: next(aud.name for aud in audiences if aud.id == x),
                key="overlap_aud2"
            )
            
            if st.button("🔍 Analisar Sobreposição"):
                with st.spinner("Analisando sobreposição..."):
                    aud1 = audience_service.get_audience(aud1_id)
                    aud2 = audience_service.get_audience(aud2_id)
                    
                    customers1 = audience_service._get_customers_by_criteria(aud1.criteria)
                    customers2 = audience_service._get_customers_by_criteria(aud2.criteria)
                    
                    ids1 = set(c.id for c in customers1)
                    ids2 = set(c.id for c in customers2)
                    
                    overlap_ids = ids1.intersection(ids2)
                    
                    # Salvar resultados no session_state para permitir downloads
                    st.session_state.overlap_analysis = {
                        'aud1_name': aud1.name,
                        'aud2_name': aud2.name,
                        'customers1': customers1,
                        'customers2': customers2,
                        'overlap_ids': overlap_ids,
                        'ids1': ids1,
                        'ids2': ids2
                    }
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(f"{aud1.name}", len(ids1))
                    with col2:
                        st.metric(f"{aud2.name}", len(ids2))
                    with col3:
                        st.metric("Sobreposição", len(overlap_ids))
                    
                    if len(overlap_ids) > 0:
                        overlap_rate = len(overlap_ids) / len(ids1.union(ids2)) * 100
                        st.info(f"📊 Taxa de sobreposição: {overlap_rate:.1f}%")
                    else:
                        st.info("📊 Não há sobreposição entre essas audiências.")
            
            # Mostrar opções de download se análise foi feita
            if 'overlap_analysis' in st.session_state:
                st.subheader("📤 Opções de Extração")
                
                analysis = st.session_state.overlap_analysis
                aud1_name = analysis['aud1_name']
                aud2_name = analysis['aud2_name']
                customers1 = analysis['customers1']
                customers2 = analysis['customers2']
                overlap_ids = analysis['overlap_ids']
                ids1 = analysis['ids1']
                ids2 = analysis['ids2']
                
                if len(overlap_ids) > 0:
                    col_extract1, col_extract2, col_extract3 = st.columns(3)
                    
                    with col_extract1:
                        # Extrair sobreposição
                        overlap_customers = [c for c in customers1 if c.id in overlap_ids]
                        if overlap_customers:
                            csv_data = audience_service._generate_audience_csv(overlap_customers)
                            st.download_button(
                                label=f"📥 Baixar Sobreposição ({len(overlap_customers)})",
                                data=csv_data,
                                file_name=f"sobreposicao_{aud1_name.replace(' ', '_')}_{aud2_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                key="download_overlap_unique"
                            )
                    
                    with col_extract2:
                        # Extrair exclusivos da primeira audiência
                        exclusive1_ids = ids1 - ids2
                        exclusive1_customers = [c for c in customers1 if c.id in exclusive1_ids]
                        if exclusive1_customers:
                            csv_data = audience_service._generate_audience_csv(exclusive1_customers)
                            st.download_button(
                                label=f"📥 Exclusivos {aud1_name} ({len(exclusive1_customers)})",
                                data=csv_data,
                                file_name=f"exclusivos_{aud1_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                key="download_exclusive1_unique"
                            )
                        else:
                            st.info("Nenhum cliente exclusivo na primeira audiência")
                    
                    with col_extract3:
                        # Extrair exclusivos da segunda audiência
                        exclusive2_ids = ids2 - ids1
                        exclusive2_customers = [c for c in customers2 if c.id in exclusive2_ids]
                        if exclusive2_customers:
                            csv_data = audience_service._generate_audience_csv(exclusive2_customers)
                            st.download_button(
                                label=f"📥 Exclusivos {aud2_name} ({len(exclusive2_customers)})",
                                data=csv_data,
                                file_name=f"exclusivos_{aud2_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                key="download_exclusive2_unique"
                            )
                        else:
                            st.info("Nenhum cliente exclusivo na segunda audiência")
                
                # Mostrar preview dos clientes sobrepostos se houver
                if len(overlap_ids) > 0:
                    st.subheader("👀 Preview dos Clientes Sobrepostos")
                    
                    overlap_customers = [c for c in customers1 if c.id in overlap_ids]
                    preview_limit = min(10, len(overlap_customers))
                    
                    preview_data = []
                    for customer in overlap_customers[:preview_limit]:
                        preview_data.append({
                            'Nome': customer.data.nome or 'N/A',
                            'Email': customer.data.email or 'N/A',
                            'Documento': customer.data.documento or 'N/A',
                            'Cidade': customer.data.cidade or 'N/A',
                            'Estado': customer.data.estado or 'N/A'
                        })
                    
                    if preview_data:
                        df_preview = pd.DataFrame(preview_data)
                        st.dataframe(df_preview, use_container_width=True)
                        
                        if len(overlap_customers) > preview_limit:
                            st.info(f"Mostrando {preview_limit} de {len(overlap_customers)} clientes sobrepostos. Baixe o CSV para ver todos.")
                
                # Gráfico visual da sobreposição
                if len(overlap_ids) > 0:
                    st.subheader("📊 Visualização da Sobreposição")
                    
                    # Criar dados para gráfico de Venn simplificado
                    exclusive1 = len(ids1 - ids2)
                    exclusive2 = len(ids2 - ids1)
                    overlap = len(overlap_ids)
                    
                    venn_data = {
                        'Categoria': [f'Exclusivos {aud1_name}', 'Sobreposição', f'Exclusivos {aud2_name}'],
                        'Quantidade': [exclusive1, overlap, exclusive2],
                        'Cor': ['#ff7f0e', '#2ca02c', '#1f77b4']
                    }
                    
                    fig = px.bar(
                        x=venn_data['Categoria'],
                        y=venn_data['Quantidade'],
                        color=venn_data['Categoria'],
                        title=f"Distribuição de Clientes: {aud1_name} vs {aud2_name}",
                        labels={'x': 'Categoria', 'y': 'Número de Clientes'},
                        color_discrete_sequence=venn_data['Cor']
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                # Botão para limpar análise
                if st.button("🧹 Limpar Análise", key="clear_overlap_analysis"):
                    del st.session_state.overlap_analysis
                    st.rerun()
        
        else:
            st.info("São necessárias pelo menos 2 audiências para análise de sobreposição.")

def _get_criteria_summary(criteria) -> list:
    """Gera resumo dos critérios de uma audiência"""
    summary = []
    criteria_dict = criteria.to_dict()
    
    for key, value in criteria_dict.items():
        if value is not None:
            # Traduzir nomes dos campos com tratamento de tipos
            try:
                if key == 'nome_contains':
                    summary.append(f'Nome contém "{value}"')
                elif key == 'email_contains':
                    summary.append(f'Email contém "{value}"')
                elif key == 'documento_equals':
                    summary.append(f'Documento = {value}')
                elif key == 'telefone_contains':
                    summary.append(f'Telefone contém "{value}"')
                elif key == 'cidade_equals':
                    summary.append(f'Cidade = {value}')
                elif key == 'estado_equals':
                    summary.append(f'Estado = {value}')
                elif key == 'cep_starts_with':
                    summary.append(f'CEP inicia com {value}')
                elif key == 'profissao_contains':
                    summary.append(f'Profissão contém "{value}"')
                elif key == 'aniversariantes_mes':
                    summary.append(f'Aniversariantes de {_get_month_name(value)}')
                elif key == 'confidence_score_min':
                    summary.append(f'Confiança ≥ {value}')
                elif key == 'confidence_score_max':
                    summary.append(f'Confiança ≤ {value}')
                elif key == 'has_email':
                    summary.append(f'{"Tem" if value else "Não tem"} email')
                elif key == 'has_telefone':
                    summary.append(f'{"Tem" if value else "Não tem"} telefone')
                elif key == 'has_endereco':
                    summary.append(f'{"Tem" if value else "Não tem"} endereço')
                elif key == 'sources_include' and isinstance(value, list):
                    summary.append(f'Inclui fontes: {", ".join(value)}')
                elif key == 'sources_exclude' and isinstance(value, list):
                    summary.append(f'Exclui fontes: {", ".join(value)}')
                elif key == 'updated_in_last_days':
                    summary.append(f'Atualizado nos últimos {value} dias')
                elif key == 'data_nascimento_from':
                    summary.append(f'Nascimento desde {value}')
                elif key == 'data_nascimento_to':
                    summary.append(f'Nascimento até {value}')
                elif key == 'created_from':
                    summary.append(f'Cadastrado desde {value}')
                elif key == 'created_to':
                    summary.append(f'Cadastrado até {value}')
                elif key == 'has_history':
                    summary.append(f'{"Tem" if value else "Não tem"} histórico')
            except Exception as e:
                # Em caso de erro, apenas adiciona o campo sem formatação especial
                summary.append(f'{key}: {value}')
    
    return summary[:5]  # Mostrar apenas os primeiros 5 critérios

def _get_month_name(month_number: int) -> str:
    """Retorna o nome do mês em português"""
    meses = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    return meses.get(month_number, "Mês inválido")