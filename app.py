
import streamlit as st
import pandas as pd
import plotly.express as px
import calendar

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Gastos Mensais - Jacobina/BA",
    page_icon="📊",
    layout="wide"
)

# --- FUNÇÃO DE CARREGAMENTO DE DADOS (OTIMIZADA) ---
@st.cache_data
def carregar_dados():
    # ATENÇÃO: Verifique se este é o nome do seu arquivo de dados unificado
    caminho_do_arquivo = 'dados/despesas_2024_completo.csv' 
    
    try:
        df = pd.read_csv(caminho_do_arquivo, sep=';', encoding='latin-1')
    except FileNotFoundError:
        st.error(f"Arquivo não encontrado em '{caminho_do_arquivo}'. Verifique o nome e o caminho do seu arquivo de dados unificado.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Ocorreu um erro ao ler o arquivo CSV. Verifique a codificação e o formato do arquivo. Erro: {e}")
        return pd.DataFrame()

    df.rename(columns={
        'DescriÃ§Ã£o': 'Descricao',
        'Unnamed: 7': 'Função'
        }, inplace=True)
    df['Valor'] = df['Valor'].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
    df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce')
    df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
    df.dropna(subset=['Valor', 'Data'], inplace=True)
    
    # Criação de novas colunas para filtros e gráficos
    df['Ano'] = df['Data'].dt.year
    df['Mes_Num'] = df['Data'].dt.month
    mapa_meses = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
        5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
        9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }
    df['Mes_Nome'] = df['Mes_Num'].map(mapa_meses)
    
    return df

# Carrega os dados
df = carregar_dados()

if df.empty:
    st.warning("Não há dados para exibir. Verifique as mensagens de erro acima.")
else:
    # --- BARRA LATERAL (SIDEBAR) COM O FILTRO DE ANO ---
    st.sidebar.header("Filtros")

    anos_disponiveis = sorted(df['Ano'].unique(), reverse=True)
    ano_selecionado = st.sidebar.selectbox(
        "Selecione o Ano:",
        anos_disponiveis
    )

    # --- FILTRAGEM DOS DADOS COM BASE NO ANO SELECIONADO ---
    df_filtrado_ano = df[df['Ano'] == ano_selecionado]
    st.sidebar.subheader("Filtro por Função")
    funcoes_disponiveis = sorted(df_filtrado_ano['Função'].dropna().unique())
    funcoes_selecionadas = st.sidebar.multiselect(
    "Selecione uma ou mais Funções:",
    options=funcoes_disponiveis,
    default=funcoes_disponiveis 
)
    if funcoes_selecionadas:
        df_filtrado = df_filtrado_ano[df_filtrado_ano['Função'].isin(funcoes_selecionadas)]
    else:
        df_filtrado = pd.DataFrame(columns=df_filtrado_ano.columns)

    # --- DASHBOARD PRINCIPAL ---
    st.title(f"📊 Análise de Despesas Públicas - Jacobina/BA")
    st.subheader(f"Visão Mensal para o Ano de {ano_selecionado}")
    st.divider()

    # --- MÉTRICAS (KPIs) PARA O ANO SELECIONADO ---
    col1, col2, col3 = st.columns(3)
    valor_total_ano = df_filtrado['Valor'].sum()
    col1.metric("Valor Total Gasto no Ano", f"R$ {valor_total_ano:,.2f}")
    total_transacoes_ano = len(df_filtrado)
    col2.metric("Nº de Transações no Ano", f"{total_transacoes_ano:,}")
    media_por_transacao_ano = valor_total_ano / total_transacoes_ano if total_transacoes_ano > 0 else 0
    col3.metric("Média por Transação", f"R$ {media_por_transacao_ano:,.2f}")
    st.divider()

    # --- GRÁFICO ÚNICO E PRINCIPAL ---
    st.subheader(f"Gastos por mês no ano de {ano_selecionado}")

    # Preparando os dados para o gráfico
    gastos_mensais = df_filtrado.groupby(['Mes_Num', 'Mes_Nome'])['Valor'].sum().reset_index()
    gastos_mensais.sort_values('Mes_Num', inplace=True)

    # Criando o gráfico de linha
    fig_barras_anual = px.bar(
        gastos_mensais,
        x='Mes_Nome',
        y='Valor',
        title=f"Comparativo de Gastos Mensais em {ano_selecionado}",
        labels={'Mes_Nome': 'Mês', 'Valor': 'Valor Gasto (R$)'},
        text_auto='.2s', # <--- ESTA LINHA ADICIONA OS VALORES
        height=500
    )
    fig_barras_anual.update_traces(textposition='outside') # Coloca os valores fora das barras
    fig_barras_anual.update_layout(
        yaxis_title="Valor Gasto (R$)", 
        xaxis_title="Mês do Ano"
    )
    st.plotly_chart(fig_barras_anual, use_container_width=True)
    # --- FIM DA MUDANÇA ---

    # Expander para mostrar os dados brutos do ano selecionado
    with st.expander(f"Ver dados brutos de {ano_selecionado}"):
        st.dataframe(df_filtrado)