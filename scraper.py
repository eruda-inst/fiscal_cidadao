# scraper.py - Versão FINAL (Focada nos Botões, lógica do usuário)

import os
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURAÇÕES ---
URL = "https://www.acessoinformacao.com.br/ba/jacobina/despesas"
DOWNLOAD_DIR = os.path.abspath('dados/csv_parciais')

def encontrar_ponto_de_partida():
    if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR); return 1
    arquivos = os.listdir(DOWNLOAD_DIR)
    if not arquivos: return 1
    numeros_paginas = [int(match.group(1)) for f in arquivos if (match := re.search(r'pagina_(\d+).csv', f))]
    return max(numeros_paginas) + 1 if numeros_paginas else 1

# --- INÍCIO DO SCRIPT ---
ponto_de_partida = encontrar_ponto_de_partida()

print("Iniciando o robô de download (versão final focada nos botões)...")
if ponto_de_partida > 1:
    print(f"Execução anterior encontrada. Continuando a partir da página {ponto_de_partida}.")
else:
    if os.path.exists(DOWNLOAD_DIR) and os.listdir(DOWNLOAD_DIR):
        print("Limpando a pasta de downloads parciais para uma nova execução...")
        for f in os.listdir(DOWNLOAD_DIR): os.remove(os.path.join(DOWNLOAD_DIR, f))

# Configurações do Chrome ...
options = webdriver.ChromeOptions()
options.add_experimental_option("prefs", {"download.default_directory": DOWNLOAD_DIR,"download.prompt_for_download": False,"download.directory_upgrade": True,"safeBrowse.enabled": True})
options.add_argument("--headless=new")
options.add_argument("--window-size=1920,1080")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

try:
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    print("Navegador Chrome iniciado em segundo plano.")
    driver.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
    params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': DOWNLOAD_DIR}}
    driver.execute("send_command", params)
except Exception as e:
    print(f"Erro ao iniciar o Chrome: {e}"); exit()

driver.get(URL)
wait = WebDriverWait(driver, 45) 
long_wait = WebDriverWait(driver, 180)
try:
    try:
        wait.until(EC.element_to_be_clickable((By.ID, "btn-aceito-cookie"))).click()
        print("Banner de cookies aceito.")
    except:
        print("Nenhum banner de cookies encontrado.")
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[.//i[contains(@class, 'fa-search')]]"))).click()
    print("Busca geral realizada. Aguardando carregamento...")
    long_wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "swal2-container")))
    print("Página inicial pronta!")
except Exception as e:
    print(f"\nERRO CRÍTICO na busca inicial: {e}"); driver.quit(); exit()

# --- LÓGICA DE AVANÇO RÁPIDO ---
if ponto_de_partida > 1:
    print(f"Avançando rapidamente para a página {ponto_de_partida}...")
    pagina_atual_ff = 1
    while pagina_atual_ff < ponto_de_partida:
        print(f"Avançando... {pagina_atual_ff}/{ponto_de_partida - 1}", end="\r")
        try:
            # A espera pelo botão 'Próximo' já garante que a página anterior carregou
            next_page_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[text()='Próximo']")))
            driver.execute_script("arguments[0].click();", next_page_button)
            pagina_atual_ff += 1
        except (StaleElementReferenceException, TimeoutException):
            # Se der erro, apenas tenta de novo no próximo loop
            print(f" (Página instável, tentando novamente...)")
            time.sleep(1)
            continue
    print(f"\nAvanço rápido concluído. Na página {ponto_de_partida}.")

# --- LOOP DE DOWNLOAD PRINCIPAL ---
pagina_atual = ponto_de_partida
while True:
    try:
        print(f"--- Página {pagina_atual} ---")
        
        # A espera pelo botão CSV aqui serve como a espera principal da página
        export_csv_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(@class, 'buttons-csv')]")
        ))
        
        # Lógica de Download
        arquivos_antes = set(os.listdir(DOWNLOAD_DIR))
        driver.execute_script("arguments[0].click();", export_csv_button)
        print(f"Download da página {pagina_atual} solicitado...")
        
        tempo_espera = 0; novo_arquivo_path = None
        while tempo_espera < 60:
            novos_arquivos = set(os.listdir(DOWNLOAD_DIR)) - arquivos_antes
            arquivos_csv_novos = [f for f in novos_arquivos if f.endswith('.csv')]
            if arquivos_csv_novos:
                nome_arquivo_baixado = arquivos_csv_novos[0]
                novo_arquivo_path = os.path.join(DOWNLOAD_DIR, nome_arquivo_baixado)
                print(f"Novo arquivo detectado: '{nome_arquivo_baixado}'")
                break
            time.sleep(1); tempo_espera += 1
        if not novo_arquivo_path: raise Exception("Timeout de 60s esperando novo arquivo .csv.")
        
        # Renomeação
        novo_nome = f"pagina_{pagina_atual}.csv"
        time.sleep(1); os.rename(novo_arquivo_path, os.path.join(DOWNLOAD_DIR, novo_nome))
        print(f"Arquivo renomeado para '{novo_nome}'.")

        # Lógica para ir para a próxima página
        next_page_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[text()='Próximo']")))
        parent_li = next_page_button.find_element(By.XPATH, "./..")
        if "disabled" in parent_li.get_attribute("class"):
            print("\nBotão 'Próximo' está desabilitado. Chegamos na última página."); break
        
        driver.execute_script("arguments[0].click();", next_page_button)
        print("Indo para a próxima página...")
        pagina_atual += 1
        
    except Exception as e:
        print(f"\nLoop encerrado na página {pagina_atual}. Tentando recarregar e continuar. Motivo: {e}")
        # Se ocorrer qualquer erro, recarrega a página e tenta continuar do mesmo ponto
        driver.refresh()
        time.sleep(5)
        continue

print("\nDownload de todas as páginas concluído!")
driver.quit()
print("Robô finalizado.")