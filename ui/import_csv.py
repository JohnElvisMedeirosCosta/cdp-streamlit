# ui/import_csv.py
"""
Páginas para importação de clientes via CSV
"""

import streamlit as st
import pandas as pd
import json
import plotly.express as px
from datetime import datetime
from core.cdp import CustomerDataPlatform
from services.import_service import ImportService
from config import CSV_MAX_PREVIEW_ROWS, DATA_SOURCES

def show_import_csv(cdp: CustomerDataPlatform):
    """Exibe as páginas de importação CSV"""
    st.header("📁 Importar Clientes via CSV")
    
    # Inicializar estado da importação se não existir
    if 'import_step' not in st.session_state:
        st.session_state.import_step = 'upload'
    if 'import_data' not in st.session_state:
        st.session_state.import_data = None
    if 'import_results' not in st.session_state:
        st.session_state.import_results = None
    
    # Inicializar serviço de importação
    import_service = ImportService(cdp)
    
    # Step 1: Upload do arquivo
    if st.session_state.import_step == 'upload':
        show_csv_upload(import_service)
    
    # Step 2: Confirmação dos dados
    elif st.session_state.import_step == 'confirm':
        show_csv_confirmation(import_service)
    
    # Step 3: Resultados da importação
    elif st.session_state.import_step == 'results':
        show_import_results()

def show_csv_upload(import_service: ImportService):
    """Exibe tela de upload do CSV"""
    st.subheader("1️⃣ Upload do Arquivo CSV")
    
    # Instruções e template
    with st.expander("📖 Instruções de Formato"):
        st.markdown("""
        **Colunas aceitas no CSV (todas opcionais):**
        - `nome` - Nome completo do cliente
        - `email` - Endereço de email
        - `documento` - CPF/CNPJ (apenas números)
        - `telefone` - Número de telefone
        - `endereco` - Endereço completo
        - `cidade` - Cidade
        - `estado` - Estado/UF
        - `cep` - Código postal
        - `data_nascimento` - Data no formato YYYY-MM-DD
        - `profissao` - Profissão/ocupação
        
        **Notas importantes:**
        - O arquivo deve ter cabeçalho (primeira linha com nomes das colunas)
        - Separador: vírgula (,)
        - Codificação: UTF-8
        - Pelo menos uma coluna deve estar preenchida
        """)
        
        # Template para download
        csv_template = import_service.create_template_csv()
        st.download_button(
            label="📥 Baixar Template CSV",
            data=csv_template,
            file_name="template_clientes.csv",
            mime="text/csv"
        )
    
    # Upload do arquivo
    uploaded_file = st.file_uploader(
        "Escolha o arquivo CSV",
        type=['csv'],
        help="Arquivo CSV com dados dos clientes"
    )
    
    if uploaded_file is not None:
        try:
            # Ler o arquivo CSV
            df = pd.read_csv(uploaded_file)
            
            # Validar dados
            validation = import_service.validate_csv_data(df)
            
            if not validation['is_valid']:
                for error in validation['errors']:
                    st.error(f"❌ {error}")
                return
            
            # Mostrar preview dos dados
            st.success(f"✅ Arquivo carregado com sucesso! {len(df)} registros encontrados.")
            
            st.subheader("👀 Preview dos Dados")
            preview_rows = min(CSV_MAX_PREVIEW_ROWS, len(df))
            st.dataframe(df.head(preview_rows), use_container_width=True)
            
            if len(df) > preview_rows:
                st.info(f"Mostrando apenas os primeiros {preview_rows} registros. Total: {len(df)} registros.")
            
            # Análise das colunas
            st.subheader("📊 Análise das Colunas")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Colunas encontradas:**")
                for col in validation['recognized_columns']:
                    st.write(f"✅ {col}")
                for col in validation['ignored_columns']:
                    st.write(f"⚠️ {col} (será ignorada)")
            
            with col2:
                st.write("**Estatísticas:**")
                for col, stats in validation['statistics'].items():
                    st.write(f"- {col}: {stats['filled']}/{stats['total']} ({stats['percentage']:.1f}%)")
            
            # Mostrar avisos
            if validation['warnings']:
                st.warning("⚠️ Avisos encontrados:")
                for warning in validation['warnings']:
                    st.write(f"- {warning}")
            
            # Configurações de importação
            st.subheader("⚙️ Configurações de Importação")
            
            col1, col2 = st.columns(2)
            
            with col1:
                source = st.selectbox("Fonte dos dados:", DATA_SOURCES)
            
            with col2:
                force_merge = st.checkbox(
                    "Forçar merge em conflitos",
                    help="Se marcado, conflitos serão resolvidos automaticamente"
                )
            
            # Botão para avançar
            if st.button("➡️ Avançar para Confirmação", type="primary"):
                # Processar dados
                processed_data = import_service.process_csv_data(df)
                
                # Salvar dados processados no estado da sessão
                st.session_state.import_data = {
                    'customers': processed_data,
                    'source': source,
                    'force_merge': force_merge,
                    'original_count': len(df),
                    'processed_count': len(processed_data)
                }
                
                st.session_state.import_step = 'confirm'
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ Erro ao processar arquivo: {str(e)}")

