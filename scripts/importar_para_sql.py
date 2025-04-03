import os
import pandas as pd
import re
from sqlalchemy import create_engine, text, inspect
from database_setup import db_config

# Diretório de destino para cópia dos arquivos
diretorio_uploads = 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads'

# Configurações do banco de dados
usuario = db_config['user']
senha = db_config['password']
host = db_config['host']
banco = db_config['database']

# Criando a string de conexão
conexao_url = f"mysql+mysqlconnector://{usuario}:{senha}@{host}/{banco}"
engine = create_engine(conexao_url)

# Função para remover caracteres especiais da coluna DESCRICAO
def remover_caracteres_especiais(df):
    if "DESCRICAO" in df.columns:
        df["DESCRICAO"] = df["DESCRICAO"].astype(str).apply(lambda x: re.sub(r"[^a-zA-Z0-9\s]", "", x))
    return df

# Função para converter valores decimais
def converter_saldos_para_decimal(df):
    for coluna in ["VL_SALDO_INICIAL", "VL_SALDO_FINAL"]:
        if coluna in df.columns:
            df[coluna] = df[coluna].replace({',': '.'}, regex=True)  # Troca vírgula por ponto
            df[coluna] = pd.to_numeric(df[coluna], errors='coerce')  # Converte para float
            df[coluna] = df[coluna].apply(lambda x: round(x, 2) if pd.notnull(x) else x)  # Arredonda para 2 casas
    return df

# Função para converter datas para o formato YYYY-MM-DD
def converter_datas(df):
    if "DATA" in df.columns:
        df["DATA"] = pd.to_datetime(df["DATA"], errors='coerce', dayfirst=True).dt.strftime('%Y-%m-%d')
    return df

# Função para importar dados do CSV para o MySQL em chunks
def importar_csv_para_mysql(caminho_csv, tabela, colunas, engine, chunksize=50000):
    try:
        # Verificar se o arquivo existe
        if not os.path.exists(caminho_csv):
            print(f"Arquivo não encontrado: {caminho_csv}")
            return

        # Obter todos os REG_ANS válidos
        with engine.connect() as connection:
            result = connection.execute(text("SELECT REGISTRO_ANS FROM Relatorio_Operadoras_Ativas"))
            valid_reg_ans = {row[0] for row in result}

        # Ler o CSV em chunks e carregar no banco de dados
        for chunk in pd.read_csv(caminho_csv, chunksize=chunksize, delimiter=';', usecols=colunas):
            # Remover caracteres especiais da coluna DESCRICAO
            chunk = remover_caracteres_especiais(chunk)

            # Converter valores decimais
            chunk = converter_saldos_para_decimal(chunk)

            # Converter datas para o formato YYYY-MM-DD
            chunk = converter_datas(chunk)

            # Remover duplicatas
            chunk = chunk.drop_duplicates(subset=['REG_ANS'])

            # Filtrar REG_ANS inválidos
            chunk = chunk[chunk['REG_ANS'].isin(valid_reg_ans)]

            # Filtrar valores fora do intervalo permitido
            chunk = chunk[(chunk['VL_SALDO_INICIAL'].abs() <= 1e30) & (chunk['VL_SALDO_FINAL'].abs() <= 1e30)]

            # Verificar se há valores nulos ou inválidos
            chunk = chunk.dropna(subset=['VL_SALDO_INICIAL', 'VL_SALDO_FINAL'])

            # Inserir no banco
            chunk.to_sql(tabela, engine, if_exists='append', index=False)

        print(f"Dados importados com sucesso para a tabela {tabela}!")

    except Exception as e:
        print(f"Erro ao importar os dados do arquivo {caminho_csv}: {e}")

# Função para obter as 10 operadoras com maiores despesas no último trimestre
def maiores_despesas_trimestre(engine):
    query = """
    SELECT
        R.RAZAO_SOCIAL AS 'OPERADORA',
        FORMAT(SUM(D.VL_SALDO_FINAL), 2, 'pt_BR') AS 'DESPESAS',
        D.DESCRICAO,
        D.DATA
    FROM Relatorio_Operadoras_Ativas R
        INNER JOIN dadosimportados AS D ON D.REG_ANS = R.REGISTRO_ANS
    WHERE D.DESCRICAO = 'EVENTOS SINISTROS CONHECIDOS OU AVISADOS DE ASSISTÊNCIA A SAÚDE MEDICO HOSPITALAR'
        AND D.DATA >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)
    GROUP BY R.RAZAO_SOCIAL, D.DATA
    ORDER BY SUM(D.VL_SALDO_FINAL) DESC
    LIMIT 10;
    """
    with engine.connect() as connection:
        result = connection.execute(text(query))
        return result.fetchall()

