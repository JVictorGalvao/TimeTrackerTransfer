import os
import sys
import threading
import queue
from datetime import datetime, timedelta
import pprint
from time import sleep

# --- Imports da Interface Gráfica ---
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk  # Adicionado ttk para o Combobox

# --- Imports do seu script original ---
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

# --- FUNÇÃO DE PERÍODOS ATUALIZADA ---


def generate_periods(months_past=12, months_future=4):
    """
    Gera um dicionário de períodos, incluindo meses passados e futuros.
    """
    periods = {}
    today = datetime.now()

    # Gera períodos passados
    for i in range(months_past):
        # Usamos uma abordagem mais segura para evitar problemas com meses de durações diferentes
        current_month_date = today - timedelta(days=i * 28)
        first_day_of_month = current_month_date.replace(day=1)
        end_date = first_day_of_month.replace(day=25)
        start_date = (first_day_of_month - timedelta(days=1)).replace(day=26)

        display_str = f"{start_date.strftime('%d/%m/%Y')} até {end_date.strftime('%d/%m/%Y')}"
        if display_str not in periods:
            periods[display_str] = {
                'start_year': start_date.year, 'start_month': start_date.month,
                'end_year': end_date.year, 'end_month': end_date.month
            }

    # Gera períodos futuros
    for i in range(1, months_future + 1):
        # Usamos uma abordagem mais segura para avançar os meses
        current_month_date = today + timedelta(days=i * 31)
        first_day_of_month = current_month_date.replace(day=1)
        end_date = first_day_of_month.replace(day=25)
        start_date = (first_day_of_month - timedelta(days=1)).replace(day=26)

        display_str = f"{start_date.strftime('%d/%m/%Y')} até {end_date.strftime('%d/%m/%Y')}"
        if display_str not in periods:
            periods[display_str] = {
                'start_year': start_date.year, 'start_month': start_date.month,
                'end_year': end_date.year, 'end_month': end_date.month
            }

    return periods

# ==============================================================================
# LÓGICA DE AUTOMAÇÃO (NÃO FOI ALTERADA)
# ==============================================================================


