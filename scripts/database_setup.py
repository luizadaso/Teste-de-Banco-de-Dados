import mysql.connector
from mysql.connector import Error

# Configurações do banco de dados
db_config = {
    'user': 'root',
    'password': 'anAmotocros57!',
    'host': 'localhost',
    'database': 'teste_de_banco_de_dados'
}

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

if __name__ == "__main__":
    criar_banco_e_tabelas(db_config)