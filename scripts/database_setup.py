import mysql.connector
from mysql.connector import Error

# Configurações do banco de dados
db_config = {
    'user': 'root',
    'password': 'senha',
    'host': 'localhost',
    'database': 'teste_de_banco_de_dados'
}

# Função para executar o script SQL
def executar_script_sql(caminho_script, connection):
    with open(caminho_script, 'r') as file:
        script_sql = file.read()
    cursor = connection.cursor()
    for resultado in script_sql.split(';'):
        if resultado.strip():
            cursor.execute(resultado)
    connection.commit()

# Função para criar o banco de dados e as tabelas
def criar_banco_e_tabelas(db_config):
    connection = None
    try:
        connection = mysql.connector.connect(
            user=db_config['user'],
            password=db_config['password'],
            host=db_config['host']
        )
        if connection.is_connected():
            print("Conectado ao MySQL")
            executar_script_sql('setup.sql', connection)
            print("Banco de dados e tabelas criados com sucesso!")
    except Error as e:
        print(f"Erro ao conectar ao MySQL: {e}")
    finally:
        if connection and connection.is_connected():
            connection.close()
            print("Conexão ao MySQL encerrada.")

if __name__ == "__main__":
    criar_banco_e_tabelas(db_config)