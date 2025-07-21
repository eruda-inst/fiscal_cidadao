# scraper.py (Versão Final Corrigida)
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
TOTAL_PAGINAS = 10968

def encontrar_ponto_de_partida():
    if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR); return 1
    arquivos = os.listdir(DOWNLOAD_DIR)
    if not arquivos: return 1
    numeros_paginas = [int(match.group(1)) for f in arquivos if (match := re.search(r'pagina_(\d+).csv', f))]
    return max(numeros_paginas) + 1 if numeros_paginas else 1

def ir_para_ultima_pagina(driver, wait):
    print("Navegando para a última página...")
    try:
        last_page_button = wait.until(EC.element_to_be_clickable((By.XPATH, f"//a[text()='{TOTAL_PAGINAS}']")))
        driver.execute_script("arguments[0].click();", last_page_button)
        long_wait = WebDriverWait(driver, 180)
        long_wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "swal2-container")))
        print(f"Sucesso! Chegamos na página final: {TOTAL_PAGINAS}.")
        return TOTAL_PAGINAS
    except Exception as e:
        print(f"\nERRO CRÍTICO ao tentar ir para a última página: {e}")
        driver.quit()
        exit()

# --- INÍCIO DO SCRIPT ---
ponto_de_partida = encontrar_ponto_de_partida()

print("Verificando o modo de execução...")
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)
arquivos_existentes = len([f for f in os.listdir(DOWNLOAD_DIR) if f.endswith('.csv')])
MODO_REVERSO = arquivos_existentes > (TOTAL_PAGINAS / 2)

if not MODO_REVERSO:
    print(f"Modo Padrão (sequencial) ativado. {arquivos_existentes} de {TOTAL_PAGINAS} páginas baixadas.")
    if ponto_de_partida > 1:
        print(f"Execução anterior encontrada. Continuando a partir da página {ponto_de_partida}.")
else:
    print(f"Modo Reverso ativado! {arquivos_existentes} de {TOTAL_PAGINAS} páginas já baixadas.")

# Configurações do Chrome ...
options = webdriver.ChromeOptions()
options.add_experimental_option("prefs", {"download.default_directory": DOWNLOAD_DIR,"download.prompt_for_download": False,"download.directory_upgrade": True,"safeBrowse.enabled": True})
#options.add_argument("--headless=new")
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


if MODO_REVERSO:
    pagina_atual = ir_para_ultima_pagina(driver, wait)
    
    while True:
        try:
            print(f"--- Página {pagina_atual} (Reverso) ---")
            nome_arquivo_esperado = f"pagina_{pagina_atual}.csv"

            if os.path.exists(os.path.join(DOWNLOAD_DIR, nome_arquivo_esperado)):
                print(f"Arquivo '{nome_arquivo_esperado}' já existe. Pulando.")
            else:
                export_csv_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'buttons-csv')]")))
                arquivos_antes = set(os.listdir(DOWNLOAD_DIR))
                driver.execute_script("arguments[0].click();", export_csv_button)
                print(f"Download da página {pagina_atual} solicitado...")
                
                tempo_espera = 0
                novo_arquivo_path = None
                
                # <<< AJUSTE 1: LÓGICA DE ESPERA DO ARQUIVO COMPLETA >>>
                while tempo_espera < 60:
                    novos_arquivos = set(os.listdir(DOWNLOAD_DIR)) - arquivos_antes
                    if (arquivos_csv_novos := [f for f in novos_arquivos if f.endswith('.csv')]):
                        novo_arquivo_path = os.path.join(DOWNLOAD_DIR, arquivos_csv_novos[0])
                        print(f"Novo arquivo detectado: '{arquivos_csv_novos[0]}'")
                        break
                    time.sleep(1); tempo_espera += 1

                if not novo_arquivo_path: raise Exception("Timeout de 60s esperando novo arquivo .csv.")
                
                time.sleep(1); os.rename(novo_arquivo_path, os.path.join(DOWNLOAD_DIR, nome_arquivo_esperado))
                print(f"Arquivo renomeado para '{nome_arquivo_esperado}'.")

            prev_page_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[text()='Anterior']")))
            parent_li = prev_page_button.find_element(By.XPATH, "./..")
            if "disabled" in parent_li.get_attribute("class"):
                print("\nBotão 'Anterior' está desabilitado. Chegamos na primeira página."); break
            
            driver.execute_script("arguments[0].click();", prev_page_button)
            print("Indo para a página anterior...")

            # <<< INÍCIO DA ESPERA INTELIGENTE >>>
            try:
                # Espera o overlay de carregamento aparecer e depois desaparecer
                wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "swal2-container")))
                long_wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "swal2-container")))
                print(" -> Página anterior carregada.")
            except TimeoutException:
                # Se o overlay não aparecer, a página pode ter carregado rápido demais.
                print(" -> Carregamento rápido ou sem overlay. Continuando...")
                time.sleep(1) # Pequena pausa de segurança
            # <<< FIM DA ESPERA INTELIGENTE >>>

            pagina_atual -= 1

        except StaleElementReferenceException:
            print(f" (Elemento instável na página {pagina_atual}. Tentando novamente...)")
            time.sleep(2)
            continue
        except Exception as e:
            print(f"\nOcorreu um erro na página {pagina_atual}. Tentando novamente em 5 segundos. Motivo: {e}")
            time.sleep(5)
            continue
