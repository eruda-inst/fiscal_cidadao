import pandas as pd
import os
import re

caminho_da_pasta = 'dados/csv_parciais/'

print("Listando e ordenando os arquivos...")
try:
    todos_os_arquivos = [f for f in os.listdir(caminho_da_pasta) if f.endswith('.csv')]

    def extrair_numero(nome_arquivo):
        match = re.search(r'pagina_(\d+).csv', nome_arquivo)
        return int(match.group(1)) if match else 0
    
    todos_os_arquivos.sort(key=extrair_numero)
    print(f"{len(todos_os_arquivos)} arquivos prontos para serem processados.")

except FileNotFoundError:
    print(f"Erro: A pasta '{caminho_da_pasta}' não foi encontrada.")
    lista_de_dataframes = []

lista_de_dataframes = []

if todos_os_arquivos:
    print("\nIniciando a junção dos arquivos CSV...")

    # Loop for agora usa a lista ordenada
    for nome_do_arquivo in todos_os_arquivos:
        caminho_completo = os.path.join(caminho_da_pasta, nome_do_arquivo)
        
        try:
            df_parcial = pd.read_csv(
                caminho_completo, 
                encoding='utf-8', 
                sep=',',          
                header=None       
            )
            lista_de_dataframes.append(df_parcial)
            print(f"Arquivo '{nome_do_arquivo}' lido com sucesso.")
        except Exception as e:
            print(f"Erro ao ler o arquivo '{nome_do_arquivo}': {e}")

if lista_de_dataframes:
    df_completo = pd.concat(lista_de_dataframes, ignore_index=True)
    if df_completo.shape[1] > 1:
        coluna_de_verificacao = df_completo.iloc[:, 1].astype(str)
        df_completo_limpo = df_completo[coluna_de_verificacao != 'Data'].copy()
        print(f'\nLimpeza realizada: {len(df_completo) - len(df_completo_limpo)} linhas removidas.')

    else:
        df_completo_limpo = df_completo


    NOMES_COLUNAS = [
        'Coluna Vazia 1', 'Data', 'Descricao', 'Valor', 'Credor', 'CNPJ/CPF', 
        'Orgao', 'Unidade Orcamentaria', 'Fonte Recurso', 'Funcao', 
        'Num Licitacao', 'Elemento Despesa', 'Fase', 'Num Empenho', 
        'Coluna Vazia 2', 'Coluna Vazia 3', 'Coluna Vazia 4', 'Coluna Vazia 5', 
        'Coluna Vazia 6', 'Coluna Vazia 7', 'Coluna Vazia 8'
    ]
    if len(df_completo_limpo.columns) == len(NOMES_COLUNAS):
        df_completo_limpo.columns = NOMES_COLUNAS

    caminho_final = 'dados/despesas_completo.csv' 
    df_completo_limpo.to_csv(caminho_final, sep=';', index=False, encoding='utf-8-sig') 

    print(f"\nSucesso! {len(lista_de_dataframes)} arquivos foram juntados.")
    print(f"O arquivo final foi salvo em: '{caminho_final}'")
    print(f"Total de linhas no arquivo final: {len(df_completo_limpo)}")
else:
    print("Nenhum arquivo CSV encontrado ou processado na pasta.")