# utils/ui_helpers.py
"""
Utilitários para interface do usuário
"""

import streamlit as st
import time
from typing import Optional, Callable

def force_refresh_with_message(message: str = "Dados atualizados!", 
                             delay: float = 0.5,
                             clear_cache: bool = True):
    """
    Força refresh da página com mensagem de sucesso
    
    Args:
        message: Mensagem a ser exibida
        delay: Tempo de espera antes do refresh
        clear_cache: Se deve limpar o cache do Streamlit
    """
    if message:
        st.success(message)
    
    if clear_cache:
        st.cache_data.clear()
    
    if delay > 0:
        time.sleep(delay)
    
    st.rerun()

def handle_operation_with_refresh(operation: Callable, 
                                success_message: str,
                                error_message: str = "Erro na operação",
                                spinner_message: str = "Processando...",
                                delay: float = 0.5):
    """
    Executa operação com spinner e refresh automático
    
    Args:
        operation: Função a ser executada
        success_message: Mensagem de sucesso
        error_message: Mensagem de erro
        spinner_message: Mensagem do spinner
        delay: Tempo de espera antes do refresh
    """
    with st.spinner(spinner_message):
        try:
            result = operation()
            if result:
                force_refresh_with_message(success_message, delay)
                return True
            else:
                st.error(error_message)
                return False
        except Exception as e:
            st.error(f"{error_message}: {str(e)}")
            return False

def confirm_action(action_name: str, 
                  item_name: str, 
                  key: str,
                  danger: bool = True) -> bool:
    """
    Sistema de confirmação para ações críticas
    
    Args:
        action_name: Nome da ação (ex: "excluir", "deletar")
        item_name: Nome do item (ex: nome da audiência)
        key: Chave única para o estado
        danger: Se é uma ação perigosa (muda a cor)
    
    Returns:
        True se confirmado, False caso contrário
    """
    confirm_key = f"confirm_{key}"
    
    if confirm_key not in st.session_state:
        st.session_state[confirm_key] = False
    
    if not st.session_state[confirm_key]:
        # Primeira vez - mostrar aviso
        st.session_state[confirm_key] = True
        if danger:
            st.warning(f"⚠️ Confirme: {action_name} '{item_name}'?")
        else:
            st.info(f"ℹ️ Confirme: {action_name} '{item_name}'?")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirmar", key=f"{key}_yes", type="primary"):
                return True
        with col2:
            if st.button("❌ Cancelar", key=f"{key}_no"):
                del st.session_state[confirm_key]
                st.rerun()
        
        return False
    else:
        # Já confirmado
        del st.session_state[confirm_key]
        return True

def auto_refresh_data(key: str, force: bool = False):
    """
    Sistema automático de refresh de dados
    
    Args:
        key: Chave única para o tipo de dados
        force: Forçar refresh mesmo que não tenha mudanças
    """
    cache_key = f"{key}_cache_version"
    refresh_key = f"force_{key}_refresh"
    
    # Inicializar versão do cache
    if cache_key not in st.session_state:
        st.session_state[cache_key] = 0
    
    # Verificar se precisa fazer refresh
    if st.session_state.get(refresh_key, False) or force:
        st.session_state[cache_key] += 1
        st.session_state[refresh_key] = False
        st.cache_data.clear()

def mark_for_refresh(key: str):
    """
    Marca dados para refresh na próxima renderização
    
    Args:
        key: Chave única para o tipo de dados
    """
    refresh_key = f"force_{key}_refresh"
    st.session_state[refresh_key] = True

def show_loading_state(message: str = "Carregando...", 
                      min_time: float = 0.5):
    """
    Context manager para mostrar estado de loading
    
    Args:
        message: Mensagem de loading
        min_time: Tempo mínimo de exibição
    """
    class LoadingContext:
        def __init__(self, msg, min_t):
            self.message = msg
            self.min_time = min_t
            self.start_time = None
            self.spinner = None
        
        def __enter__(self):
            self.start_time = time.time()
            self.spinner = st.spinner(self.message)
            self.spinner.__enter__()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            elapsed = time.time() - self.start_time
            if elapsed < self.min_time:
                time.sleep(self.min_time - elapsed)
            
            self.spinner.__exit__(exc_type, exc_val, exc_tb)
    
    return LoadingContext(message, min_time)

def show_success_with_auto_hide(message: str, 
                               duration: float = 3.0,
                               auto_refresh: bool = False):
    """
    Mostra mensagem de sucesso que desaparece automaticamente
    
    Args:
        message: Mensagem de sucesso
        duration: Duração em segundos
        auto_refresh: Se deve fazer refresh após esconder
    """
    success_placeholder = st.empty()
    success_placeholder.success(message)
    
    # Usar JavaScript para esconder após duration
    if duration > 0:
        time.sleep(duration)
        success_placeholder.empty()
        
        if auto_refresh:
            st.rerun()

def batch_operation_progress(items: list, 
                           operation: Callable,
                           operation_name: str = "Processando",
                           success_callback: Optional[Callable] = None):
    """
    Executa operação em lote com barra de progresso
    
    Args:
        items: Lista de itens para processar
        operation: Função que recebe um item e retorna True/False
        operation_name: Nome da operação
        success_callback: Callback executado ao final se houver sucessos
    
    Returns:
        Tupla (sucessos, erros, total)
    """
    if not items:
        st.info("Nenhum item para processar.")
        return 0, 0, 0
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    success_count = 0
    error_count = 0
    
    for i, item in enumerate(items):
        status_text.text(f"{operation_name} item {i + 1} de {len(items)}...")
        
        try:
            if operation(item):
                success_count += 1
            else:
                error_count += 1
        except Exception:
            error_count += 1
        
        progress_bar.progress((i + 1) / len(items))
    
    progress_bar.empty()
    status_text.empty()
    
    # Mostrar resultado
    if success_count > 0:
        st.success(f"✅ {success_count} item(s) processado(s) com sucesso!")
        if success_callback:
            success_callback()
    
    if error_count > 0:
        st.error(f"❌ {error_count} item(s) com erro!")
    
    return success_count, error_count, len(items)