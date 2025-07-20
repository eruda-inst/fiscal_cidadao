import streamlit as st
import pandas as pd
import os
from agente_ia import AgenteDeDados

# --- Configuração da Página ---
st.set_page_config(
    page_title="Oráculo dos Gastos",
    page_icon="🔮",
    layout="wide"
)

st.title("🔮 Oráculo dos Gastos Públicos")
st.markdown("Faça uma pergunta em linguagem natural sobre os gastos públicos de Jacobina.")

@st.cache_data
def carregar_dados():
    caminho_arquivo = 'dados/despesas_completo.csv'
    if not os.path.exists(caminho_arquivo):
        return None
    
    df = pd.read_csv(caminho_arquivo, sep=';', encoding='utf-8-sig')
    df['Valor_Num'] = pd.to_numeric(df['Valor'].astype(str).str.replace(r'[R$\s.]', '', regex=True).str.replace(',', '.', regex=True), errors='coerce')
    df['Data_Obj'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
    df.dropna(subset=['Valor_Num', 'Data_Obj'], inplace=True)
    return df

df = carregar_dados()

if 'resposta_oraculo' not in st.session_state:
    st.session_state.resposta_oraculo = ""
if 'pergunta_oraculo' not in st.session_state:
    st.session_state.pergunta_oraculo = ""

if df is None:
    st.error("Arquivo de dados 'despesas_completo.csv' não foi encontrado.")
else:
    pergunta_usuario = st.text_area("Sua pergunta:", height=100, placeholder="Ex: Qual foi o gasto total com a saúde em 2024?")
    col1, col2 = st.columns([4, 1])
    with col1:
        if st.button("Perguntar ao Oráculo", use_container_width=True):
            if not pergunta_usuario:
                st.warning("Por favor, digite uma pergunta.")
            else:
                with st.spinner("O Oráculo está consultando os registros... Por favor, aguarde."):
                    try:
                        agente = AgenteDeDados()
                        resposta = agente.perguntar(pergunta_usuario, df)

                        st.subheader("Resposta do Oráculo:")
                        st.markdown(resposta)
                    
                    except Exception as e:
                        st.error(f"Não foi possível inicializar o Oráculo. Verifique o console ou o arquivo .env. Erro: {e}")
    
    with col2:
        if st.button("Limpar", use_container_width=True):
            st.session_state.pergunta_oraculo = ""
            st.session_state.resposta_oraculo = ""
    
    if st.session_state.resposta_oraculo:
        st.subheader("Resposta do Oráculo:")
        st.markdown(st.session_state.resposta_oraculo)
