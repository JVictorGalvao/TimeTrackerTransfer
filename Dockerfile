# Usa o Ubuntu 20.04 como base
FROM ubuntu:20.04

# Define o diretório de trabalho
WORKDIR /app

# ---- BLOCO DE INSTALAÇÃO À PROVA DE FALHAS ----
# Força a configuração do fuso horário de forma não-interativa e instala tudo num passo só
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y tzdata && \
    ln -snf /usr/share/zoneinfo/America/Sao_Paulo /etc/localtime && echo "America/Sao_Paulo" > /etc/timezone && \
    apt-get install -y python3 python3-pip python3-tk && \
    rm -rf /var/lib/apt/lists/*
# ---- FIM DO BLOCO ----

# Instala as bibliotecas Python
RUN pip3 install --no-cache-dir pyinstaller pandas selenium webdriver-manager openpyxl

# Copia seu script para o ambiente
COPY automacao.py .

# Comando final: Apenas executa o PyInstaller
CMD ["pyinstaller", "--noconfirm", "--name", "AutomacaoPonto", "automacao.py"]