import os
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import zipfile
import shutil
import pandas as pd
import re
import time

# Diretório onde os arquivos serão salvos
diretorio_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
diretorio_downloads = os.path.join(diretorio_base, 'downloads')
os.makedirs(diretorio_downloads, exist_ok=True)

# Diretório de destino para cópia dos arquivos
diretorio_uploads = 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads'
os.makedirs(diretorio_uploads, exist_ok=True)

# URL base
url_base = 'https://dadosabertos.ans.gov.br/FTP/PDA/demonstracoes_contabeis/'
url_operadoras_ativas = 'https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/'

# Função para baixar um arquivo
def baixar_arquivo(url, destino):
    resposta = requests.get(url)
    if resposta.status_code == 200:
        with open(destino, 'wb') as f:
            f.write(resposta.content)
        print(f'Arquivo baixado: {destino}')
    else:
        print(f'Erro ao baixar {url}: {resposta.status_code}')

# Função para obter a lista de arquivos em um diretório
def obter_lista_arquivos(url, extensao='.csv'):
    resposta = requests.get(url)
    if resposta.status_code == 200:
        soup = BeautifulSoup(resposta.text, 'html.parser')
        return [url + node.get('href') for node in soup.find_all('a') if node.get('href').endswith(extensao)]
    else:
        print(f'Erro ao acessar {url}: {resposta.status_code}')
        return []

# Função para descompactar arquivos ZIP
def descompactar_arquivo_zip(caminho_zip, caminho_destino):
    with zipfile.ZipFile(caminho_zip, 'r') as zip_ref:
        for member in zip_ref.namelist():
            filename = os.path.basename(member)
            if not filename:
                continue
            source = zip_ref.open(member)
            target_path = os.path.join(caminho_destino, filename)
            # Verificar se o comprimento do caminho é válido
            if len(target_path) > 260:
                print(f"Erro: O caminho do arquivo é muito longo: {target_path}")
                continue
            with open(target_path, "wb") as target:
                shutil.copyfileobj(source, target)
    print(f'Arquivo descompactado: {caminho_zip} para {caminho_destino}')

# Função para copiar arquivos para o diretório de uploads
def copiar_arquivos(origem, destino):
    for root, dirs, files in os.walk(origem):
        for file in files:
            caminho_origem = os.path.join(root, file)
            caminho_destino = os.path.join(destino, file)
            shutil.copy2(caminho_origem, caminho_destino)
            print(f'Arquivo copiado para: {caminho_destino}')

# Função para excluir arquivos ZIP
def excluir_arquivos_zip(diretorio):
    for root, dirs, files in os.walk(diretorio):
        for file in files:
            if file.endswith('.zip'):
                os.remove(os.path.join(root, file))
                print(f'Arquivo ZIP removido: {os.path.join(root, file)}')

# Baixar arquivos dos últimos 2 anos
ano_atual = datetime.now().year
anos_para_baixar = [ano_atual - 1, ano_atual - 2]
arquivos_para_baixar = []

for ano in anos_para_baixar:
    url_ano = f'{url_base}{ano}/'
    arquivos = obter_lista_arquivos(url_ano, extensao='.zip')
    arquivos_para_baixar.extend(arquivos)

# Baixar todos os arquivos
for arquivo in arquivos_para_baixar:
    nome_arquivo = os.path.basename(arquivo)
    caminho_destino = os.path.join(diretorio_downloads, nome_arquivo)
    baixar_arquivo(arquivo, caminho_destino)

# Descompactar todos os arquivos e criar pastas por ano
for arquivo in arquivos_para_baixar:
    nome_arquivo = os.path.basename(arquivo)
    caminho_destino = os.path.join(diretorio_downloads, nome_arquivo)
    ano = nome_arquivo.split('T')[1].split('.')[0]  # Extrair o ano do nome do arquivo
    caminho_pasta_ano = os.path.join(diretorio_downloads, ano)
    os.makedirs(caminho_pasta_ano, exist_ok=True)
    descompactar_arquivo_zip(caminho_destino, caminho_pasta_ano)

# Copiar todos os arquivos descompactados para o diretório de uploads
for ano in anos_para_baixar:
    caminho_pasta_ano = os.path.join(diretorio_downloads, str(ano))
    copiar_arquivos(caminho_pasta_ano, diretorio_uploads)

# Baixar o arquivo de operadoras de plano de saúde ativas
arquivos_operadoras_ativas = obter_lista_arquivos(url_operadoras_ativas, extensao='.csv')
if arquivos_operadoras_ativas:
    url_operadoras_ativas_csv = arquivos_operadoras_ativas[0]
    caminho_operadoras_ativas = os.path.join(diretorio_downloads, 'Relatorio_Operadoras_Ativas.csv')
    baixar_arquivo(url_operadoras_ativas_csv, caminho_operadoras_ativas)

    # Copiar o arquivo baixado para o diretório de uploads
    caminho_operadoras_ativas_uploads = os.path.join(diretorio_uploads, 'Relatorio_Operadoras_Ativas.csv')
    shutil.copy2(caminho_operadoras_ativas, caminho_operadoras_ativas_uploads)
    print(f'Arquivo copiado para: {caminho_operadoras_ativas_uploads}')
else:
    print("Erro: Nenhum arquivo CSV encontrado no diretório de operadoras de plano de saúde ativas.")

# Verificar se os arquivos foram gerados corretamente
caminho_arquivo_operadoras = os.path.join(diretorio_uploads, "Relatorio_Operadoras_Ativas.csv")

if os.path.exists(caminho_arquivo_operadoras):
    print(f"Arquivo {caminho_arquivo_operadoras} gerado com sucesso.")
else:
    print(f"Erro: Arquivo {caminho_arquivo_operadoras} não foi gerado.")

# Excluir todos os arquivos ZIP após o processo
excluir_arquivos_zip(diretorio_downloads)