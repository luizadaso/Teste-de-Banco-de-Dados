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
def obter_lista_arquivos(url, extensao='.zip'):
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

# Função para remover caracteres especiais da coluna DESCRICAO
def remover_caracteres_especiais(df):
    if "DESCRICAO" in df.columns:
        df["DESCRICAO"] = df["DESCRICAO"].astype(str).apply(lambda x: re.sub(r"[^a-zA-Z0-9\s]", "", x))
    return df

# Função para converter colunas de saldo para float
def converter_saldos_para_decimal(df):
    for coluna in ["VL_SALDO_INICIAL", "VL_SALDO_FINAL"]:
        if coluna in df.columns:
            df[coluna] = df[coluna].replace({',': '.'}, regex=True)  # Troca vírgula por ponto
            df[coluna] = pd.to_numeric(df[coluna], errors='coerce')  # Converte para float
            df[coluna] = df[coluna].apply(lambda x: round(x, 2) if pd.notnull(x) else x)  # Arredonda para 2 casas
    return df

# Função para pré-processar arquivos CSV
def preprocessar_arquivos_csv(diretorio):
    arquivos = [f for f in os.listdir(diretorio) if f.endswith('.csv')]
    lista_dfs = []

    for arquivo in arquivos:
        caminho_entrada = os.path.join(diretorio, arquivo)

        try:
            # Detecta o delimitador automaticamente
            with open(caminho_entrada, "r", encoding="latin1") as f:
                primeira_linha = f.readline()
                delimitador = ";" if ";" in primeira_linha else ","

            # Ler o CSV com delimitador correto
            df = pd.read_csv(caminho_entrada, encoding="latin1", delimiter=delimitador, on_bad_lines="skip")

            # Remover caracteres especiais da coluna DESCRICAO
            df = remover_caracteres_especiais(df)

            # Converter as colunas de saldo para float
            df = converter_saldos_para_decimal(df)

            # Adicionar o DataFrame à lista
            lista_dfs.append(df)
            print(f"Arquivo processado: {arquivo}")
        except Exception as e:
            print(f"Erro ao processar {arquivo}: {e}")

    # Concatenar todos os DataFrames em um único DataFrame
    df_final = pd.concat(lista_dfs, ignore_index=True)

    # Caminho do arquivo final
    caminho_saida_final = os.path.join(diretorio, "dados_combinados.csv")

    # Salvar o DataFrame final em um único arquivo CSV
    df_final.to_csv(caminho_saida_final, encoding="utf-8", index=False, sep=delimitador)
    print(f"Arquivos combinados salvos em: {caminho_saida_final}")

# Baixar arquivos dos últimos 2 anos
ano_atual = datetime.now().year
anos_para_baixar = [ano_atual - 1, ano_atual - 2]
arquivos_para_baixar = []

for ano in anos_para_baixar:
    url_ano = f'{url_base}{ano}/'
    arquivos = obter_lista_arquivos(url_ano)
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

# Pré-processar arquivos CSV no diretório de uploads
preprocessar_arquivos_csv(diretorio_uploads)

# Excluir todos os arquivos ZIP após o processo
excluir_arquivos_zip(diretorio_downloads)