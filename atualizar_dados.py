# atualizar_dados.py (Versão com Verificação de Data)

import os
import sys
import subprocess
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURAÇÕES ---
URL_PORTAL = "https://www.acessoinformacao.com.br/ba/jacobina/despesas"
ARQUIVO_LOCAL_DATA = "ultima_atualizacao.txt"
# XPath para encontrar a div. Se houver muitas divs com essa classe, pode precisar de um ajuste.
XPATH_DIV_DATA = "//div[@id='updated_at']//div[@class='panel-body']"
def ler_data_local():
    """Lê a data/hora da última atualização bem-sucedida do arquivo local."""
    try:
        with open(ARQUIVO_LOCAL_DATA, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def obter_data_online():
    """Usa Selenium para extrair a data/hora de atualização do portal."""
    print("Acessando o portal para obter a data de última atualização...")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    service = Service(ChromeDriverManager().install())
    
    try:
        with webdriver.Chrome(service=service, options=options) as driver:
            wait = WebDriverWait(driver, 60)
            driver.get(URL_PORTAL)
            
            # 1. Espera a tabela principal carregar (garante que a página está estável)
            print("Aguardando a tabela de dados principal carregar...")
            wait.until(EC.presence_of_element_located((By.ID, "dataTableBuilder")))
            print("Tabela principal carregada. Procurando pela data de atualização...")

            # 2. Agora espera pelo texto na div da data usando o nosso novo XPath super confiável
            locator = (By.XPATH, XPATH_DIV_DATA)
            wait.until(EC.text_to_be_present_in_element(locator, '/'))
            
            elemento_data = driver.find_element(By.XPATH, XPATH_DIV_DATA)
            texto_completo = elemento_data.text.strip()
            
            partes = texto_completo.split()
            if len(partes) >= 2:
                data_hora_online = f"{partes[0]} {partes[1]}"
                print(f"Data encontrada no portal: {data_hora_online}")
                return data_hora_online
            else:
                print(f"ERRO: Formato de texto inesperado na div: '{texto_completo}'")
                return None

    except Exception as e:
        print(f"ERRO CRÍTICO ao tentar obter a data do portal: {e}")
        return None

def salvar_data_local(data_str):
    """Salva a nova data de atualização no arquivo local."""
    with open(ARQUIVO_LOCAL_DATA, 'w') as f:
        f.write(data_str)
    print(f"Arquivo '{ARQUIVO_LOCAL_DATA}' atualizado com a nova data.")

def executar_atualizacao_completa():
    """Orquestra a execução dos scripts de scraping e unificação."""
    print("\n--- Iniciando o SCRAPER (pode demorar)... ---")
    processo_scraper = subprocess.run([sys.executable, 'scraper.py'], capture_output=True, text=True, encoding='utf-8')
    if processo_scraper.returncode != 0:
        print("--- ERRO NO SCRAPER! ---")
        print(processo_scraper.stderr)
        return False
    print("--- Scraper concluído com sucesso! ---")
    
    print("\n--- Iniciando a UNIFICAÇÃO dos dados... ---")
    processo_unificador = subprocess.run([sys.executable, 'juntar_csv.py'], capture_output=True, text=True, encoding='utf-8')
    if processo_unificador.returncode != 0:
        print("--- ERRO NA UNIFICAÇÃO! ---")
        print(processo_unificador.stderr)
        return False
    print("--- Unificação concluída com sucesso! ---")
    
    return True

# --- FLUXO PRINCIPAL DA ATUALIZAÇÃO ---
if __name__ == "__main__":
    print(f"INICIANDO ROTINA DE VERIFICAÇÃO - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    data_local = ler_data_local()
    data_online = obter_data_online()
    
    if data_online is None:
        print("\n❌ FALHA NA VERIFICAÇÃO. Não foi possível obter a data do portal. O processo foi abortado.")
        sys.exit(1)
        
    print(f"\n--- Comparando Datas ---")
    print(f"Última data registrada localmente: {data_local}")
    print(f"Última data encontrada no portal:  {data_online}")

    if data_local == data_online:
        print("\n✅ Nenhuma alteração encontrada. Os dados já estão atualizados.")
        sys.exit(0)
    else:
        print("\n⚠️ DETECTADA NOVA ATUALIZAÇÃO NO PORTAL! Iniciando o processo de atualização completa...")
        
        sucesso = executar_atualizacao_completa()
        
        if sucesso:
            salvar_data_local(data_online)
            print("\n✅ PROCESSO DE ATUALIZAÇÃO CONCLUÍDO COM SUCESSO!")
        else:
            print("\n❌ FALHA DURANTE A ATUALIZAÇÃO. A data local não foi alterada para forçar uma nova tentativa na próxima execução.")
            sys.exit(1)