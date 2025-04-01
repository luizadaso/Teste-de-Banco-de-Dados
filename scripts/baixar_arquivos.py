import os
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import zipfile

# Diretório onde os arquivos serão salvos
diretorio_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
diretorio_downloads = os.path.join(diretorio_base, 'downloads')
os.makedirs(diretorio_downloads, exist_ok=True)

# URL base
url_base = 'https://dadosabertos.ans.gov.br/FTP/PDA/demonstracoes_contabeis/'

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
def obter_lista_arquivos(url):
    resposta = requests.get(url)
    if resposta.status_code == 200:
        soup = BeautifulSoup(resposta.text, 'html.parser')
        return [url + node.get('href') for node in soup.find_all('a') if node.get('href').endswith('.zip')]
    else:
        print(f'Erro ao acessar {url}: {resposta.status_code}')
        return []

# Função para descompactar arquivos ZIP
def descompactar_arquivo_zip(caminho_zip, caminho_destino):
    with zipfile.ZipFile(caminho_zip, 'r') as zip_ref:
        zip_ref.extractall(caminho_destino)
    print(f'Arquivo descompactado: {caminho_zip} para {caminho_destino}')

# Baixar arquivos dos últimos 2 anos
ano_atual = datetime.now().year
anos_para_baixar = [ano_atual - 1, ano_atual - 2]
for ano in anos_para_baixar:
    url_ano = f'{url_base}{ano}/'
    arquivos = obter_lista_arquivos(url_ano)
    for arquivo in arquivos:
        nome_arquivo = os.path.basename(arquivo)
        caminho_destino = os.path.join(diretorio_downloads, nome_arquivo)
        baixar_arquivo(arquivo, caminho_destino)
        
        # Criar pasta do ano e descompactar o arquivo
        caminho_pasta_ano = os.path.join(diretorio_downloads, str(ano))
        os.makedirs(caminho_pasta_ano, exist_ok=True)
        descompactar_arquivo_zip(caminho_destino, caminho_pasta_ano)

# Baixar dados cadastrais das operadoras ativas
url_operadoras = 'https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/operadoras_ativas.zip'
destino_operadoras = os.path.join(diretorio_downloads, 'operadoras_ativas.zip')
baixar_arquivo(url_operadoras, destino_operadoras)

# Criar pasta para operadoras ativas e descompactar o arquivo
caminho_pasta_operadoras = os.path.join(diretorio_downloads, 'operadoras_ativas')
os.makedirs(caminho_pasta_operadoras, exist_ok=True)
descompactar_arquivo_zip(destino_operadoras, caminho_pasta_operadoras)