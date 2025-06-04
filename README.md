Sistema completo de gestão unificada de dados de clientes com detecção inteligente de duplicatas, interface web moderna e funcionalidades avançadas de importação/exportação.

## 🚀 Principais Funcionalidades

- **Dashboard Interativo**: Visão geral completa do sistema
- **Cadastro Individual**: Formulário completo para adicionar clientes
- **Importação CSV**: Sistema avançado de importação em lote com validação
- **Busca Inteligente**: Múltiplos filtros para encontrar clientes
- **Sistema de Audiências**: Criação e gestão de segmentações de clientes
- **Extração CSV**: Exportação de audiências com dados filtrados
- **Histórico Completo**: Rastreamento de todas as alterações
- **Estatísticas Avançadas**: Análises detalhadas e relatórios
- **Detecção de Duplicatas**: Algoritmo inteligente para identificar clientes similares
- **Gestão de Conflitos**: Sistema para resolver conflitos de dados
- **Exportação Flexível**: Múltiplos formatos de exportação

## 📁 Estrutura do Projeto

```
cdp_project/
├── requirements.txt         # Dependências
├── config.py               # Configurações globais
├── main.py                 # Aplicação principal Streamlit
├── models/                 # Modelos de dados
│   ├── __init__.py
│   ├── database.py         # Modelos SQLAlchemy
│   └── schemas.py          # Dataclasses e schemas
├── core/                   # Lógica principal
│   ├── __init__.py
│   ├── matcher.py          # Sistema de matching
│   └── cdp.py             # Classe principal CDP
├── services/               # Serviços
│   ├── __init__.py
│   ├── import_service.py   # Importação de dados
│   └── export_service.py   # Exportação de dados
├── ui/                     # Interface Streamlit
│   ├── __init__.py
│   ├── components.py       # Componentes reutilizáveis
│   ├── dashboard.py        # Página dashboard
│   ├── add_customer.py     # Página adicionar cliente
│   ├── import_csv.py       # Páginas importação CSV
│   ├── search_customers.py # Página busca
│   ├── history.py          # Página histórico
│   └── statistics.py       # Página estatísticas
└── utils/                  # Utilitários
    ├── __init__.py
    ├── helpers.py          # Funções auxiliares
    └── validators.py       # Validadores
```

## 🛠️ Instalação e Execução

