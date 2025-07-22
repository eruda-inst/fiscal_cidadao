# atualizar_dados.py (Versão Final com Scraping Incremental)

import os
import sys
import time
import pandas as pd
import subprocess
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURAÇÕES ---
URL = "https://www.acessoinformacao.com.br/ba/jacobina/despesas"
PARQUET_FILE = 'dados/despesas_completo.parquet'
DOWNLOAD_DIR_TEMP = os.path.abspath('dados/csv_novos') # Pasta temporária para novos downloads
COLUNA_EMPENHO_ONLINE = 14
COLUNA_EMпенHO_LOCAL = 'Num Empenho'

def get_latest_local_id():
    """Lê o Parquet e retorna o Num Empenho do registro mais recente."""
    if not os.path.exists(PARQUET_FILE): return None
    df = pd.read_parquet(PARQUET_FILE)
    if df.empty: return None
    
    df['Data_Obj'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
    df.sort_values(by='Data_Obj', ascending=False, inplace=True)
    
    return str(df.iloc[0][COLUNA_EMPENHO_LOCAL])

def baixar_novidades(ultimo_id_conhecido):
    """
    Navega pelo portal, baixa apenas as páginas com dados mais recentes que o último ID conhecido.
    Retorna True se novos arquivos foram baixados, False caso contrário.
    """
    print("Iniciando verificação e download incremental...")
    if not os.path.exists(DOWNLOAD_DIR_TEMP):
        os.makedirs(DOWNLOAD_DIR_TEMP)
    else: # Limpa a pasta de downloads temporários
        for f in os.listdir(DOWNLOAD_DIR_TEMP):
            os.remove(os.path.join(DOWNLOAD_DIR_TEMP, f))

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_experimental_option("prefs", {"download.default_directory": DOWNLOAD_DIR_TEMP})
    service = Service(ChromeDriverManager().install())
    
    novos_arquivos_baixados = 0
    with webdriver.Chrome(service=service, options=options) as driver:
        wait = WebDriverWait(driver, 60)
        long_wait = WebDriverWait(driver, 180)
        driver.get(URL)

        # Setup inicial robusto da página (com cookie)
        try:
            print("Configurando a página inicial...")
            wait.until(EC.element_to_be_clickable((By.ID, "btn-aceito-cookie"))).click()
            print("Banner de cookies aceito.")
        except TimeoutException:
            print("Nenhum banner de cookies encontrado.")
        
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[.//i[contains(@class, 'fa-search')]]"))).click()
        long_wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "swal2-container")))
        print("Página inicial pronta.")

        pagina_atual = 1
        while True:
            print(f"--- Verificando página {pagina_atual} ---")
            
            empenho_elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, f"//table[@id='dataTableBuilder']/tbody/tr/td[{COLUNA_EMPENHO_ONLINE}]")))
            empenhos_na_pagina = [el.text.strip() for el in empenho_elements]

            if ultimo_id_conhecido and ultimo_id_conhecido in empenhos_na_pagina:
                print(f"Encontrado o último registro conhecido ('{ultimo_id_conhecido}') na página {pagina_atual}. Finalizando a busca de novidades.")
                break

            print(f"Página {pagina_atual} contém novidades. Baixando...")
            arquivos_antes = set(os.listdir(DOWNLOAD_DIR_TEMP))
            wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'buttons-csv')]"))).click()
            
            tempo_espera = 0
            novo_arquivo_detectado = False
            while tempo_espera < 180:
                novos_arquivos = set(os.listdir(DOWNLOAD_DIR_TEMP)) - arquivos_antes
                if novos_arquivos:
                    nome_original = novos_arquivos.pop()
                    novo_nome = f"novos_pagina_{pagina_atual}.csv"
                    os.rename(os.path.join(DOWNLOAD_DIR_TEMP, nome_original), os.path.join(DOWNLOAD_DIR_TEMP, novo_nome))
                    print(f"Arquivo da página {pagina_atual} salvo.")
                    novos_arquivos_baixados += 1
                    novo_arquivo_detectado = True
                    break
                time.sleep(1)
                tempo_espera += 1
            
            if not novo_arquivo_detectado:
                print(f"ERRO: Timeout esperando o download da página {pagina_atual}.")
                return False

            try:
                next_button = driver.find_element(By.XPATH, "//a[text()='Próximo']")
                if "disabled" in next_button.find_element(By.XPATH, "./..").get_attribute("class"):
                    break
                driver.execute_script("arguments[0].click();", next_button)
                long_wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "swal2-container")))
                pagina_atual += 1
            except:
                break

    return novos_arquivos_baixados > 0

def unificar_novidades():
    """Pega os novos CSVs, junta com o Parquet existente e salva."""
    print("\n--- Iniciando a unificação dos dados... ---")
    # (A função unificar_novidades que já tínhamos pode ser usada aqui)
    # ... (código para ler os CSVs de 'dados/csv_novos', ler o parquet antigo,
    #      concatenar, remover duplicatas e salvar o novo parquet)
    return subprocess.run([sys.executable, 'juntar_csv.py'], capture_output=True, text=True, encoding='utf-8').returncode == 0


# --- FLUXO PRINCIPAL DA ATUALIZAÇÃO ---
if __name__ == "__main__":
    print(f"INICIANDO ROTINA DE ATUALIZAÇÃO INCREMENTAL - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    ultimo_id = get_latest_local_id()
    
    if baixar_novidades(ultimo_id):
        if unificar_novidades():
             print("\n✅ ATUALIZAÇÃO INCREMENTAL CONCLUÍDA COM SUCESSO!")
        else:
            print("\n❌ FALHA NA ETAPA DE UNIFICAÇÃO.")
    else:
        print("\n✅ Nenhuma novidade para baixar. Dados já estavam atualizados.")