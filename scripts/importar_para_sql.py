import os
import pandas as pd
import mysql.connector
from mysql.connector import Error
import re
from database_setup import db_config

# Diretório de destino para cópia dos arquivos
diretorio_uploads = 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads'

# Função para remover caracteres especiais da coluna DESCRICAO
def remover_caracteres_especiais(df):
    if "DESCRICAO" in df.columns:
        df["DESCRICAO"] = df["DESCRICAO"].astype(str).apply(lambda x: re.sub(r"[^a-zA-Z0-9\s]", "", x))
    return df

# Função para converter valores decimais
def converter_valores_decimais(df, colunas):
    for coluna in colunas:
        if coluna in df.columns:
            df[coluna] = df[coluna].str.replace(',', '.').astype(float)
    return df

# Função para importar dados do CSV para o MySQL
def importar_csv_para_mysql(caminho_csv, tabela, colunas, db_config):
    # Ler o arquivo CSV usando pandas
    # Adicionar depuração para verificar os nomes das colunas
    df_temp = pd.read_csv(caminho_csv, delimiter=';', nrows=0)
    print(f"Nomes das colunas no arquivo CSV: {df_temp.columns.tolist()}")

    df = pd.read_csv(caminho_csv, delimiter=';', usecols=colunas)

    # Remover caracteres especiais da coluna DESCRICAO
    df = remover_caracteres_especiais(df)

    # Converter valores decimais
    df = converter_valores_decimais(df, ['VL_SALDO_FINAL', 'VL_SALDO_INICIAL'])

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

# Importar dados das tabelas trimestrais
arquivos_trimestres = [
    os.path.join(diretorio_uploads, '4T2024.csv'),
    os.path.join(diretorio_uploads, '3T2024.csv'),
    os.path.join(diretorio_uploads, '2T2024.csv'),
    os.path.join(diretorio_uploads, '1T2024.csv')
]

for arquivo in arquivos_trimestres:
    importar_csv_para_mysql(arquivo, 'dadosimportados', ['REG_ANS', 'DESCRICAO', 'VL_SALDO_FINAL', 'VL_SALDO_INICIAL', 'DATA'], db_config)

# Importar dados do CSV para o MySQL
destino_operadoras_final = os.path.join(diretorio_uploads, 'Relatorio_Operadoras_Ativas.csv')
importar_csv_para_mysql(destino_operadoras_final, 'Relatorio_Operadoras_Ativas', ['Registro_ANS', 'Razao_Social'], db_config)