import pandas as pd
import os
import re

caminho_da_pasta = 'dados/csv_parciais/'
print("Listando e ordenando os arquivos...")
try:
    todos_os_arquivos = [f for f in os.listdir(caminho_da_pasta) if f.endswith('.csv')]
    if not todos_os_arquivos:
        raise FileNotFoundError
    
    def extrair_numero(nome_arquivo):
        match = re.search(r'pagina_(\d+).csv', nome_arquivo)
        return int(match.group(1)) if match else 0

    todos_os_arquivos.sort(key=extrair_numero)
    print(f"{len(todos_os_arquivos)} arquivos prontos para serem processados.")

except FileNotFoundError:
    print(f"Erro: A pasta '{caminho_da_pasta}' não foi encontrada ou está vazia.")
    todos_os_arquivos = []

if todos_os_arquivos:
    print("\nIniciando a junção dos arquivos CSV...")
    lista_de_dataframes = [pd.read_csv(os.path.join(caminho_da_pasta, f), encoding='utf-8', sep=',', header=None, low_memory=False) for f in todos_os_arquivos]
    
    df_completo = pd.concat(lista_de_dataframes, ignore_index=True)

    df_completo.columns = [f'col_{i}' for i in range(len(df_completo.columns))]
    coluna_data_str = df_completo['col_1'].astype(str)
    df_limpo = df_completo[coluna_data_str.str.contains('/', na=False)].copy()
    print(f"\nLimpeza realizada: {len(df_completo) - len(df_limpo)} linhas inválidas foram removidas.")

    if df_limpo.empty:
        print("ERRO CRÍTICO: Nenhum dado válido restou após a limpeza.")
    else:
        NOMES_COLUNAS = [
            'Coluna Vazia 1', 'Data', 'Descricao', 'Valor', 'Credor', 'CNPJ/CPF', 
            'Orgao', 'Unidade Orcamentaria', 'Fonte Recurso', 'Funcao', 
            'Num Licitacao', 'Elemento Despesa', 'Fase', 'Num Empenho', 
            'Coluna Vazia 2', 'Coluna Vazia 3', 'Coluna Vazia 4', 'Coluna Vazia 5', 
            'Coluna Vazia 6', 'Coluna Vazia 7', 'Coluna Vazia 8'
        ]
        df_limpo.columns = NOMES_COLUNAS[:len(df_limpo.columns)]

        # --- INÍCIO DA CORREÇÃO DEFINITIVA ---
        # Itera sobre todas as colunas do DataFrame.
        # Se uma coluna for do tipo 'object' (misto/texto), ela é convertida para string.
        print("Forçando a conversão de todas as colunas de texto para string...")
        for col in df_limpo.columns:
            if df_limpo[col].dtype == 'object':
                df_limpo[col] = df_limpo[col].astype(str)
        # --- FIM DA CORREÇÃO DEFINITIVA ---

        caminho_final_parquet = 'dados/despesas_completo.parquet'
        df_limpo.to_parquet(caminho_final_parquet, index=False)

        print(f"\n✅ Sucesso! Os dados foram juntados e salvos em formato Parquet.")
        print(f"O arquivo final foi salvo em: '{caminho_final_parquet}'")
        print(f"Total de linhas no arquivo final: {len(df_limpo)}")
else:
    print("Nenhum arquivo CSV encontrado ou processado na pasta.")