else:
    if ponto_de_partida > 1:
        print(f"Avançando rapidamente para a página {ponto_de_partida}...")
        pagina_atual_ff = 1
        while pagina_atual_ff < ponto_de_partida:
            print(f"Avançando... {pagina_atual_ff}/{ponto_de_partida - 1}", end="\r")
            try:
                next_page_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[text()='Próximo']")))
                driver.execute_script("arguments[0].click();", next_page_button)
                pagina_atual_ff += 1
            except (StaleElementReferenceException, TimeoutException):
                print(" (Página instável, tentando novamente...)")
                time.sleep(1); continue
        print(f"\nAvanço rápido concluído. Na página {ponto_de_partida}.")

    pagina_atual = ponto_de_partida
    while True:
        try:
            print(f"--- Página {pagina_atual} ---")
            export_csv_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'buttons-csv')]")))
            
            arquivos_antes = set(os.listdir(DOWNLOAD_DIR))
            driver.execute_script("arguments[0].click();", export_csv_button)
            print(f"Download da página {pagina_atual} solicitado...")
            
            tempo_espera = 0
            novo_arquivo_path = None
            while tempo_espera < 60:
                novos_arquivos = set(os.listdir(DOWNLOAD_DIR)) - arquivos_antes
                if (arquivos_csv_novos := [f for f in novos_arquivos if f.endswith('.csv')]):
                    novo_arquivo_path = os.path.join(DOWNLOAD_DIR, arquivos_csv_novos[0])
                    print(f"Novo arquivo detectado: '{arquivos_csv_novos[0]}'")
                    break
                time.sleep(1); tempo_espera += 1
            if not novo_arquivo_path: raise Exception("Timeout de 60s esperando novo arquivo .csv.")
            
            novo_nome = f"pagina_{pagina_atual}.csv"
            time.sleep(1); os.rename(novo_arquivo_path, os.path.join(DOWNLOAD_DIR, novo_nome))
            print(f"Arquivo renomeado para '{novo_nome}'.")

            next_page_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[text()='Próximo']")))
            parent_li = next_page_button.find_element(By.XPATH, "./..")
            if "disabled" in parent_li.get_attribute("class"):
                print("\nBotão 'Próximo' está desabilitado. Chegamos na última página."); break
            
            driver.execute_script("arguments[0].click();", next_page_button)
            print("Indo para a próxima página...")

            # <<< INÍCIO DA ESPERA INTELIGENTE >>>
            try:
                # Espera o overlay de carregamento aparecer e depois desaparecer
                wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "swal2-container")))
                long_wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "swal2-container")))
                print(" -> Página seguinte carregada.")
            except TimeoutException:
                # Se o overlay não aparecer, a página pode ter carregado rápido demais.
                print(" -> Carregamento rápido ou sem overlay. Continuando...")
                time.sleep(1) # Pequena pausa de segurança
            # <<< FIM DA ESPERA INTELIGENTE >>>

            pagina_atual += 1
            
        except StaleElementReferenceException:
            print(f" (Elemento instável na página {pagina_atual}. Tentando novamente...)")
            time.sleep(2)
            continue
        except Exception as e:
            print(f"\nOcorreu um erro na página {pagina_atual}. Tentando novamente em 5 segundos. Motivo: {e}")
            time.sleep(5)
            continue

print("\nDownload de todas as páginas concluído!")
driver.quit()
print("Robô finalizado.")