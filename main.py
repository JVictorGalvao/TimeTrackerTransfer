import os

from datetime import datetime, timedelta
import pprint
from time import sleep

import pandas as pd

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException

# Verify if the file already exists
if os.path.exists('arquivo.csv'):
    # Remove the file
    os.remove('arquivo.csv')

if os.path.exists('Meus Apontamentos de Horas.xls'):
    # Remove the file
    os.remove('Meus Apontamentos de Horas.xls')


# Date variables
current_year = datetime.now().year
# If the current month is january, the last month is december of the previous year
previous_year = current_year
current_month = datetime.now().month
current_day = datetime.now().day if datetime.now().day <= 25 else 25
previous_month = current_month - 1

if previous_month == 0:
    previous_month = 12
    previous_year -= 1

download_path = os.path.dirname(os.path.abspath(__file__))

# Browser options
options = Options()
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
options.add_argument("--start-maximized")
options.add_experimental_option("prefs", {
    # Setting download path to current directory
    "download.default_directory": download_path,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
})

# Check README to see wich version of chromedriver is compatible with your browser
driver = webdriver.Chrome(service=Service(ChromeDriverManager(
    driver_version=os.getenv("CHROMEDRIVE_VERSION")).install()), options=options)

# Access the Netproject website
driver.get("https://projetos.synchro.com.br")

while True:
    try:
        element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        print("Página carregada com sucesso")
    except:
        print("A página demorou muito para carregar: F5")
        driver.refresh()
        continue
    break

# Login
user_field = driver.find_element(by=By.ID, value="username")
password_field = driver.find_element(by=By.ID, value="password")

user_field.send_keys(os.getenv("NETPROJECT_USER"))
password_field.send_keys(os.getenv("NETPROJECT_PASSWORD"))
password_field.send_keys(Keys.RETURN)

# Access the time tracking report menu
menu = driver.find_element(by=By.CLASS_NAME, value="userbox")
menu.click()

menu_item = driver.find_element(by=By.ID, value="menu_549")
menu_item.click()

# Access the time tracking date filters
filter_button = driver.find_element(by=By.ID, value="fw_abre_filtro")
filter_button.click()

# Filter by the 26th of the previous month until the 25th of the current month
init_date = driver.find_element(by=By.ID, value="ini")
init_date.clear()
init_date.send_keys(f"26/{previous_month}/{previous_year}")

end_date = driver.find_element(by=By.ID, value="fim")
end_date.clear()
end_date.send_keys(f"{current_day}/{current_month}/{current_year}")

finish_filter_button = driver.find_element(
    by=By.XPATH, value="//button[contains(text(), 'Filtrar')]")
finish_filter_button.click()

# Download the CSV report file
csv_download_button = driver.find_element(by=By.ID, value="btn_csv")
csv_download_button.click()

sleep(2)  # Wait for the download to finish

# Access mikael
driver.get("https://mikael.synchro.com.br/mikael/indexLogin.jsp")

while True:
    try:
        element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "loginForm:codlogin"))
        )
        print("Página carregada com sucesso")
    except:
        print("A página demorou muito para carregar: F5")
        driver.refresh()
        continue
    break

# Login
user_field = driver.find_element(by=By.ID, value="loginForm:codlogin")
password_field = driver.find_element(by=By.ID, value="loginForm:password")

user_field.send_keys(os.getenv("SGI_USER"))
password_field.send_keys(os.getenv("SGI_PASSWORD"))
password_field.send_keys(Keys.RETURN)

xpath_melhorado = "//span[normalize-space()='Apontamentos']"
try:
    wait = WebDriverWait(driver, 10)
    menu = wait.until(
        EC.element_to_be_clickable((By.XPATH, xpath_melhorado))
    )
    menu.click()

except Exception as e:
    print(f"Erro mesmo com XPath melhorado: {e}")

xpath_melhorado = "//span[normalize-space()='Meus Apontamentos de Horas']"
try:
    wait = WebDriverWait(driver, 10)
    menu = wait.until(
        EC.element_to_be_clickable((By.XPATH, xpath_melhorado))
    )
    menu.click()
    print("Elemento 'Apontamentos' encontrado com normalize-space() e clicado.")

