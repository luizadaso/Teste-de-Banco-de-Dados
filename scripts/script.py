import os
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import zipfile
import shutil
import pandas as pd
import mysql.connector
from mysql.connector import Error

# Diretório onde os arquivos serão salvos
diretorio_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
diretorio_downloads = os.path.join(diretorio_base, 'downloads')
os.makedirs(diretorio_downloads, exist_ok=True)

# Diretório de destino para cópia dos arquivos
diretorio_uploads = 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads'
os.makedirs(diretorio_uploads, exist_ok=True)

# Configurações do banco de dados
db_config = {
    'user': 'root',
    'password': 'anAmotocros57!',
    'host': 'localhost',
    'database': 'teste_de_banco_de_dados'
}

# URL base
url_base = 'https://dadosabertos.ans.gov.br/FTP/PDA/demonstracoes_contabeis/'

# Função para criar o banco de dados e as tabelas
def criar_banco_e_tabelas(db_config):
    try:
        connection = mysql.connector.connect(
            user=db_config['user'],
            password=db_config['password'],
            host=db_config['host']
        )
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("CREATE DATABASE IF NOT EXISTS teste_de_banco_de_dados")
            cursor.execute("USE teste_de_banco_de_dados")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Relatorio_Operadoras_Ativas (
                    REGISTRO_ANS INT PRIMARY KEY,
                    RAZAO_SOCIAL VARCHAR(255)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dadosimportados (
                    REG_ANS INT,
                    DESCRICAO VARCHAR(255),
                    VL_SALDO_FINAL DECIMAL(10, 2),
                    VL_SALDO_INICIAL DECIMAL(10, 2),
                    DATA DATE,
                    FOREIGN KEY (REG_ANS) REFERENCES Relatorio_Operadoras_Ativas(REGISTRO_ANS)
                )
            """)
            connection.commit()
            print("Banco de dados e tabelas criados com sucesso!")
    except Error as e:
        print(f"Erro ao conectar ao MySQL: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Conexão ao MySQL encerrada.")

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
        zip_ref.extractall(caminho_destino)
    print(f'Arquivo descompactado: {caminho_zip} para {caminho_destino}')
    os.remove(caminho_zip)
    print(f'Arquivo ZIP removido: {caminho_zip}')

# Função para copiar arquivos para o diretório de uploads
def copiar_arquivos(origem, destino):
    for root, dirs, files in os.walk(origem):
        for file in files:
            caminho_origem = os.path.join(root, file)
            caminho_destino = os.path.join(destino, file)
            shutil.copy2(caminho_origem, caminho_destino)
            print(f'Arquivo copiado para: {caminho_destino}')

# Função para importar dados do CSV para o MySQL
def importar_csv_para_mysql(caminho_csv, tabela, colunas, db_config):
    # Ler o arquivo CSV usando pandas
    # Adicionar depuração para verificar os nomes das colunas
    df_temp = pd.read_csv(caminho_csv, nrows=0)
    print(f"Nomes das colunas no arquivo CSV: {df_temp.columns.tolist()}")

    df = pd.read_csv(caminho_csv, usecols=colunas)

    # Conectar ao banco de dados MySQL
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            cursor = connection.cursor()

            # Inserir os dados do DataFrame no banco de dados
            for index, row in df.iterrows():
                if tabela == 'Relatorio_Operadoras_Ativas':
                    insert_query = f"""
                    INSERT INTO {tabela} (REGISTRO_ANS, RAZAO_SOCIAL)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE RAZAO_SOCIAL = VALUES(RAZAO_SOCIAL);
                    """
                    cursor.execute(insert_query, (row['Registro_ANS'], row['Razao_Social']))
                else:
                    insert_query = f"""
                    INSERT INTO {tabela} (REG_ANS, DESCRICAO, VL_SALDO_FINAL, VL_SALDO_INICIAL, DATA)
                    VALUES (%s, %s, %s, %s, %s);
                    """
                    cursor.execute(insert_query, (row['REG_ANS'], row['DESCRICAO'], row['VL_SALDO_FINAL'], row['VL_SALDO_INICIAL'], row['DATA']))
            
            connection.commit()
            print(f"Dados importados com sucesso para a tabela {tabela}!")

    except Error as e:
        print(f"Erro ao conectar ao MySQL: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Conexão ao MySQL encerrada.")

# Criar banco de dados e tabelas
criar_banco_e_tabelas(db_config)

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
        
        # Copiar arquivos descompactados para o diretório de uploads
        copiar_arquivos(caminho_pasta_ano, diretorio_uploads)

# Baixar dados cadastrais das operadoras ativas
url_operadoras_base = 'https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/'
arquivos_operadoras = obter_lista_arquivos(url_operadoras_base, extensao='.csv')
for arquivo in arquivos_operadoras:
    caminho_pasta_operadoras = os.path.join(diretorio_downloads, 'operadoras_ativas')
    os.makedirs(caminho_pasta_operadoras, exist_ok=True)
    destino_operadoras_temp = os.path.join(caminho_pasta_operadoras, os.path.basename(arquivo))
    destino_operadoras_final = os.path.join(caminho_pasta_operadoras, 'Relatorio_Operadoras_Ativas.csv')
    baixar_arquivo(arquivo, destino_operadoras_temp)
    
    # Verificar se o arquivo de destino já existe e removê-lo se necessário
    if os.path.exists(destino_operadoras_final):
        os.remove(destino_operadoras_final)
    
    os.rename(destino_operadoras_temp, destino_operadoras_final)
    print(f'Arquivo renomeado para: {destino_operadoras_final}')
    
    # Copiar o arquivo CSV para o diretório de uploads
    shutil.copy2(destino_operadoras_final, diretorio_uploads)
    print(f'Arquivo copiado para: {os.path.join(diretorio_uploads, "Relatorio_Operadoras_Ativas.csv")}')

# Importar os dados do CSV para o MySQL
importar_csv_para_mysql(destino_operadoras_final, 'Relatorio_Operadoras_Ativas', ['Registro_ANS', 'Razao_Social'], db_config)

# Importar dados das tabelas trimestrais
arquivos_trimestres = [
    os.path.join(diretorio_uploads, '4T2024.csv'),
    os.path.join(diretorio_uploads, '3T2024.csv'),
    os.path.join(diretorio_uploads, '2T2024.csv'),
    os.path.join(diretorio_uploads, '1T2024.csv')
]

for arquivo in arquivos_trimestres:
    importar_csv_para_mysql(arquivo, 'dadosimportados', ['REG_ANS', 'DESCRICAO', 'VL_SALDO_FINAL', 'VL_SALDO_INICIAL', 'DATA'], db_config)