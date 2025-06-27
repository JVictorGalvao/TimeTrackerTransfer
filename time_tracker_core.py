# time_tracker_core.py

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
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, WebDriverException


def run_time_transfer(netproject_user, netproject_password, sgi_user, sgi_password, chromedriver_version, log_callback=None):
    """
    Função principal que executa a lógica do TimeTrackerTransfer.
    Recebe todos os parâmetros necessários diretamente da GUI.
    log_callback: função para atualizar a GUI com o progresso e mensagens.
    """

    def log(message):
        """Função auxiliar para enviar mensagens para o callback da GUI e para o console."""
        if log_callback:
            log_callback(message)
        print(message)

    log("Iniciando o processo TimeTrackerTransfer...")

    driver = None  # Inicializa o driver como None para garantir que seja fechado no finally

    try:
        # --- Limpeza de arquivos existentes ---
        log("Verificando e removendo arquivos de relatório antigos...")
        if os.path.exists('arquivo.csv'):
            os.remove('arquivo.csv')
            log("  arquivo.csv removido.")
        if os.path.exists('Meus Apontamentos de Horas.xls'):
            os.remove('Meus Apontamentos de Horas.xls')
            log("  Meus Apontamentos de Horas.xls removido.")

        # --- Variáveis de Data ---
        current_year = datetime.now().year
        previous_year = current_year
        current_month = datetime.now().month
        current_day = datetime.now().day if datetime.now().day <= 25 else 25
        previous_month = current_month - 1

        if previous_month == 0:
            previous_month = 12
            previous_year -= 1

        download_path = os.path.dirname(os.path.abspath(__file__))

        # --- Opções do Navegador ---
        log("Configurando o navegador Chrome...")
        options = Options()
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--start-maximized")
        options.add_experimental_option("prefs", {
            "download.default_directory": download_path,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safeBrowse.enabled": True
        })

        # --- Inicialização do WebDriver ---
        log(
            f"Baixando e inicializando ChromeDriver (versão: {chromedriver_version})...")
        try:
            # Garante que a versão do chromedriver é uma string
            driver = webdriver.Chrome(service=Service(ChromeDriverManager(
                driver_version=str(chromedriver_version)).install()), options=options)
        except Exception as e:
            log(
                f"ERRO: Não foi possível inicializar o ChromeDriver. Verifique a versão ({chromedriver_version}). Erro: {e}")
            raise  # Re-lança a exceção para ser capturada pelo bloco try/except principal

        # --- Acesso e Login no Netproject ---
        log("Acessando Netproject...")
        driver.get("https://projetos.synchro.com.br")

        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            log("Página do Netproject carregada.")
        except TimeoutException:
            log("ERRO: Página do Netproject demorou muito para carregar. Tentando novamente...")
            driver.refresh()
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            log("Página do Netproject recarregada.")

        log(f"Fazendo login no Netproject como: {netproject_user}")
        user_field = driver.find_element(by=By.ID, value="username")
        password_field = driver.find_element(by=By.ID, value="password")

        user_field.send_keys(netproject_user)
        password_field.send_keys(netproject_password)
        password_field.send_keys(Keys.RETURN)
        sleep(2)  # Pequena pausa para o login processar

        # --- Acessar menu de relatório de apontamento de horas ---
        log("Acessando relatório de apontamento de horas no Netproject...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "userbox"))).click()
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "menu_549"))).click()
        sleep(1)

        # --- Acessar filtros de data ---
        log("Aplicando filtros de data no Netproject...")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "fw_abre_filtro"))).click()

        init_date = driver.find_element(by=By.ID, value="ini")
        init_date.clear()
        # Adicionado :02d para formatar com 2 dígitos
        init_date.send_keys(f"26/{previous_month:02d}/{previous_year}")

        end_date = driver.find_element(by=By.ID, value="fim")
        end_date.clear()
        # Adicionado :02d para formatar com 2 dígitos
        end_date.send_keys(
            f"{current_day:02d}/{current_month:02d}/{current_year}")

        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(), 'Filtrar')]"))
        ).click()
        sleep(2)  # Espera o filtro ser aplicado

        # --- Download do relatório CSV ---
        log("Baixando relatório CSV do Netproject...")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "btn_csv"))).click()
        sleep(3)  # Espera o download terminar

        # --- Acesso e Login no Mikael (SGI) ---
        log("Acessando Mikael (SGI) para login...")
        driver.get("https://mikael.synchro.com.br/mikael/indexLogin.jsp")

        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "loginForm:codlogin"))
            )
            log("Página do Mikael carregada.")
        except TimeoutException:
            log("ERRO: Página do Mikael demorou muito para carregar. Tentando novamente...")
            driver.refresh()
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "loginForm:codlogin"))
            )
            log("Página do Mikael recarregada.")

        log(f"Fazendo login no Mikael (SGI) como: {sgi_user}")
        user_field = driver.find_element(by=By.ID, value="loginForm:codlogin")
        password_field = driver.find_element(
            by=By.ID, value="loginForm:password")

        user_field.send_keys(sgi_user)
        password_field.send_keys(sgi_password)
        password_field.send_keys(Keys.RETURN)
        sleep(2)  # Pequena pausa para o login processar

        # --- Navegação para Meus Apontamentos de Horas no Mikael ---
        log("Navegando para 'Meus Apontamentos de Horas' no Mikael...")
        try:
            wait = WebDriverWait(driver, 10)
            menu_apontamentos = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//span[normalize-space()='Apontamentos']"))
            )
            menu_apontamentos.click()
            log("  Clicado em 'Apontamentos'.")

            menu_meus_apontamentos = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//span[normalize-space()='Meus Apontamentos de Horas']"))
            )
            menu_meus_apontamentos.click()
            log("  Clicado em 'Meus Apontamentos de Horas'.")
            sleep(2)
        except Exception as e:
            log(f"ERRO ao navegar para apontamentos no Mikael: {e}")
            raise  # Re-lança para parar a execução

        # --- Exportar XLS do Mikael ---
        log("Exportando relatório XLS do Mikael...")
        xpath_botao_excel_1 = "//img[contains(@src, 'exportar_excel.png')]"
        # Algumas vezes a imagem muda
        xpath_botao_excel_2 = "//img[contains(@src, 'excel.gif')]"

        tentativas = 3
        botao_clicado = False
        for i in range(tentativas):
            try:
                wait = WebDriverWait(driver, 10)
                # Tenta o primeiro XPath
                botao = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, xpath_botao_excel_1)))
                botao.click()
                log(
                    f"Botão de exportar Excel (exportar_excel.png) clicado na tentativa {i+1}.")
                botao_clicado = True
                break
            except (StaleElementReferenceException, TimeoutException):
                log(
                    f"Primeiro botão de exportar XLS não encontrado ou obsoleto (tentativa {i+1}). Tentando segundo XPath...")
                try:  # Tenta o segundo XPath se o primeiro falhar
                    botao = wait.until(EC.element_to_be_clickable(
                        (By.XPATH, xpath_botao_excel_2)))
                    botao.click()
                    log(
                        f"Botão de exportar Excel (excel.gif) clicado na tentativa {i+1}.")
                    botao_clicado = True
                    break
                except (StaleElementReferenceException, TimeoutException):
                    log(
                        f"Segundo botão de exportar XLS também não encontrado ou obsoleto (tentativa {i+1}).")
            except Exception as e:
                log(
                    f"Ocorreu um erro inesperado ao tentar clicar no botão de exportar XLS: {e}")
                break

        if not botao_clicado:
            log("ERRO: Não foi possível clicar no botão de exportar Excel do Mikael após várias tentativas.")
            raise Exception("Não foi possível exportar XLS do Mikael.")

        sleep(3)  # Espera o download terminar

        # --- Processamento dos Arquivos ---
        log("Processando os arquivos CSV e XLS baixados...")
        caminho_csv = os.path.join(download_path, 'arquivo.csv')
        caminho_xls = os.path.join(
            download_path, 'Meus Apontamentos de Horas.xls')

        # Funções de Processamento
        def processar_arquivo_csv_inner(caminho):
            log(f"--- Processando arquivo CSV: {caminho} ---")
            try:
                with open(caminho, 'r', encoding='ISO-8859-1') as file:
                    lines = file.readlines()
                lines = lines[:-2]  # Remove as últimas 2 linhas (rodape)
                with open(caminho, 'w', encoding='ISO-8859-1') as file:
                    file.writelines(lines)

                dataframe = pd.read_csv(
                    caminho, sep=';', encoding='iso-8859-1')
                day_list = dataframe['Dia'].unique()

                data = {}
                for day in day_list:
                    day_key = datetime.strptime(
                        day, '%d/%m/%Y').strftime('%d/%m/%y')
                    subdataframe = dataframe[dataframe['Dia'] == day]

                    if day_key not in data:
                        data[day_key] = []

                    previous_saida = None
                    for _, row in subdataframe.iterrows():
                        try:
                            entrada = datetime.strptime(
                                str(row['Entrada']), '%H:%M')
                            saida = datetime.strptime(
                                str(row['Saída']), '%H:%M')

                            if previous_saida and (entrada - previous_saida) <= timedelta(minutes=2):
                                # Se a diferença for pequena, mescla com o bloco anterior
                                # Remove o último horário de saída
                                data[day_key].pop()
                                # Adiciona a nova saída
                                data[day_key].append(saida.strftime('%Hh%M'))
                            else:
                                data[day_key].extend(
                                    [entrada.strftime('%Hh%M'), saida.strftime('%Hh%M')])

                            previous_saida = saida
                        except (ValueError, TypeError):
                            log(
                                f"  AVISO: Formato de hora inválido encontrado no CSV para o dia {day_key}. Linha ignorada.")
                            continue
                log("Arquivo CSV processado com sucesso.")
                return data

            except FileNotFoundError:
                log(
                    f"  AVISO: Arquivo CSV '{caminho}' não encontrado. Pulando processamento.")
                return {}
            except Exception as e:
                log(f"  ERRO ao processar o arquivo CSV: {e}")
                return {}

        def processar_arquivo_xls_inner(caminho):
            data_inicio_filtro = pd.to_datetime(
                f"{previous_year}-{previous_month}-26")
            data_fim_filtro = pd.to_datetime(
                f"{current_year}-{current_month}-25")
            log(f"\n--- Processando arquivo XLS: {caminho} ---")
            try:
                df = pd.read_excel(caminho, skiprows=11)

                nome_coluna_data = 'Data Inicial'
                nome_coluna_hora = 'Hora Inicial'
                nome_coluna_evento = 'Tarefa / Evento'

                df[nome_coluna_data] = pd.to_datetime(
                    df[nome_coluna_data], errors='coerce')
                df.dropna(subset=[nome_coluna_data], inplace=True)

                log(
                    f"  Filtrando apontamentos XLS de {data_inicio_filtro.date()} até {data_fim_filtro.date()}...")
                df_filtrado = df[(df[nome_coluna_data] >= data_inicio_filtro) & (
                    df[nome_coluna_data] <= data_fim_filtro)].copy()

                if df_filtrado.empty:
                    log("  Nenhum registro encontrado no XLS para este intervalo de datas.")
                    return {}

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
                # Cria um block_id apenas para iniciar blocos, se o primeiro for interrupção, ignora
                df_processado['block_id'] = (
                    df_processado['is_start'] & df_processado['is_start'].shift(fill_value=True)).cumsum()

                data = {}
                for _, group in df_processado.groupby('block_id'):
                    # Apenas considera blocos que começam com 'is_start' e terminam com 'is_end'
                    if not group.empty and group.iloc[0]['is_start'] and group.iloc[-1]['is_end']:
                        inicio = group.iloc[0]['Timestamp']
                        fim = group.iloc[-1]['Timestamp']
                        day_key = inicio.strftime('%d/%m/%y')

                        if day_key not in data:
                            data[day_key] = []

                        data[day_key].extend(
                            [inicio.strftime('%Hh%M'), fim.strftime('%Hh%M')])
                    else:
                        log(
                            f"  AVISO: Bloco XLS ignorado para block_id {group.name} - não começou/terminou corretamente com Início/Interrupção.")

                log("Arquivo XLS processado com sucesso.")
                return data

            except FileNotFoundError:
                log(
                    f"  AVISO: Arquivo XLS '{caminho}' não encontrado. Pulando processamento.")
                return {}
            except Exception as e:
                log(f"  ERRO ao processar o arquivo XLS: {e}")
                return {}

        dados_csv = processar_arquivo_csv_inner(caminho_csv)
        dados_xls = processar_arquivo_xls_inner(caminho_xls)

        data = dados_csv.copy()  # Começa com os dados do CSV

        for dia, horarios in dados_xls.items():
            if dia in data:
                data[dia].extend(horarios)
                # Garante a ordenação correta de horas
                data[dia].sort(key=lambda x: datetime.strptime(x, '%Hh%M'))
            else:
                data[dia] = sorted(horarios, key=lambda x: datetime.strptime(
                    x, '%Hh%M'))  # Garante a ordenação

        log("\n--- DADOS FINAIS MESCLADOS (CSV + XLS) ---")
        # Usa pformat para formatar o dicionário para o log
        log(pprint.pformat(data))

        if not data:
            log("AVISO: Nenhuns dados de apontamento foram processados. Verifique os relatórios.")
            return  # Sai da função se não há dados para lançar

        # --- Acesso e Login no SGI (Final) ---
        log("Acessando SGI para lançamento de horas...")
        driver.get("https://sgiweb.synchro.com.br/login.html")

        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.NAME, "prfNome"))
            )
            log("Página do SGI carregada.")
        except TimeoutException:
            log("ERRO: Página do SGI demorou muito para carregar. Tentando novamente...")
            driver.refresh()
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.NAME, "prfNome"))
            )
            log("Página do SGI recarregada.")

        log(f"Fazendo login no SGI como: {sgi_user}")
        user_field = driver.find_element(by=By.NAME, value="prfNome")
        password_field = driver.find_element(by=By.NAME, value="prfSenha")
        user_field.send_keys(sgi_user)
        password_field.send_keys(sgi_password)
        password_field.send_keys(Keys.RETURN)
        sleep(2)

        # --- Selecionar Período e Manter Marcações ---
        log("Configurando período e opção 'Manter marcações de jornada' no SGI...")
        try:
            period_select_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "perCodigo"))
            )
            period_select = Select(period_select_element)
            period_value = f"{str(previous_year)[-2:]}{previous_month:02d}"
            period_select.select_by_value(period_value)
            log(f"  Período '{period_value}' selecionado.")
        except Exception as e:
            log(f"ERRO ao selecionar o período no SGI: {e}")
            raise

        try:
            keep_schedule = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//input[@value='HoraEntrada']"))
            )
            keep_schedule.click()
            log("  Opção 'Manter marcações de jornada' selecionada.")
        except Exception as e:
            log(
                f"ERRO ao selecionar 'Manter marcações de jornada' no SGI: {e}")
            raise

        execute_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.NAME, "go"))
        )
        execute_button.click()
        log("  Botão 'Executar' clicado.")
        sleep(2)

        # --- Lançamento das Horas ---
        log("Iniciando lançamento das horas no SGI...")
        dates_already_visited = []

        for date, hours in data.items():
            log(f"  Processando dia: {date} com horas: {hours}")
            try:
                edit_day_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, f"//a[@href=\"javascript: submitform('{date}')\"]"))
                )
                edit_day_button.click()
                sleep(1)  # Pequena pausa para a página carregar após o clique

                index = 0
                while index < len(hours):
                    inputs = driver.find_elements(by=By.NAME, value="hora")

                    if date not in dates_already_visited:
                        # Limpa todos os inputs e preenche os primeiros
                        for input_elem in inputs:
                            if input_elem.get_attribute('value'):
                                input_elem.clear()
                                # Opcional: define um valor padrão limpo
                                input_elem.send_keys('00h00')
                        log(
                            f"  Limpando e preenchendo inputs para o dia {date} pela primeira vez.")
                        for input_elem in inputs:
                            if index < len(hours):
                                input_elem.clear()
                                input_elem.send_keys(hours[index])
                                index += 1
                            else:
                                break
                        dates_already_visited.append(
                            date)  # Marca como visitado
                    else:
                        # Preenche apenas os inputs vazios ou com '00h00'
                        log(
                            f"  Preenchendo inputs adicionais para o dia {date}.")
                        for input_elem in inputs:
                            current_value = input_elem.get_attribute('value')
                            if not current_value or current_value == '00h00':
                                if index < len(hours):
                                    input_elem.clear()
                                    input_elem.send_keys(hours[index])
                                    index += 1
                                else:
                                    break

                    if index == len(hours):
                        log(f"  Todas as horas preenchidas para o dia {date}.")
                        break
                    else:
                        # Ainda há horas para preencher, salvar e recarregar
                        log("  Gravar e recarregar para mais inputs...")
                        save_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable(
                                (By.XPATH, "//input[@value='Gravar']"))
                        )
                        save_button.click()

                        # Volta para a tela de seleção de datas para recarregar
                        driver.back()
                        driver.back()
                        WebDriverWait(driver, 10).until(
                            # Espera um elemento da tela anterior
                            EC.presence_of_element_located((By.NAME, "go"))
                        )
                        driver.refresh()
                        sleep(1)  # Pequena pausa para a tela atualizar

                        # Reclica no botão do dia para abrir novamente
                        edit_day_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable(
                                (By.XPATH, f"//a[@href=\"javascript: submitform('{date}')\"]"))
                        )
                        edit_day_button.click()
                        sleep(1)  # Pausa após reclicar no dia

                # Salvar as últimas horas preenchidas para o dia atual
                log(f"  Salvando lançamentos para o dia {date}.")
                save_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//input[@value='Gravar']"))
                )
                save_button.click()

                # Voltar para a tela de seleção de datas
                driver.back()
                driver.back()
                WebDriverWait(driver, 10).until(
                    # Espera um elemento da tela anterior
                    EC.presence_of_element_located((By.NAME, "go"))
                )
                driver.refresh()
                sleep(1)  # Pausa para a tela de datas carregar

            except Exception as e:
                log(f"ERRO ao processar o dia {date}: {e}. Pulando para o próximo dia.")
                # Tentar voltar para a tela de datas para não travar o loop
                try:
                    driver.back()
                    driver.back()
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.NAME, "go")))
                    driver.refresh()
                except:
                    log("  Não foi possível voltar para a tela de datas após erro. Verifique manualmente.")
                    # Se não conseguir voltar, é melhor encerrar para evitar mais erros
                    raise  # Re-lança a exceção para finalizar o processo principal

        # --- Finalização ---
        log("Processo de lançamento de horas concluído.")

        # Voltar para a página principal (se necessário)
        try:
            driver.back()
            driver.refresh()
            sleep(1)
        except:
            log("Não foi possível voltar para a página principal após lançamento. Ignorando.")

        # Marcar Logoff no SGI
        log("Marcando logoff no SGI...")
        try:
            logoff_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@value='X']"))
            )
            logoff_button.click()

            execute_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.NAME, "go"))
            )
            execute_button.click()
            log("Logoff no SGI efetuado.")
        except Exception as e:
            log(f"AVISO: Não foi possível realizar o logoff no SGI. Erro: {e}")

        log("TimeTrackerTransfer finalizado com sucesso!")

    except Exception as e:
        log(f"ERRO CRÍTICO NO PROCESSO: {e}")
        log("Verifique os logs para mais detalhes e tente novamente.")
    finally:
        if driver:
            log("Fechando o navegador.")
            driver.quit()
        else:
            log("Navegador não foi inicializado ou já foi fechado.")


# --- Código para teste (rodar diretamente este arquivo, sem a GUI) ---
if __name__ == "__main__":
    # Substitua pelos seus dados REAIS para testar!
    # Lembre-se que isto fará alterações no SGI!
    test_netproject_user = os.getenv(
        'NETPROJECT_USER', 'SEU_USUARIO_NETPROJECT')
    test_netproject_password = os.getenv(
        'NETPROJECT_PASSWORD', 'SUA_SENHA_NETPROJECT')
    test_sgi_user = os.getenv('SGI_USER', 'SEU_USUARIO_SGI')
    test_sgi_password = os.getenv('SGI_PASSWORD', 'SUA_SENHA_SGI')
    test_chromedriver_version = os.getenv(
        'CHROMEDRIVE_VERSION', '127.0.6533.88')  # Use sua versão real

    # Função simples de log para quando rodar sem a GUI
    def console_log(message):
        print(message)

    run_time_transfer(
        test_netproject_user,
        test_netproject_password,
        test_sgi_user,
        test_sgi_password,
        test_chromedriver_version,
        log_callback=console_log
    )