except Exception as e:
    print(f"Erro mesmo com XPath melhorado: {e}")

xpath_botao_pesquisar = "//img[contains(@src, 'exportar_excel.png')]"
tentativas = 3  # Número de vezes que vamos tentar antes de desistir

for i in range(tentativas):
    try:
        # 1. Espera o elemento estar clicável (isso sempre busca o elemento mais recente)
        wait = WebDriverWait(driver, 10)
        botao = wait.until(
            EC.element_to_be_clickable((By.XPATH, xpath_botao_pesquisar))
        )

        # 2. Tenta clicar
        botao.click()

        # 3. Se o clique foi bem-sucedido, imprime e sai do laço
        print(f"Botão de pesquisa clicado com sucesso na tentativa {i+1}.")
        break  # Sai do 'for' loop

    except StaleElementReferenceException:
        # Se o elemento ficou obsoleto, o laço continua para a próxima tentativa
        print(
            f"Elemento obsoleto detectado (tentativa {i+1}/{tentativas}). Tentando novamente...")
        # Uma pequena pausa pode ser útil em alguns casos, mas não é sempre necessária
        # time.sleep(0.5)

    except TimeoutException:
        # Se o elemento não for encontrado em 10 segundos, não adianta tentar de novo
        print("Erro: O elemento não foi encontrado no tempo de espera. (TimeoutException)")
        break

    except Exception as e:
        # Pega outros erros inesperados
        print(f"Ocorreu um erro inesperado: {e}")
        break

xpath_botao_pesquisar = "//img[contains(@src, 'excel.gif')]"
tentativas = 3  # Número de vezes que vamos tentar antes de desistir

for i in range(tentativas):
    try:
        # 1. Espera o elemento estar clicável (isso sempre busca o elemento mais recente)
        wait = WebDriverWait(driver, 10)
        botao = wait.until(
            EC.element_to_be_clickable((By.XPATH, xpath_botao_pesquisar))
        )

        # 2. Tenta clicar
        botao.click()

        # 3. Se o clique foi bem-sucedido, imprime e sai do laço
        print(f"Botão de pesquisa clicado com sucesso na tentativa {i+1}.")
        break  # Sai do 'for' loop

    except StaleElementReferenceException:
        # Se o elemento ficou obsoleto, o laço continua para a próxima tentativa
        print(
            f"Elemento obsoleto detectado (tentativa {i+1}/{tentativas}). Tentando novamente...")
        # Uma pequena pausa pode ser útil em alguns casos, mas não é sempre necessária
        # time.sleep(0.5)

    except TimeoutException:
        # Se o elemento não for encontrado em 10 segundos, não adianta tentar de novo
        print("Erro: O elemento não foi encontrado no tempo de espera. (TimeoutException)")
        break

    except Exception as e:
        # Pega outros erros inesperados
        print(f"Ocorreu um erro inesperado: {e}")
        break
sleep(2)