def show_csv_confirmation(import_service: ImportService):
    """Exibe tela de confirmação dos dados"""
    st.subheader("2️⃣ Confirmação dos Dados")
    
    if not st.session_state.import_data:
        st.error("Dados de importação não encontrados!")
        if st.button("🔙 Voltar ao Upload"):
            st.session_state.import_step = 'upload'
            st.rerun()
        return
    
    data = st.session_state.import_data
    customers = data['customers']
    
    # Resumo da importação
    st.info(f"""
    **Resumo da Importação:**
    - Registros no arquivo: {data['original_count']}
    - Registros válidos para importação: {data['processed_count']}
    - Fonte: {data['source']}
    - Forçar merge: {'Sim' if data['force_merge'] else 'Não'}
    """)
    
    # Preview dos dados processados
    st.subheader("👀 Preview dos Dados Processados")
    
    if customers:
        # Converter para DataFrame para melhor visualização
        preview_data = []
        for i, customer in enumerate(customers[:CSV_MAX_PREVIEW_ROWS]):
            row = {'#': i + 1}
            row.update(customer)
            preview_data.append(row)
        
        preview_df = pd.DataFrame(preview_data)
        st.dataframe(preview_df, use_container_width=True)
        
        if len(customers) > CSV_MAX_PREVIEW_ROWS:
            st.info(f"Mostrando apenas os primeiros {CSV_MAX_PREVIEW_ROWS} registros. Total a importar: {len(customers)}")
    
    # Análise de conflitos potenciais
    with st.spinner("🔍 Analisando conflitos potenciais..."):
        conflicts_analysis = import_service.analyze_potential_conflicts(customers)
    
    if conflicts_analysis['potential_conflicts'] > 0:
        st.warning(f"⚠️ {conflicts_analysis['potential_conflicts']} conflito(s) potencial(is) detectado(s)")
        
        with st.expander("Ver detalhes dos conflitos"):
            for conflict in conflicts_analysis['details']:
                st.write(f"- **Linha {conflict['row']}**: {conflict['reason']}")
    else:
        st.success("✅ Nenhum conflito potencial detectado!")
    
    # Botões de ação
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔙 Voltar ao Upload"):
            st.session_state.import_step = 'upload'
            st.session_state.import_data = None
            st.rerun()
    
    with col2:
        if st.button("❌ Cancelar Importação"):
            st.session_state.import_step = 'upload'
            st.session_state.import_data = None
            st.session_state.import_results = None
            st.rerun()
    
    with col3:
        if st.button("✅ Confirmar Importação", type="primary"):
            # Executar importação
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def progress_callback(progress, message):
                progress_bar.progress(progress)
                status_text.text(message)
            
            with st.spinner("📤 Importando clientes..."):
                results = import_service.execute_import(
                    customers, 
                    data['source'], 
                    data['force_merge'],
                    progress_callback
                )
            
            progress_bar.empty()
            status_text.empty()
            
            st.session_state.import_results = results
            st.session_state.import_step = 'results'
            st.rerun()

def show_import_results():
    """Exibe tela de resultados da importação"""
    st.subheader("3️⃣ Resultados da Importação")
    
    if not st.session_state.import_results:
        st.error("Resultados da importação não encontrados!")
        return
    
    results = st.session_state.import_results
    
    # Resumo dos resultados
    st.success("🎉 Importação concluída!")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Processado", results.total_processed)
    with col2:
        st.metric("Criados", results.created, delta=results.created)
    with col3:
        st.metric("Atualizados", results.updated, delta=results.updated)
    with col4:
        st.metric("Conflitos", results.conflicts, delta=-results.conflicts if results.conflicts > 0 else None)
    with col5:
        st.metric("Erros", results.errors, delta=-results.errors if results.errors > 0 else None)
    
    # Gráfico de resultados
    if results.total_processed > 0:
        fig = px.pie(
            values=[results.created, results.updated, results.conflicts, results.errors],
            names=['Criados', 'Atualizados', 'Conflitos', 'Erros'],
            title="Distribuição dos Resultados da Importação"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Detalhes por status
    if results.details:
        st.subheader("📝 Detalhes da Importação")
        
        # Filtros
        status_filter = st.selectbox(
            "Filtrar por status:",
            ["Todos", "created", "updated", "conflict_detected", "error"]
        )
        
        # Filtrar dados
        filtered_details = results.details
        if status_filter != "Todos":
            filtered_details = [d for d in results.details if d['status'] == status_filter]
        
        # Mostrar tabela
        if filtered_details:
            details_df = pd.DataFrame(filtered_details)
            
            # Mapear status para símbolos
            status_map = {
                'created': '✅ Criado',
                'updated': '🔄 Atualizado',
                'conflict_detected': '⚠️ Conflito',
                'error': '❌ Erro'
            }
            
            details_df['Status'] = details_df['status'].map(status_map)
            details_df = details_df[['row', 'customer', 'Status', 'message']]
            details_df.columns = ['Linha', 'Cliente', 'Status', 'Mensagem']
            
            st.dataframe(details_df, use_container_width=True)
        else:
            st.info("Nenhum registro encontrado para o filtro selecionado.")
    
    # Botões de ação
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📁 Nova Importação"):
            st.session_state.import_step = 'upload'
            st.session_state.import_data = None
            st.session_state.import_results = None
            st.rerun()
    
    with col2:
        # Download do relatório
        report_data = {
            'resumo': {
                'total_processado': results.total_processed,
                'criados': results.created,
                'atualizados': results.updated,
                'conflitos': results.conflicts,
                'erros': results.errors
            },
            'detalhes': results.details
        }
        
        report_json = json.dumps(report_data, indent=2, ensure_ascii=False)
        st.download_button(
            label="📥 Baixar Relatório JSON",
            data=report_json,
            file_name=f"relatorio_importacao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )