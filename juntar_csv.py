import pandas as pd
import os

caminho_da_pasta = 'dados/csv_parciais/'

lista_de_dataframes = []

print("Iniciando a junção dos arquivos CSV...")

for nome_do_arquivo in os.listdir(caminho_da_pasta):
    if nome_do_arquivo.endswith('.csv'):
        caminho_completo = os.path.join(caminho_da_pasta, nome_do_arquivo)
        
        try:
            df_parcial = pd.read_csv(caminho_completo, encoding='latin-1')
            lista_de_dataframes.append(df_parcial)
            print(f"Arquivo '{nome_do_arquivo}' lido com sucesso.")
        except Exception as e:
            print(f"Erro ao ler o arquivo '{nome_do_arquivo}': {e}")

if lista_de_dataframes:
    df_completo = pd.concat(lista_de_dataframes, ignore_index=True)

    caminho_final = 'dados/despesas_2024_completo.csv'
    df_completo.to_csv(caminho_final, sep=';', index=False, encoding='utf-8')

    print(f"\nSucesso! {len(lista_de_dataframes)} arquivos foram juntados.")
    print(f"O arquivo final foi salvo em: '{caminho_final}'")
    print(f"Total de linhas no arquivo final: {len(df_completo)}")
else:
    print("Nenhum arquivo CSV encontrado na pasta para juntar.")