def run_automation_logic(credentials, period_data, log_queue):
    """
    Função principal que contém toda a lógica de automação.
    Recebe as credenciais e o período selecionado da interface.
    """
    try:
        # --- Extrai as credenciais do dicionário ---
        netproject_user = credentials['netproject_user']
        netproject_password = credentials['netproject_password']
        sgi_user = credentials['sgi_user']
        sgi_password = credentials['sgi_password']

        # --- Limpeza de arquivos antigos ---
        log_queue.put("Iniciando limpeza de arquivos antigos...")
        if os.path.exists('arquivo.csv'):
            os.remove('arquivo.csv')
            log_queue.put("arquivo.csv removido.")

        if os.path.exists('Meus Apontamentos de Horas.xls'):
            os.remove('Meus Apontamentos de Horas.xls')
            log_queue.put("Meus Apontamentos de Horas.xls removido.")

        # --- As variáveis agora vêm do período selecionado ---
        previous_year = period_data['start_year']
        previous_month = period_data['start_month']
        current_year = period_data['end_year']
        current_month = period_data['end_month']
        current_day = 25

        log_queue.put(
            f"Período selecionado para processar: 26/{previous_month}/{previous_year} a {current_day}/{current_month}/{current_year}")

        # Determina o caminho de download para o diretório do script
        if getattr(sys, 'frozen', False):
            download_path = os.path.dirname(sys.executable)
        else:
            download_path = os.path.dirname(os.path.abspath(__file__))

        # --- Configurações do Navegador ---
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

        log_queue.put("Configurando o navegador Chrome...")
        driver = webdriver.Chrome(service=Service(
            ChromeDriverManager().install()), options=options)

        # O restante da lógica de automação abaixo permanece IDÊNTICO.

        # ======================================================================
        # ETAPA 1: NETPROJECT
        # ======================================================================
        log_queue.put("Acessando Netproject...")
        driver.get("https://projetos.synchro.com.br")

        while True:
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "username")))
                log_queue.put("Página do Netproject carregada com sucesso.")
            except:
                log_queue.put("A página demorou muito para carregar: F5")
                driver.refresh()
                continue
            break

        log_queue.put("Realizando login no Netproject...")
        user_field = driver.find_element(by=By.ID, value="username")
        password_field = driver.find_element(by=By.ID, value="password")
        user_field.send_keys(netproject_user)
        password_field.send_keys(netproject_password)
        password_field.send_keys(Keys.RETURN)

        log_queue.put("Navegando até o relatório de apontamentos...")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "userbox"))).click()
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "menu_549"))).click()

        log_queue.put("Aplicando filtro de datas...")
        driver.find_element(by=By.ID, value="fw_abre_filtro").click()

        init_date = driver.find_element(by=By.ID, value="ini")
        init_date.clear()
        init_date.send_keys(f"26/{previous_month}/{previous_year}")

        end_date = driver.find_element(by=By.ID, value="fim")
        end_date.clear()
        end_date.send_keys(f"{current_day}/{current_month}/{current_year}")

        driver.find_element(
            by=By.XPATH, value="//button[contains(text(), 'Filtrar')]").click()

        log_queue.put("Baixando o arquivo CSV (arquivo.csv)...")
        driver.find_element(by=By.ID, value="btn_csv").click()
        sleep(3)

        # ======================================================================
        # ETAPA 2: MIKAEL
        # ======================================================================
        log_queue.put("Acessando Mikael...")
        driver.get("https://mikael.synchro.com.br/mikael/indexLogin.jsp")

        while True:
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "loginForm:codlogin")))
                log_queue.put("Página do Mikael carregada com sucesso.")
            except:
                log_queue.put("A página demorou muito para carregar: F5")
                driver.refresh()
                continue
            break

        log_queue.put("Realizando login no Mikael...")
        user_field = driver.find_element(by=By.ID, value="loginForm:codlogin")
        password_field = driver.find_element(
            by=By.ID, value="loginForm:password")
        user_field.send_keys(sgi_user)
        password_field.send_keys(sgi_password)
        password_field.send_keys(Keys.RETURN)

        log_queue.put("Navegando para 'Meus Apontamentos de Horas'...")
        try:
            xpath_apontamentos = "//span[normalize-space()='Apontamentos']"
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                (By.XPATH, xpath_apontamentos))).click()

            xpath_meus_apontamentos = "//span[normalize-space()='Meus Apontamentos de Horas']"
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                (By.XPATH, xpath_meus_apontamentos))).click()
            log_queue.put("Navegação em Mikael concluída.")
        except Exception as e:
            log_queue.put(f"ERRO ao navegar nos menus de Mikael: {e}")
            raise

        log_queue.put(
            "Baixando o arquivo XLS (Meus Apontamentos de Horas.xls)...")
        for i in range(3):
            try:
                xpath_botao_exportar = "//img[contains(@src, 'exportar_excel.png')]"
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                    (By.XPATH, xpath_botao_exportar))).click()
                log_queue.put("Botão de exportar clicado.")
                break
            except (StaleElementReferenceException, TimeoutException) as e:
                log_queue.put(
                    f"Tentativa {i+1} de clicar em exportar falhou. Tentando novamente...")
                if i == 2:
                    raise e
                sleep(1)

        for i in range(3):
            try:
                xpath_botao_excel = "//img[contains(@src, 'excel.gif')]"
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                    (By.XPATH, xpath_botao_excel))).click()
                log_queue.put("Botão de download do Excel clicado.")
                break
            except (StaleElementReferenceException, TimeoutException) as e:
                log_queue.put(
                    f"Tentativa {i+1} de clicar no download do excel falhou. Tentando novamente...")
                if i == 2:
                    raise e
                sleep(1)

        sleep(3)

        # ======================================================================
        # ETAPA 3: PROCESSAMENTO DE DADOS
        # ======================================================================
        def processar_arquivo_csv(caminho_csv):
            log_queue.put("--- Processando arquivo CSV... ---")
            try:
                with open(caminho_csv, 'r', encoding='ISO-8859-1') as file:
                    lines = file.readlines()
                lines = lines[:-2]
                with open(caminho_csv, 'w', encoding='ISO-8859-1') as file:
                    file.writelines(lines)

                dataframe = pd.read_csv(
                    caminho_csv, sep=';', encoding='iso-8859-1')
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
                                row['Entrada'], '%H:%M')
                            saida = datetime.strptime(row['Saída'], '%H:%M')
                            if previous_saida and (entrada - previous_saida) <= timedelta(minutes=2):
                                data[day_key].pop()
                                data[day_key].append(saida.strftime('%Hh%M'))
                            else:
                                data[day_key].extend(
                                    [entrada.strftime('%Hh%M'), saida.strftime('%Hh%M')])
                            previous_saida = saida
                        except (ValueError, TypeError):
                            continue
                log_queue.put("Arquivo CSV processado com sucesso.")
                return data
            except FileNotFoundError:
                log_queue.put(
                    f"AVISO: Arquivo CSV '{caminho_csv}' não encontrado.")
                return {}
            except Exception as e:
                log_queue.put(f"ERRO ao processar o arquivo CSV: {e}")
                return {}

        def processar_arquivo_xls(caminho_xls):
            data_inicio_filtro = pd.to_datetime(
                f"{previous_year}-{previous_month}-26")
            data_fim_filtro = pd.to_datetime(
                f"{current_year}-{current_month}-25")
            log_queue.put("\n--- Processando arquivo XLS... ---")
            try:
                df = pd.read_excel(caminho_xls, skiprows=11)
                nome_coluna_data = 'Data Inicial'
                nome_coluna_hora = 'Hora Inicial'
                nome_coluna_evento = 'Tarefa / Evento'
                df[nome_coluna_data] = pd.to_datetime(
                    df[nome_coluna_data], errors='coerce')
                df.dropna(subset=[nome_coluna_data], inplace=True)
                log_queue.put(
                    f"Filtrando apontamentos de {data_inicio_filtro.date()} até {data_fim_filtro.date()}...")
                df_filtrado = df[(df[nome_coluna_data] >= data_inicio_filtro) & (
                    df[nome_coluna_data] <= data_fim_filtro)].copy()
                if df_filtrado.empty:
                    log_queue.put(
                        "Nenhum registro encontrado no XLS para este intervalo.")
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
                log_queue.put("Arquivo XLS processado com sucesso.")
                return data
            except FileNotFoundError:
                log_queue.put(
                    f"AVISO: Arquivo XLS '{caminho_xls}' não encontrado.")
                return {}
            except Exception as e:
                log_queue.put(f"ERRO ao processar o arquivo XLS: {e}")
                return {}

        caminho_csv = os.path.join(download_path, 'arquivo.csv')
        caminho_xls = os.path.join(
            download_path, 'Meus Apontamentos de Horas.xls')

        dados_csv = processar_arquivo_csv(caminho_csv)
        dados_xls = processar_arquivo_xls(caminho_xls)

        data = dados_csv.copy()
        for dia, horarios in dados_xls.items():
            if dia in data:
                data[dia].extend(horarios)
                data[dia].sort()
            else:
                data[dia] = horarios

        log_queue.put("\n\n--- DADOS FINAIS MESCLADOS (CSV + XLS) ---")
        log_queue.put(pprint.pformat(data))

        # ======================================================================
        # ETAPA 4: SGIWEB - PREENCHIMENTO DO PONTO
        # ======================================================================
        log_queue.put("\n--- Iniciando preenchimento no SGI Web ---")
        driver.get("https://sgiweb.synchro.com.br/login.html")

        log_queue.put("Realizando login no SGI Web...")
        user_field = driver.find_element(by=By.NAME, value="prfNome")
        password_field = driver.find_element(by=By.NAME, value="prfSenha")
        user_field.send_keys(sgi_user)
        password_field.send_keys(sgi_password)
        password_field.send_keys(Keys.RETURN)

        log_queue.put(
            f"Selecionando período {previous_month:02d}/{str(previous_year)[-2:]}...")
        period_select = Select(driver.find_element(
            by=By.NAME, value="perCodigo"))
        period_select.select_by_value(
            f"{str(previous_year)[-2:]}{previous_month:02d}")

        log_queue.put(
            "Selecionando 'Manter marcações de jornada' e executando...")
        driver.find_element(
            by=By.XPATH, value="//input[@value='HoraEntrada']").click()
        driver.find_element(by=By.NAME, value="go").click()

        dates_already_visited = []

        log_queue.put("\n--- Início do preenchimento das marcações ---")
        sorted_dates = sorted(
            data.keys(), key=lambda x: datetime.strptime(x, '%d/%m/%y'))

        for date in sorted_dates:
            hours = data[date]
            log_queue.put(f"Processando dia: {date} com as marcações: {hours}")
            edit_day_button = driver.find_element(
                by=By.XPATH, value=f"//a[@href=\"javascript: submitform('{date}')\"]")
            edit_day_button.click()

            index = 0
            while index < len(hours):
                inputs = driver.find_elements(by=By.NAME, value="hora")
                if date not in dates_already_visited:
                    for input_field in inputs:
                        if input_field.get_attribute('value'):
                            input_field.clear()
                            input_field.send_keys('00h00')
                    for input_field in inputs:
                        input_field.clear()
                        input_field.send_keys(hours[index])
                        index += 1
                        if index == len(hours):
                            break
                    dates_already_visited.append(date)
                else:
                    for input_field in inputs:
                        if not input_field.get_attribute('value') or input_field.get_attribute('value') == '00h00':
                            input_field.clear()
                            input_field.send_keys(hours[index])
                            index += 1
                            if index == len(hours):
                                break

                if index == len(hours):
                    break
                else:
                    log_queue.put(
                        "...Mais marcações que campos. Gravando para obter mais campos...")
                    driver.find_element(
                        by=By.XPATH, value="//input[@value='Gravar']").click()
                    driver.back()
                    driver.back()
                    driver.refresh()
                    driver.find_element(
                        by=By.XPATH, value=f"//a[@href=\"javascript: submitform('{date}')\"]").click()

            log_queue.put(f"Gravando marcações do dia {date}.")
            driver.find_element(
                by=By.XPATH, value="//input[@value='Gravar']").click()
            driver.back()
            driver.back()
            driver.refresh()

        log_queue.put("\n--- Finalizando e fazendo Logoff ---")
        driver.back()
        driver.refresh()
        driver.find_element(by=By.XPATH, value="//input[@value='X']").click()
        driver.find_element(by=By.NAME, value="go").click()

        log_queue.put("\n\nAUTOMAÇÃO CONCLUÍDA COM SUCESSO!")

    except Exception as e:
        log_queue.put(f"\n\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        log_queue.put(f"ERRO CRÍTICO DURANTE A AUTOMAÇÃO: {e}")
        log_queue.put(f"Tipo de erro: {type(e).__name__}")
        log_queue.put(
            f"Verifique o log acima para identificar o último passo executado.")
        log_queue.put(f"O navegador pode permanecer aberto para inspeção.")
        log_queue.put(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        return

    finally:
        if 'driver' in locals() and driver:
            try:
                exc_info = sys.exc_info()
                if exc_info[0] is None:
                    driver.quit()
                    log_queue.put("Navegador fechado.")
            except:
                pass

# ==============================================================================
# CLASSE DA INTERFACE GRÁFICA (COM LÓGICA DE PERÍODO ATUALIZADA)
# ==============================================================================


class AutomationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Automação de Espelho de Ponto")
        self.root.geometry("500x440")

        main_frame = tk.Frame(root, padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)

        period_frame = tk.Frame(main_frame)
        period_frame.pack(fill="x", pady=(0, 10))

        tk.Label(period_frame, text="Período:").pack(side="left", padx=(0, 5))

        self.periods_data = generate_periods(months_past=12, months_future=4)
        period_keys = sorted(
            list(self.periods_data.keys()),
            key=lambda d: datetime.strptime(d.split(' ')[0], '%d/%m/%Y')
        )

        self.period_combobox = ttk.Combobox(
            period_frame,
            values=period_keys,
            state="readonly",
            width=40
        )

        today = datetime.now()
        if today.day <= 25:
            end_date_default = today.replace(day=25)
        else:
            next_month_date = today + timedelta(days=35)
            end_date_default = next_month_date.replace(day=25)

        first_day_of_end_month = end_date_default.replace(day=1)
        start_date_default = (first_day_of_end_month -
                              timedelta(days=1)).replace(day=26)

        default_period_str = f"{start_date_default.strftime('%d/%m/%Y')} até {end_date_default.strftime('%d/%m/%Y')}"

        if default_period_str in period_keys:
            self.period_combobox.set(default_period_str)
        elif period_keys:
            self.period_combobox.set(period_keys[-1])

        self.period_combobox.pack(side="left", fill="x", expand=True)

        credentials_frame = tk.LabelFrame(
            main_frame, text="Credenciais", padx=10, pady=10)
        credentials_frame.pack(fill="x")

        tk.Label(credentials_frame, text="Usuário Netproject:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5)
        self.netproject_user_entry = tk.Entry(credentials_frame, width=25)
        self.netproject_user_entry.grid(
            row=0, column=1, sticky="w", padx=5, pady=5)

        tk.Label(credentials_frame, text="Senha Netproject:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5)
        self.netproject_password_entry = tk.Entry(
            credentials_frame, show="*", width=25)
        self.netproject_password_entry.grid(
            row=1, column=1, sticky="w", padx=5, pady=5)

        self.netproject_show_pass_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            credentials_frame,
            text="Mostrar",
            variable=self.netproject_show_pass_var,
            command=self.toggle_netproject_password,
        ).grid(row=1, column=2, padx=5, sticky="w")

        tk.Label(credentials_frame, text="Usuário SGI/Mikael:").grid(row=2,
                                                                     column=0, sticky="w", padx=5, pady=5)
        self.sgi_user_entry = tk.Entry(credentials_frame, width=25)
        self.sgi_user_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        tk.Label(credentials_frame, text="Senha SGI/Mikael:").grid(row=3,
                                                                   column=0, sticky="w", padx=5, pady=5)
        self.sgi_password_entry = tk.Entry(
            credentials_frame, show="*", width=25)
        self.sgi_password_entry.grid(
            row=3, column=1, sticky="w", padx=5, pady=5)

        self.sgi_show_pass_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            credentials_frame,
            text="Mostrar",
            variable=self.sgi_show_pass_var,
            command=self.toggle_sgi_password,
        ).grid(row=3, column=2, padx=5, sticky="w")

        button_frame = tk.Frame(main_frame, pady=10)
        button_frame.pack(fill="x")

        self.run_button = tk.Button(
            button_frame, text="Executar Automação", command=self.start_automation_thread)
        self.run_button.pack()

        # --- SEÇÃO DO LOG MODIFICADA ---
        log_frame = tk.Frame(main_frame)
        log_frame.pack(fill="both", expand=True)

        # Frame para o título e o botão de copiar
        log_header_frame = tk.Frame(log_frame)
        log_header_frame.pack(fill="x")

        tk.Label(log_header_frame, text="Log de Execução:").pack(side="left")

        # NOVO BOTÃO "Copiar Log"
        self.copy_log_button = ttk.Button(
            log_header_frame, text="Copiar Log", command=self.copy_log_to_clipboard)
        self.copy_log_button.pack(side="right")

        # A janela de log agora volta a ser desabilitada para evitar qualquer problema,
        # pois a cópia será feita pelo botão.
        self.log_text = scrolledtext.ScrolledText(
            log_frame, wrap=tk.WORD, state="disabled", height=10)
        self.log_text.pack(fill="both", expand=True)
        # --- FIM DA SEÇÃO MODIFICADA ---

        self.log_queue = queue.Queue()
        self.root.after(100, self.process_log_queue)

    # --- NOVA FUNÇÃO PARA O BOTÃO DE COPIAR ---
    def copy_log_to_clipboard(self):
        """Copia todo o conteúdo da caixa de log para a área de transferência."""
        # Pega todo o texto do início (1.0) ao fim (END)
        log_content = self.log_text.get(1.0, tk.END)
        # Limpa a área de transferência do sistema
        self.root.clipboard_clear()
        # Adiciona o conteúdo do log à área de transferência
        self.root.clipboard_append(log_content)
        # Mostra uma mensagem de sucesso para o usuário
        messagebox.showinfo(
            "Copiado!", "O conteúdo do log foi copiado para a área de transferência.")

    def toggle_netproject_password(self):
        if self.netproject_show_pass_var.get():
            self.netproject_password_entry.config(show="")
        else:
            self.netproject_password_entry.config(show="*")

    def toggle_sgi_password(self):
        if self.sgi_show_pass_var.get():
            self.sgi_password_entry.config(show="")
        else:
            self.sgi_password_entry.config(show="*")

    def start_automation_thread(self):
        credentials = {
            "netproject_user": self.netproject_user_entry.get(),
            "netproject_password": self.netproject_password_entry.get(),
            "sgi_user": self.sgi_user_entry.get(),
            "sgi_password": self.sgi_password_entry.get()
        }

        selected_period_str = self.period_combobox.get()

        if not all(credentials.values()) or not selected_period_str:
            messagebox.showerror(
                "Erro de Validação", "Todos os campos, incluindo o período, devem ser preenchidos.")
            return

        period_data = self.periods_data[selected_period_str]

        self.run_button.config(state="disabled", text="Executando...")

        # A lógica de limpeza do log volta ao normal (habilitar/desabilitar)
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")

        self.automation_thread = threading.Thread(
            target=run_automation_logic,
            args=(credentials, period_data, self.log_queue),
            daemon=True
        )
        self.automation_thread.start()
        self.root.after(100, self.check_thread)

    def process_log_queue(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                # A lógica de escrita no log volta ao normal (habilitar/desabilitar)
                self.log_text.config(state="normal")
                self.log_text.insert(tk.END, msg + "\n")
                self.log_text.config(state="disabled")
                self.log_text.see(tk.END)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_log_queue)

    def check_thread(self):
        if self.automation_thread.is_alive():
            self.root.after(100, self.check_thread)
        else:
            self.run_button.config(state="normal", text="Executar Automação")


if __name__ == "__main__":
    root = tk.Tk()
    app = AutomationApp(root)
    root.mainloop()
