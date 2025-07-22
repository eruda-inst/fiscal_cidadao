import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# --- Configuração da Página ---
st.set_page_config(
    page_title="Portal da Transparência de Jacobina",
    page_icon="💰",
    layout="wide"
)

@st.cache_data
def carregar_dados():
    caminho_arquivo = 'dados/despesas_completo.parquet'
    if not os.path.exists(caminho_arquivo):
        return None
    
    df = pd.read_parquet('dados/despesas_completo.parquet')
    
    df['Valor_Num'] = df['Valor'].astype(str).str.replace(r'[R$\s.]', '', regex=True).str.replace(',', '.', regex=True)
    df['Valor_Num'] = pd.to_numeric(df['Valor_Num'], errors='coerce')
    df['Data_Obj'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
    df.dropna(subset=['Valor_Num', 'Data_Obj'], inplace=True)
    
    return df

# --- Início da Interface da Aplicação ---
df = carregar_dados()

col1, col2 = st.columns([4, 1])
with col1:
    st.title("💰 Portal da Transparência - Jacobina")
    st.markdown("Uma visão simplificada e interativa dos gastos públicos do município.")

with col2:
    # --- INÍCIO DA LÓGICA DINÂMICA ---
    
    caminho_arquivo_data = "ultima_atualizacao.txt"
    data_ultima_att_str = None
    
    # 1. Tenta ler a data do arquivo
    if os.path.exists(caminho_arquivo_data):
        with open(caminho_arquivo_data, 'r') as f:
            data_ultima_att_str = f.read().strip()
    
    # 2. Se a data foi lida com sucesso, calcula o tempo passado
    if data_ultima_att_str:
        try:
            data_ultima_att = datetime.strptime(data_ultima_att_str, "%d/%m/%Y %H:%M:%S")
            hoje = datetime.now()

            diferenca_meses = (hoje.year - data_ultima_att.year) * 12 + (hoje.month - data_ultima_att.month)
            if hoje.day < data_ultima_att.day:
                diferenca_meses -= 1
            
            if diferenca_meses <= 0:
                texto_tempo_passado = "(este mês)"
            elif diferenca_meses == 1:
                texto_tempo_passado = "(há 1 mês)"
            else:
                texto_tempo_passado = f"(há {diferenca_meses} meses)"
            
            # Exibe a data lida e o tempo calculado
            st.caption(f"Última atualização: {data_ultima_att.strftime('%d/%m/%Y %H:%M')} {texto_tempo_passado}")

        except ValueError:
            # Se o arquivo tiver um conteúdo inválido
            st.caption(f"Última atualização: {data_ultima_att_str} (formato inválido)")
    else:
        # 3. Se o arquivo não existir, mostra uma mensagem padrão
        st.caption("Ainda não há dados de atualização.")


# --- Barra Lateral de Filtros ---
st.sidebar.header("Filtros")

# Filtro por Setor (Unidade Orçamentária)
setores = df['Unidade Orcamentaria'].unique()
setor_selecionado = st.sidebar.multiselect(
    'Selecione o Setor Responsável',
    options=setores,
    default=None 
)

# Filtro por Período
data_min = df['Data_Obj'].min()
data_max = df['Data_Obj'].max()
periodo_selecionado = st.sidebar.date_input(
    'Selecione o Período',
    value=(data_min, data_max),
    min_value=data_min,
    max_value=data_max
)

# --- Aplicação dos Filtros ---
df_filtrado = df[
    (df['Data_Obj'] >= pd.to_datetime(periodo_selecionado[0])) &
    (df['Data_Obj'] <= pd.to_datetime(periodo_selecionado[1]))
]

if setor_selecionado: 
    df_filtrado = df_filtrado[df_filtrado['Unidade Orcamentaria'].isin(setor_selecionado)]


if df_filtrado is None:
    st.error(
        "Arquivo de dados não encontrado! 😥"
        "Por favor, execute primeiro o seu scraper e depois o script 'unificador.py' para gerar o arquivo 'dados/despesas_completo.csv'."
    )
else:
    # --- Seção de KPIs (Indicadores Chave) ---
    st.header("Resumo Geral")

    total_gasto = df_filtrado['Valor_Num'].sum()
    principal_unidade = df_filtrado.groupby('Unidade Orcamentaria')['Valor_Num'].sum().idxmax()
    principal_credor = df_filtrado.groupby('Credor')['Valor_Num'].sum().idxmax()
    total_contratos = len(df_filtrado)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Valor Total Gasto", f"R$ {total_gasto/1e6:,.2f} M".replace(',', '#').replace('.', ',').replace('#', '.'))
    col2.metric("Setor Responsável", principal_unidade)
    col3.metric("Principal Fornecedor", principal_credor)
    col4.metric("Total de Registros", f"{total_contratos:,}".replace(',', '.'))

    st.markdown("---") 

    # --- Seção dos Gráficos em Colunas ---
    st.header("Análises Visuais")
    
    col_graf1, col_graf2 = st.columns(2)

    with col_graf1:
        # --- Gráfico 1: Gastos por Unidade Orçamentária (Gráfico de Pizza)
        st.subheader("Distribuição por Unidade Orçamentária")
        gastos_por_unidade = df_filtrado.groupby('Unidade Orcamentaria')['Valor_Num'].sum().sort_values(ascending=False)
        
        top_n = 8
        if len(gastos_por_unidade) > top_n:
            outros = gastos_por_unidade[top_n:].sum()
            gastos_plot = gastos_por_unidade[:top_n]
            gastos_plot['Outros'] = outros
        else:
            gastos_plot = gastos_por_unidade
        
        fig_pizza = px.pie(
            gastos_plot,
            values='Valor_Num',
            names=gastos_plot.index,
            title='Distribuição de Gastos por Unidade Orçamentária',
            hole=.3
        )
        fig_pizza.update_traces(textposition='inside', textinfo='percent+label', insidetextfont=dict(color='white'))
        fig_pizza.update_layout(showlegend=False)
        st.plotly_chart(fig_pizza, use_container_width=True)

    with col_graf2:
        # --- Gráfico 2: Top 10 Fornecedores (Gráfico de Barras)
        st.subheader("Quem Mais Recebe?")
        gastos_por_credor = df_filtrado.groupby('Credor')['Valor_Num'].sum().nlargest(10)
        
        fig_barras = px.bar(
            gastos_por_credor,
            x=gastos_por_credor.values,
            y=gastos_por_credor.index,
            orientation='h',
            title='Top 10 Fornecedores por Valor Total Recebido',
            text=gastos_por_credor.values,
            labels={'x': 'Valor Gasto (R$)', 'y': 'Fornecedor'}
        )
        fig_barras.update_layout(yaxis={'categoryorder':'total ascending'})
        fig_barras.update_traces(texttemplate='R$ %{text:,.2s}', textposition='outside')
        st.plotly_chart(fig_barras, use_container_width=True)

    st.markdown("---")

    # --- Gráfico 3: Evolução dos Gastos (Gráfico de Linha)
    st.header("Evolução dos Gastos ao Longo do Tempo")
    df_filtrado_temporal = df_filtrado[['Data_Obj', 'Valor_Num']].set_index('Data_Obj')
    gastos_mensais = df_filtrado_temporal.resample('ME').sum()

    fig_linha = px.line(
        gastos_mensais,
        x=gastos_mensais.index,
        y='Valor_Num',
        title='Total Gasto por Mês',
        markers=True,
        labels={'Valor_Num': 'Valor Total Gasto (R$)', 'Data_Obj': 'Mês'}
    )
    fig_linha.update_layout(xaxis_title='Mês', yaxis_title='Valor Gasto (R$)')
    st.plotly_chart(fig_linha, use_container_width=True)


# --- INÍCIO DO RODAPÉ ---
st.markdown("---")
st.caption("Fonte dos dados: [Portal da Transparência de Jacobina](https://www.acessoinformacao.com.br/ba/jacobina/despesas) - Os dados foram coletados e consolidados para esta visualização.")
st.caption("Última atualização do portal: 31/12/2024 16:01:27 (há 6 meses) ")
# --- FIM DO RODAPÉ ---