def processar_arquivo_csv(caminho_csv):
    """
    Lê e processa o arquivo de ponto (CSV), consolidando blocos de tempo.
    Retorna um dicionário com os dados processados.
    """
    print("--- Processando arquivo CSV... ---")
    try:
        # A sua lógica de limpeza prévia (pode ser melhorada, mas mantida por fidelidade)
        with open(caminho_csv, 'r', encoding='ISO-8859-1') as file:
            lines = file.readlines()
        lines = lines[:-2]
        with open(caminho_csv, 'w', encoding='ISO-8859-1') as file:
            file.writelines(lines)

        dataframe = pd.read_csv(caminho_csv, sep=';', encoding='iso-8859-1')
        day_list = dataframe['Dia'].unique()

        data = {}
        for day in day_list:
            day_key = datetime.strptime(day, '%d/%m/%Y').strftime('%d/%m/%y')
            subdataframe = dataframe[dataframe['Dia'] == day]

            if day_key not in data:
                data[day_key] = []

            previous_saida = None
            for _, row in subdataframe.iterrows():
                try:
                    entrada = datetime.strptime(row['Entrada'], '%H:%M')
                    saida = datetime.strptime(row['Saída'], '%H:%M')

                    if previous_saida and (entrada - previous_saida) <= timedelta(minutes=2):
                        data[day_key].pop()
                        data[day_key].append(saida.strftime('%Hh%M'))
                    else:
                        data[day_key].extend(
                            [entrada.strftime('%Hh%M'), saida.strftime('%Hh%M')])

                    previous_saida = saida
                except (ValueError, TypeError):
                    continue  # Pula linhas com formato de hora inválido

        print("Arquivo CSV processado com sucesso.")
        return data

    except FileNotFoundError:
        print(f"AVISO: Arquivo CSV '{caminho_csv}' não encontrado. Pulando...")
        return {}
    except Exception as e:
        print(f"ERRO ao processar o arquivo CSV: {e}")
        return {}

# ==============================================================================
# FUNÇÃO 2: PROCESSA O ARQUIVO XLS (Nossa nova lógica de Início/Interrupção)
# ==============================================================================


def processar_arquivo_xls(caminho_xls):
    """
    Lê o arquivo de apontamentos (XLS), filtra por período e extrai os blocos
    de trabalho baseados em início e interrupção.
    """
    data_inicio_filtro = pd.to_datetime(f"{previous_year}-{previous_month}-26")
    data_fim_filtro = pd.to_datetime(f"{current_year}-{current_month}-25")
    print("\n--- Processando arquivo XLS... ---")
    try:
        df = pd.read_excel(caminho_xls, skiprows=11)

        # Prepara as colunas
        nome_coluna_data = 'Data Inicial'
        nome_coluna_hora = 'Hora Inicial'
        nome_coluna_evento = 'Tarefa / Evento'

        df[nome_coluna_data] = pd.to_datetime(
            df[nome_coluna_data], errors='coerce')
        # Remove linhas com data inválida
        df.dropna(subset=[nome_coluna_data], inplace=True)

        print(
            f"Filtrando apontamentos de {data_inicio_filtro.date()} até {data_fim_filtro.date()}...")
        df_filtrado = df[(df[nome_coluna_data] >= data_inicio_filtro) & (
            df[nome_coluna_data] <= data_fim_filtro)].copy()

        if df_filtrado.empty:
            print("Nenhum registro encontrado no XLS para este intervalo de datas.")
            return {}

        # O restante do processamento agora usa o 'df_filtrado'
        df_filtrado[nome_coluna_hora] = pd.to_datetime(
            df_filtrado[nome_coluna_hora], format='%H:%M:%S', errors='coerce').dt.time
        df_processado = df_filtrado.dropna(
            subset=[nome_coluna_data, nome_coluna_hora]).copy()
        df_processado['Timestamp'] = df_processado.apply(lambda r: pd.Timestamp.combine(
            r[nome_coluna_data].date(), r[nome_coluna_hora]), axis=1)
        df_processado = df_processado.sort_values(
            'Timestamp').reset_index(drop=True)

        df_processado['is_end'] = df_processado[nome_coluna_evento].str.contains(
            "INTERRUPÇÃO DE TRABALHO", na=False)
        df_processado['is_start'] = ~df_processado['is_end']
        df_processado['block_id'] = df_processado['is_start'].cumsum()

        data = {}
        for _, group in df_processado.groupby('block_id'):
            if group.iloc[-1]['is_end']:
                inicio = group.iloc[0]['Timestamp']
                fim = group.iloc[-1]['Timestamp']
                day_key = inicio.strftime('%d/%m/%y')

                if day_key not in data:
                    data[day_key] = []

                data[day_key].extend(
                    [inicio.strftime('%Hh%M'), fim.strftime('%Hh%M')])

        print("Arquivo XLS processado com sucesso.")
        return data

    except FileNotFoundError:
        print(f"AVISO: Arquivo XLS '{caminho_xls}' não encontrado. Pulando...")
        return {}
    except Exception as e:
        print(f"ERRO ao processar o arquivo XLS: {e}")
        return {}