# Função para obter as 10 operadoras com maiores despesas no último ano
def maiores_despesas_ano(engine):
    query = """
    SELECT
        R.RAZAO_SOCIAL AS 'OPERADORA',
        FORMAT(SUM(D.VL_SALDO_FINAL), 2, 'pt_BR') AS 'DESPESAS',
        D.DESCRICAO,
        D.DATA
    FROM Relatorio_Operadoras_Ativas R
        INNER JOIN dadosimportados AS D ON D.REG_ANS = R.REGISTRO_ANS
    WHERE D.DESCRICAO = 'EVENTOS SINISTROS CONHECIDOS OU AVISADOS DE ASSISTÊNCIA A SAÚDE MEDICO HOSPITALAR'
        AND D.DATA >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
    GROUP BY R.RAZAO_SOCIAL, D.DATA
    ORDER BY SUM(D.VL_SALDO_FINAL) DESC
    LIMIT 10;
    """
    with engine.connect() as connection:
        result = connection.execute(text(query))
        return result.fetchall()

# Função para contar registros em uma tabela
def contar_registros(engine, tabela):
    query = f"SELECT COUNT(*) FROM {tabela}"
    with engine.connect() as connection:
        result = connection.execute(text(query))
        return result.scalar()

# Função para visualizar algumas linhas de uma tabela
def visualizar_dados(engine, tabela, limite=5):
    query = f"SELECT * FROM {tabela} LIMIT {limite}"
    with engine.connect() as connection:
        result = connection.execute(text(query))
        return result.fetchall()

# Função para criar índices e configurar variáveis globais
def configurar_banco_de_dados(engine):
    with engine.connect() as connection:
        inspector = inspect(engine)
        indices = inspector.get_indexes('Relatorio_Operadoras_Ativas')
        index_names = [index['name'] for index in indices]

        if 'idx_reg_ans_data_descricao' not in index_names:
            connection.execute(text("CREATE INDEX idx_reg_ans_data_descricao ON Relatorio_Operadoras_Ativas(REGISTRO_ANS);"))
            print("Índice 'idx_reg_ans_data_descricao' criado com sucesso.")
        else:
            print("Índice 'idx_reg_ans_data_descricao' já existe.")

        # Configurações adicionais
        queries = [
            "SHOW VARIABLES LIKE 'wait_timeout';",
            "SHOW VARIABLES LIKE 'interactive_timeout';",
            "SET GLOBAL wait_timeout = 28800;",
            "SET GLOBAL interactive_timeout = 28800;",
            "GRANT ALL PRIVILEGES ON *.* TO 'root'@'localhost' WITH GRANT OPTION;"
        ]
        for query in queries:
            connection.execute(text(query))
        print("Configurações do banco de dados aplicadas com sucesso!")

# Configurar o banco de dados
configurar_banco_de_dados(engine)

# Importar dados de cada arquivo CSV individualmente
arquivos_csv = [f for f in os.listdir(diretorio_uploads) if f.endswith('.csv') and f != 'Relatorio_Operadoras_Ativas.csv']
for arquivo in arquivos_csv:
    caminho_csv = os.path.join(diretorio_uploads, arquivo)
    importar_csv_para_mysql(caminho_csv, 'dadosimportados', ['REG_ANS', 'DESCRICAO', 'VL_SALDO_FINAL', 'VL_SALDO_INICIAL', 'DATA'], engine)

# Importar dados de operadoras ativas
caminho_operadoras_ativas = os.path.join(diretorio_uploads, 'Relatorio_Operadoras_Ativas.csv')
importar_csv_para_mysql(caminho_operadoras_ativas, 'Relatorio_Operadoras_Ativas', ['Registro_ANS', 'Razao_Social'], engine)

# Verificar se os dados foram importados antes de executar as consultas
inspector = inspect(engine)
if inspector.has_table('dadosimportados') and inspector.has_table('Relatorio_Operadoras_Ativas'):
    # Contar registros nas tabelas
    total_dadosimportados = contar_registros(engine, 'dadosimportados')
    total_operadoras_ativas = contar_registros(engine, 'Relatorio_Operadoras_Ativas')
    print(f"Total de registros em dadosimportados: {total_dadosimportados}")
    print(f"Total de registros em Relatorio_Operadoras_Ativas: {total_operadoras_ativas}")

    # Visualizar algumas linhas das tabelas
    print("Algumas linhas de dadosimportados:")
    print(visualizar_dados(engine, 'dadosimportados'))
    print("Algumas linhas de Relatorio_Operadoras_Ativas:")
    print(visualizar_dados(engine, 'Relatorio_Operadoras_Ativas'))

    # Obter e imprimir as 10 operadoras com maiores despesas no último trimestre
    print("10 operadoras com maiores despesas no último trimestre:")
    print(maiores_despesas_trimestre(engine))

    # Obter e imprimir as 10 operadoras com maiores despesas no último ano
    print("10 operadoras com maiores despesas no último ano:")
    print(maiores_despesas_ano(engine))
else:
    print("As tabelas necessárias não foram encontradas no banco de dados.")

# Fechar a conexão
engine.dispose()