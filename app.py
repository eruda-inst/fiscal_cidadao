# app.py - Versão 6 (FINAL) - Limpeza de dados de moeda robusta

import streamlit as st
import pandas as pd
import plotly.express as px
import calendar

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Dashboard de Despesas - Jacobina/BA",
    layout="wide"
)

# --- FUNÇÃO DE CARREGAMENTO DE DADOS (VERSÃO FINAL) ---
@st.cache_data
def carregar_dados():
    caminho_do_arquivo = 'dados/despesas_2024_completo.csv'
    
    try:
        df_bruto = pd.read_csv(caminho_do_arquivo, sep=';', encoding='utf-8')
    except UnicodeDecodeError:
        df_bruto = pd.read_csv(caminho_do_arquivo, sep=';', encoding='latin-1')
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao ler o arquivo CSV: {e}")
        return pd.DataFrame()

    colunas_essenciais = ['Data', 'DescriÃ§Ã£o', 'Valor', 'Credor']
    
    if not all(coluna in df_bruto.columns for coluna in colunas_essenciais):
        st.error("O arquivo CSV não contém as colunas esperadas ('Data', 'DescriÃ§Ã£o', 'Valor', 'Credor'). Verifique o arquivo baixado.")
        return pd.DataFrame()

    df = df_bruto[colunas_essenciais].copy()
    df.rename(columns={'DescriÃ§Ã£o': 'Descricao'}, inplace=True)
    
    # --- LIMPEZA ROBUSTA DA COLUNA 'VALOR' ---
    df['Valor'] = df['Valor'].astype(str) \
                            .str.replace('R$', '', regex=False) \
                            .str.replace('.', '', regex=False) \
                            .str.replace(',', '.', regex=False) \
                            .str.strip()

    df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce')
    df.dropna(subset=['Valor'], inplace=True) # Remove linhas onde a conversão ainda falhou
    
    # --- FIM DA CORREÇÃO ---
    
    df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
    df.dropna(subset=['Data'], inplace=True)
    
    df['Mes_Num'] = df['Data'].dt.month
    df['Mes_Nome'] = df['Mes_Num'].apply(lambda x: calendar.month_name[x].capitalize())
    
    return df

df = carregar_dados()

if not df.empty:
    st.sidebar.header("Filtros")
    lista_meses = df['Mes_Nome'].unique().tolist()
    ordem_meses = list(calendar.month_name)[1:]
    lista_meses_ordenada = sorted(lista_meses, key=lambda x: ordem_meses.index(x.lower().capitalize()))
    lista_meses_ordenada.insert(0, "Todos")

    mes_selecionado = st.sidebar.selectbox("Selecione um Mês:", lista_meses_ordenada)

    if mes_selecionado == "Todos":
        df_filtrado = df
    else:
        df_filtrado = df[df['Mes_Nome'] == mes_selecionado]

    st.title("📊 Dashboard de Despesas Públicas - Jacobina/BA (2024)")
    st.markdown(f"Analisando os gastos de: **{mes_selecionado}**")
    st.header("Resumo Geral")
    col1, col2, col3 = st.columns(3)
    valor_total = df_filtrado['Valor'].sum()
    col1.metric("Valor Total Gasto", f"R$ {valor_total:,.2f}")
    total_transacoes = len(df_filtrado)
    col2.metric("Total de Transações", f"{total_transacoes}")
    if total_transacoes > 0:
        media_por_transacao = valor_total / total_transacoes
        col3.metric("Média por Transação", f"R$ {media_por_transacao:,.2f}")
    else:
        col3.metric("Média por Transação", "R$ 0,00")
    st.divider()
    st.header("Análises Detalhadas")
    st.subheader(f"Top 10 Credores ({mes_selecionado})")
    top_10_credores = df_filtrado.groupby('Credor')['Valor'].sum().nlargest(10).sort_values(ascending=True)
    if not top_10_credores.empty:
        fig_credores = px.bar(top_10_credores, x='Valor', y=top_10_credores.index, orientation='h', labels={'Valor': 'Valor Gasto (R$)', 'y': 'Credor'}, text_auto='.2s')
        st.plotly_chart(fig_credores, use_container_width=True)
    else:
        st.warning("Não há dados de credores para exibir no período selecionado.")
    if mes_selecionado == "Todos":
        st.subheader("Gastos ao Longo do Ano")
        gastos_mensais = df.groupby('Mes_Nome')['Valor'].sum().reset_index()
        gastos_mensais_ordenados = sorted(gastos_mensais['Mes_Nome'].tolist(), key=lambda x: ordem_meses.index(x.lower().capitalize()))
        
        fig_linha_tempo = px.line(gastos_mensais, x='Mes_Nome', y='Valor', category_orders={"Mes_Nome": gastos_mensais_ordenados}, title="Evolução Mensal dos Gastos", labels={'Mes_Nome': 'Mês', 'Valor': 'Valor Gasto (R$)'}, markers=True)
        st.plotly_chart(fig_linha_tempo, use_container_width=True)

    with st.expander("Clique para ver a tabela de dados completa"):
        st.dataframe(df_filtrado)
else:
    st.error("Não foi possível carregar os dados para exibir o dashboard. Verifique o arquivo CSV e as mensagens de erro acima.")