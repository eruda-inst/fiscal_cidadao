# juntar_csv.py
import pandas as pd
import os
import re

# --- CONFIGURAÇÕES ---
# Pasta onde o scraper incremental salva os novos CSVs
DOWNLOAD_DIR_TEMP = os.path.abspath('dados/csv_novos')
# O arquivo principal e final com todos os dados
PARQUET_FILE = os.path.abspath('dados/despesas_completo.parquet')
# Nomes das colunas para os novos dados
NOMES_COLUNAS = [
    'Coluna Vazia 1', 'Data', 'Descricao', 'Valor', 'Credor', 'CNPJ/CPF', 'Orgao', 
    'Unidade Orcamentaria', 'Fonte Recurso', 'Funcao', 'Num Licitacao', 'Elemento Despesa', 
    'Fase', 'Num Empenho', 'Coluna Vazia 2', 'Coluna Vazia 3', 'Coluna Vazia 4', 'Coluna Vazia 5', 
    'Coluna Vazia 6', 'Coluna Vazia 7', 'Coluna Vazia 8'
]

def limpar_arquivos_temporarios():
    """Apaga os arquivos da pasta temporária após a unificação."""
    print(f"Limpando a pasta temporária '{DOWNLOAD_DIR_TEMP}'...")
    try:
        for f in os.listdir(DOWNLOAD_DIR_TEMP):
            os.remove(os.path.join(DOWNLOAD_DIR_TEMP, f))
        print("Limpeza concluída.")
    except Exception as e:
        print(f"Erro ao limpar a pasta temporária: {e}")

# --- LÓGICA PRINCIPAL DA UNIFICAÇÃO ---
if __name__ == "__main__":
    print("Iniciando o processo de unificação incremental...")

    # 1. Ler os novos arquivos CSV da pasta temporária
    try:
        arquivos_novos = [f for f in os.listdir(DOWNLOAD_DIR_TEMP) if f.endswith('.csv')]
        if not arquivos_novos:
            print("Nenhum arquivo novo encontrado na pasta temporária. Nenhum trabalho a fazer.")
            exit(0)
    except FileNotFoundError:
        print(f"Pasta temporária '{DOWNLOAD_DIR_TEMP}' não encontrada. Nenhum trabalho a fazer.")
        exit(0)

    print(f"Encontrados {len(arquivos_novos)} novos arquivos CSV para processar.")
    lista_dfs_novos = [pd.read_csv(os.path.join(DOWNLOAD_DIR_TEMP, f), encoding='utf-8', sep=',', header=None, low_memory=False) for f in arquivos_novos]
    df_novos = pd.concat(lista_dfs_novos, ignore_index=True)

    # 2. Limpar e estruturar os dados novos
    df_novos.columns = [f'col_{i}' for i in range(len(df_novos.columns))]
    df_novos = df_novos[df_novos['col_1'].astype(str).str.contains('/', na=False)].copy()
    df_novos.columns = NOMES_COLUNAS[:len(df_novos.columns)]
    print(f"{len(df_novos)} novos registros de dados foram lidos e limpos.")

    # 3. Carregar os dados antigos (se existirem)
    if os.path.exists(PARQUET_FILE):
        print(f"Carregando dados antigos de '{PARQUET_FILE}'...")
        df_antigo = pd.read_parquet(PARQUET_FILE)
        print(f"{len(df_antigo)} registros antigos carregados.")
        
        # Junta o antigo com o novo
        df_final = pd.concat([df_novos, df_antigo], ignore_index=True)
    else:
        print("Arquivo Parquet principal não encontrado. Este será o primeiro carregamento.")
        df_final = df_novos

    # 4. Remover duplicatas para garantir a integridade dos dados
    print("Removendo possíveis duplicatas...")
    # Uma chave de identificação forte para uma despesa
    chave_duplicata = ['Num Empenho', 'Data', 'Valor', 'Fase', 'Descricao'] 
    registros_antes = len(df_final)
    df_final.drop_duplicates(subset=chave_duplicata, keep='first', inplace=True)
    registros_depois = len(df_final)
    print(f"{registros_antes - registros_depois} duplicatas foram removidas.")

    # 5. Forçar tipos de dados para evitar erros ao salvar
    print("Garantindo os tipos de dados corretos antes de salvar...")
    for col in df_final.columns:
        if df_final[col].dtype == 'object':
            df_final[col] = df_final[col].astype(str)

    # 6. Salvar o resultado final
    try:
        df_final.to_parquet(PARQUET_FILE, index=False)
        print(f"\n✅ Sucesso! Arquivo '{PARQUET_FILE}' foi atualizado com sucesso.")
        print(f"Total de registros no arquivo final: {len(df_final)}")
        
        # 7. Limpar os arquivos temporários
        limpar_arquivos_temporarios()
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO ao salvar o arquivo Parquet final: {e}")
        print("Os arquivos temporários não foram apagados para permitir a depuração.")
        exit(1)