### 1. Clone o projeto
```bash
git clone <repository-url>
cd cdp_project
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Execute a aplicação
```bash
streamlit run main.py
```

### 4. Acesse no navegador
```
http://localhost:8501
```

## 📋 Dependências

- **streamlit**: Interface web interativa
- **sqlalchemy**: ORM para banco de dados
- **pandas**: Manipulação de dados
- **plotly**: Gráficos interativos

## 🎯 Como Usar

### 1. Dashboard
- Visualize métricas principais do sistema
- Veja lista de clientes cadastrados
- Analise distribuição de scores de confiança

### 2. Adicionar Cliente
- Preencha o formulário completo
- Configure fonte dos dados
- Sistema detecta automaticamente duplicatas

### 3. Importar CSV
**Fluxo em 3 etapas:**
- **Upload**: Envie arquivo CSV com validação automática
- **Confirmação**: Revise dados e analise conflitos potenciais
- **Resultados**: Acompanhe progresso e baixe relatórios

**Formato CSV aceito:**
```csv
nome,email,documento,telefone,endereco,cidade,estado,cep,data_nascimento,profissao
João Silva,joao@email.com,12345678901,11999887766,Rua A 123,São Paulo,SP,01234567,1985-05-15,Engenheiro
```

### 4. Buscar Clientes
- Use múltiplos filtros simultâneos
- Visualize resultados detalhados
- Exporte, veja histórico ou exclua clientes

### 5. Histórico
- Acompanhe todas as alterações por cliente
- Visualize gráficos de alterações por campo
- Exporte histórico em CSV

### 6. Estatísticas
- Análises completas de dados
- Gráficos interativos
- Relatórios de qualidade dos dados
- Distribuição geográfica

## 🔧 Configurações

### Banco de Dados
Por padrão usa SQLite local (`customer_data.db`). Para usar PostgreSQL:

```python
# config.py
DATABASE_URL = "postgresql://user:password@localhost/dbname"
```

### Matching de Clientes
Ajuste os pesos dos campos no arquivo `config.py`:

```python
FIELD_WEIGHTS = {
    'documento': 0.40,    # Peso alto para documentos
    'email': 0.15,
    'nome': 0.25,
    'telefone': 0.10,
    'endereco': 0.05,
    'data_nascimento': 0.05
}
```

### Threshold de Similaridade
```python
MATCH_THRESHOLD = 0.5  # Mínimo para considerar match
```

## 🧠 Sistema de Matching Inteligente

### Algoritmo de Detecção
1. **Busca por Candidatos**: Encontra clientes similares no banco
2. **Cálculo de Score**: Avalia similaridade ponderada por campo
3. **Detecção de Conflitos**: Identifica informações conflitantes
4. **Decisão de Merge**: Determina se é seguro unificar dados

### Critérios de Conflito
- **Documentos diferentes**: Bloqueia merge automaticamente
- **Nomes muito diferentes**: Gera alerta
- **Telefones diferentes**: Requer confirmação
- **Múltiplos conflitos**: Penaliza score final

## 📊 Tipos de Relatórios

### Relatórios de Importação
- Resumo de operações (criados/atualizados/conflitos/erros)
- Detalhes por registro
- Gráficos de distribuição de resultados

### Relatórios de Estatísticas
- Métricas gerais do sistema
- Análise de fontes de dados
- Completude dos dados
- Distribuição geográfica
- Qualidade dos dados

## 🔒 Validações Implementadas

### Dados de Cliente
- Email: Formato válido
- Documento: CPF (11 dígitos) ou CNPJ (14 dígitos)
- Telefone: 10 ou 11 dígitos
- CEP: 8 dígitos
- Data nascimento: Formato YYYY-MM-DD

### Dados de CSV
- Estrutura válida
- Colunas reconhecidas
- Registros não vazios
- Duplicatas internas

### Integridade do Sistema
- Consistência de timestamps
- Scores de confiança válidos
- Referências de histórico

## 🎨 Interface

### Componentes Reutilizáveis
- Cards de cliente
- Formulários padronizados
- Gráficos interativos
- Métricas visuais

### Navegação
- Menu lateral intuitivo
- Breadcrumbs de processo
- Feedback visual de ações
- Indicadores de progresso

## 🚀 Extensibilidade

### Adicionando Novos Campos
1. Atualize `VALID_CUSTOMER_FIELDS` em `config.py`
2. Adicione campo em `CustomerData` em `schemas.py`
3. Atualize modelo do banco em `database.py`
4. Ajuste formulários em `components.py`

### Novas Fontes de Dados
1. Adicione em `DATA_SOURCES` em `config.py`
2. Implemente parser específico se necessário
3. Atualize validações se aplicável

### Novos Tipos de Relatório
1. Crie função em `export_service.py`
2. Adicione botão na interface
3. Implemente visualização se necessário

## 📈 Performance

### Otimizações Implementadas
- Cache de CDP com `@st.cache_resource`
- Índices no banco de dados
- Paginação de resultados
- Lazy loading de dados

### Recomendações para Produção
- Use PostgreSQL para volumes maiores
- Configure índices adicionais conforme necessário
- Implemente cache Redis para sessões
- Configure backup automático

## 🐛 Troubleshooting

### Problemas Comuns

**Erro de conexão com banco:**
```
Verifique DATABASE_URL em config.py
Confirme permissões de escrita para SQLite
```

**CSV não é processado:**
```
Verifique codificação (deve ser UTF-8)
Confirme separador de colunas (vírgula)
Valide cabeçalhos das colunas
```

**Performance lenta:**
```
Limpe cache: botão na sidebar
Verifique tamanho do banco de dados
Configure índices adicionais se necessário
```

## 📝 Licença

Este projeto está sob licença MIT. Veja arquivo LICENSE para detalhes.

## 👥 Contribuição

1. Fork o projeto
2. Crie branch para feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para branch (`git push origin feature/nova-feature`)
5. Abra Pull Request

---

**Desenvolvido com ❤️ usando Streamlit e Python**