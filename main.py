import os

from datetime import datetime
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

# Verify if the file already exists
if os.path.exists('arquivo.csv'):
    # Remove the file
    os.remove('arquivo.csv')

# Date variables
current_year = datetime.now().year
previous_year = current_year # If the current month is january, the last month is december of the previous year
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
    "download.default_directory": download_path, # Setting download path to current directory
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
})

# Check README to see wich version of chromedriver is compatible with your browser
driver = webdriver.Chrome(service=Service(ChromeDriverManager(driver_version=os.getenv("CHROMEDRIVE_VERSION")).install()), options=options)

# # Access the Netproject website
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

finish_filter_button = driver.find_element(by=By.XPATH, value="//button[contains(text(), 'Filtrar')]")
finish_filter_button.click()

# Download the CSV report file
csv_download_button = driver.find_element(by=By.ID, value="btn_csv")
csv_download_button.click()

sleep(2) # Wait for the download to finish

# Lê todas as linhas do arquivo CSV
with open('arquivo.csv', 'r', encoding='ISO 8859-2') as file:
    lines = file.readlines()

# Remove the last two lines (Trash)
lines = lines[:-2]

with open('arquivo.csv', 'w', encoding='ISO 8859-2') as file:
    file.writelines(lines)

dataframe = pd.read_csv('arquivo.csv', sep=';', encoding='iso-8859-2')

task_list = dataframe['Projeto'].unique()

data = {}

for task in task_list:
    data[task] = {}
    subdataframe = dataframe[dataframe['Projeto'] == task]

    for index, row in subdataframe.iterrows():
        date = datetime.strptime(row['Dia'], '%d/%m/%Y').strftime('%d/%m/%y')

        if date not in data[task]:
           data[task][date] = [row['Entrada'].replace(":", "h"), row['Saída'].replace(":", "h")]
        else:
            data[task][date].extend([row['Entrada'].replace(":", "h"), row['Saída'].replace(":", "h")])

    aux_value = data[task]
    aux_key = task.split(' - ')[0]
    data.pop(task)
    data[aux_key] = aux_value

pprint.pprint(data)

# Open SGI website
driver.get("https://sgiweb.synchro.com.br/login.html")

# Login
user_field = driver.find_element(by=By.NAME, value="prfNome")
password_field = driver.find_element(by=By.NAME, value="prfSenha")
user_field.send_keys(os.getenv("SGI_USER"))
password_field.send_keys(os.getenv("SGI_PASSWORD"))
password_field.send_keys(Keys.RETURN)

dates_already_visited = []

for task, dates in data.items():
    # Select period
    period_select = Select(driver.find_element(by=By.NAME, value="perCodigo"))
    period_select.select_by_value(f"{str(previous_year)[-2:]}{previous_month:02d}")

    # Insert task code
    task_field = driver.find_element(by=By.NAME, value="prjCodigoTxt")
    task_field.send_keys(task)

    # Select "Manter marcações de jornada"
    keep_schedule = driver.find_element(by=By.XPATH, value="//input[@value='HoraEntrada']")
    keep_schedule.click()

    # Click on "Executar"
    execute_button = driver.find_element(by=By.NAME, value="go")
    execute_button.click()

    # Iterate through each date at the current project code
    for date, hours in dates.items():
        edit_day_button = driver.find_element(by=By.XPATH, value=f"//a[@href=\"javascript: submitform('{date}')\"]")
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
                        input.send_keys('00h00') # Set the default value at filled inputs to 00h00
                for input in inputs:
                    input.clear()
                    input.send_keys(hours[index])
                    index += 1
                    dates_already_visited.append(date)
                    if index == len(hours):
                        break
            else: # If it's not the first time visiting the date, fill only the empty inputs
                for input in inputs:
                    if not input.get_attribute('value') or input.get_attribute('value') == '00h00':
                        input.clear()
                        input.send_keys(hours[index])
                        index += 1
                        if index == len(hours):
                            break

            if index == len(hours): # If all hours were filled,
                break
            else: # If there are still hours to fill, click on "Gravar" and refresh this date to open new inputs
                save_button = driver.find_element(by=By.XPATH, value="//input[@value='Gravar']")
                save_button.click()

                driver.back()
                driver.back()
                driver.refresh()

                edit_day_button = driver.find_element(by=By.XPATH, value=f"//a[@href=\"javascript: submitform('{date}')\"]")
                edit_day_button.click()
    
        # Save the last filled hours
        save_button = driver.find_element(by=By.XPATH, value="//input[@value='Gravar']")
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