# Defina os caminhos para os seus arquivos
caminho_csv = 'arquivo.csv'
# Use o caminho local do seu arquivo
caminho_xls = 'Meus Apontamentos de Horas.xls'

# Processa cada arquivo separadamente
dados_csv = processar_arquivo_csv(caminho_csv)
dados_xls = processar_arquivo_xls(caminho_xls)

# Mescla os dois dicionários
data = dados_csv.copy()  # Começa com os dados do CSV

for dia, horarios in dados_xls.items():
    if dia in data:
        # Se o dia já existe, adiciona os novos horários e ordena
        data[dia].extend(horarios)
        data[dia].sort()
    else:
        # Se o dia não existe, simplesmente adiciona
        data[dia] = horarios

print("\n\n--- DADOS FINAIS MESCLADOS (CSV + XLS) ---")
pprint.pprint(data)

# Open SGI website
driver.get("https://sgiweb.synchro.com.br/login.html")

# Login
user_field = driver.find_element(by=By.NAME, value="prfNome")
password_field = driver.find_element(by=By.NAME, value="prfSenha")
user_field.send_keys(os.getenv("SGI_USER"))
password_field.send_keys(os.getenv("SGI_PASSWORD"))
password_field.send_keys(Keys.RETURN)

# Select period
period_select = Select(driver.find_element(by=By.NAME, value="perCodigo"))
period_select.select_by_value(
    f"{str(previous_year)[-2:]}{previous_month:02d}")

# Select "Manter marcações de jornada"
keep_schedule = driver.find_element(
    by=By.XPATH, value="//input[@value='HoraEntrada']")
keep_schedule.click()

# Click on "Executar"
execute_button = driver.find_element(by=By.NAME, value="go")
execute_button.click()

dates_already_visited = []

# Iterate through each date at the current project code
for date, hours in data.items():
    edit_day_button = driver.find_element(
        by=By.XPATH, value=f"//a[@href=\"javascript: submitform('{date}')\"]")
    edit_day_button.click()

    index = 0

    # For each hour in the current date
    while index < len(hours):

        # Get hour inputs
        inputs = driver.find_elements(by=By.NAME, value="hora")

        # If it's the first time visiting the date, clear all inputs
        if date not in dates_already_visited:
            for input in inputs:
                if input.get_attribute('value'):
                    input.clear()
                    # Set the default value at filled inputs to 00h00
                    input.send_keys('00h00')
            for input in inputs:
                input.clear()
                input.send_keys(hours[index])
                index += 1
                dates_already_visited.append(date)
                if index == len(hours):
                    break
        else:  # If it's not the first time visiting the date, fill only the empty inputs
            for input in inputs:
                if not input.get_attribute('value') or input.get_attribute('value') == '00h00':
                    input.clear()
                    input.send_keys(hours[index])
                    index += 1
                    if index == len(hours):
                        break

        if index == len(hours):  # If all hours were filled,
            break
        else:  # If there are still hours to fill, click on "Gravar" and refresh this date to open new inputs
            save_button = driver.find_element(
                by=By.XPATH, value="//input[@value='Gravar']")
            save_button.click()

            driver.back()
            driver.back()
            driver.refresh()

            edit_day_button = driver.find_element(
                by=By.XPATH, value=f"//a[@href=\"javascript: submitform('{date}')\"]")
            edit_day_button.click()

    # Save the last filled hours
    save_button = driver.find_element(
        by=By.XPATH, value="//input[@value='Gravar']")
    save_button.click()

    # Go back to the dates page
    driver.back()
    driver.back()
    driver.refresh()

# Go back to the main page
driver.back()
driver.refresh()

# Mark Logoff from SGI
logoff = driver.find_element(by=By.XPATH, value="//input[@value='X']")
logoff.click()

# Click on "Executar"
execute_button = driver.find_element(by=By.NAME, value="go")
execute_button.click()

driver.quit()
