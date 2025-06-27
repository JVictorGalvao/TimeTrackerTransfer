import subprocess
import platform
import re
import os

def get_chrome_version():
    """
    Tenta detectar a versão do Google Chrome instalada no sistema.
    Retorna a versão como string (ex: "127.0.6533.88") ou None se não for encontrada.
    """
    os_name = platform.system()

    if os_name == "Windows":
        try:
            # Tenta ler do registro do Windows
            # O comando 'reg query' pode variar ligeiramente dependendo da versão do Windows/Chrome
            command = r'reg query "HKCU\Software\Google\Chrome\BLBeacon" /v version'
            result = subprocess.run(command, capture_output=True, text=True, shell=True, check=True)
            match = re.search(r'version\s+REG_SZ\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
            if match:
                return match.group(1)
            
            # Se não encontrou no HKCU, tenta HKLM (para instalações de todos os usuários)
            command = r'reg query "HKLM\Software\Google\Chrome\BLBeacon" /v version'
            result = subprocess.run(command, capture_output=True, text=True, shell=True, check=True)
            match = re.search(r'version\s+REG_SZ\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
            if match:
                return match.group(1)

        except (subprocess.CalledProcessError, FileNotFoundError):
            pass # Continua para a próxima tentativa se o comando falhar ou não encontrar

        # Tenta obter a versão do executável (mais complexo para parsear em algumas versões)
        try:
            chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
            if not os.path.exists(chrome_path):
                chrome_path = "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"

            if os.path.exists(chrome_path):
                # Executar chrome.exe --version
                command = f'"{chrome_path}" --version'
                result = subprocess.run(command, capture_output=True, text=True, shell=True, check=True)
                match = re.search(r'Chrome\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
                if match:
                    return match.group(1)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass # Ignora e retorna None

    elif os_name == "Linux":
        try:
            # Tenta 'google-chrome --version'
            command = "google-chrome --version"
            result = subprocess.run(command, capture_output=True, text=True, shell=True, check=True)
            match = re.search(r'Google Chrome (\d+\.\d+\.\d+\.\d+)', result.stdout)
            if match:
                return match.group(1)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        try:
            # Tenta 'chromium --version' ou 'chromium-browser --version'
            command = "chromium --version"
            result = subprocess.run(command, capture_output=True, text=True, shell=True, check=True)
            match = re.search(r'Chromium (\d+\.\d+\.\d+\.\d+)', result.stdout)
            if match:
                return match.group(1)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    elif os_name == "Darwin": # macOS
        try:
            # Tenta 'Google Chrome --version'
            command = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome --version"
            result = subprocess.run(command, capture_output=True, text=True, shell=True, check=True)
            match = re.search(r'Google Chrome (\d+\.\d+\.\d+\.\d+)', result.stdout)
            if match:
                return match.group(1)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    return None # Retorna None se a versão não for encontrada