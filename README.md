# Análise de Gastos com Assistência Médica

Este projeto realiza o processamento e análise de dados financeiros das operadoras de saúde brasileiras com foco em eventos/sinistros médicos-hospitalares. Ele automatiza o download, descompactação e importação dos dados trimestrais dos últimos dois anos, utilizando Python e MySQL para organização e consulta.

## Objetivo

> Identificar as **10 operadoras com maiores gastos** no **último trimestre** e no **último ano** na categoria:
>
> **"EVENTOS/ SINISTROS CONHECIDOS OU AVISADOS DE ASSISTÊNCIA A SAÚDE MÉDICO HOSPITALAR"**

---

## Funcionalidades

- **Download automático** de arquivos trimestrais compactados (ZIP)
- **Descompactação** e remoção dos arquivos ZIP
- **Criação de tabelas** no banco de dados MySQL
- **Importação otimizada** dos dados em chunks (pedaços) para melhor performance
- **Limpeza de dados**: normalização de datas, remoção de caracteres especiais, tratamento de valores decimais e duplicados
- **Consultas analíticas**:
  - Top 10 operadoras com maiores despesas no último trimestre
  - Top 10 operadoras com maiores despesas no último ano

---

## Tecnologias Utilizadas

- **Python 3.13**
  - `pandas` para manipulação de dados
  - `sqlalchemy` e `mysql-connector` para integração com o banco
  - `re` para limpeza textual
  - `os` e `zipfile` para manipulação de arquivos
- **MySQL 8.0**
  - Criação de índices
  - Ajuste de variáveis globais (`wait_timeout`, `interactive_timeout`)
  - Execução de queries analíticas via `JOIN` e `GROUP BY`
- **SQLAlchemy** para ORM e conexão segura com o banco

---

## Estrutura do Projeto

```
README.md
downloads/
├── Relatorio_Operadoras_Ativas.csv
├── 2023/
│   ├── 1T2023.csv
│   ├── 2T2023.csv
│   ├── 3T2023.csv
│   └── 4T2023.csv
├── 2024/
│   ├── 1T2024.csv
│   ├── 2T2024.csv
│   ├── 3T2024.csv
│   └── 4T2024.csv

scripts/
├── baixar_e_preparar.py
├── database_setup.py
├── importar_para_sql.py
├── setup.sql
└── __pycache__/
    └── database_setup.cpython-313.pyc
```

---

## Tabelas Criadas

### `Relatorio_Operadoras_Ativas`
| Campo          | Tipo     |
|----------------|----------|
| REGISTRO_ANS   | String   |
| RAZAO_SOCIAL   | String   |

### `dadosimportados`
| Campo             | Tipo     |
|------------------|----------|
| REG_ANS          | String   |
| DESCRICAO        | String   |
| VL_SALDO_INICIAL | Decimal  |
| VL_SALDO_FINAL   | Decimal  |
| DATA             | Date     |

---

## Consultas Realizadas

- **Top 10 do Trimestre:**
  ```sql
  SELECT R.RAZAO_SOCIAL, SUM(D.VL_SALDO_FINAL)
  FROM Relatorio_Operadoras_Ativas R
  JOIN dadosimportados D ON D.REG_ANS = R.REGISTRO_ANS
  WHERE D.DESCRICAO = 'EVENTOS SINISTROS CONHECIDOS OU AVISADOS DE ASSISTÊNCIA A SAÚDE MEDICO HOSPITALAR'
    AND D.DATA >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)
  GROUP BY R.RAZAO_SOCIAL
  ORDER BY SUM(D.VL_SALDO_FINAL) DESC
  LIMIT 10;
  ```

- **Top 10 do Ano:**
  (Mesma estrutura acima, trocando o intervalo para `1 YEAR`)

---

## Pré-requisitos

- Python 3.10+
- MySQL Server 8.0
- Pacotes Python:
  ```bash
  pip install pandas sqlalchemy mysql-connector-python
  pip install requests beautifulsoup4 pandas
  ```

---

## Como Executar

1. **Configure seu banco de dados** no arquivo `database_setup.py`
2. Certifique-se de que o diretório de uploads esteja configurado corretamente:
   ```python
   diretorio_uploads = r'C:\ProgramData\MySQL\MySQL Server 8.0\Uploads'
   ```
3. Execute o script principal:
   ```bash
   python main.py
   ```

---

## Resultados Esperados

Ao final da execução, o script exibirá:
- Quantidade total de registros importados
- Amostras de dados inseridos
- Listagem das 10 operadoras com maiores gastos no trimestre e no ano

---

## Observações

- Os dados utilizados são públicos e seguem o padrão de layout da ANS.
- O script foi preparado para ser reutilizável e fácil de expandir para novas categorias de análise.
- A manipulação dos arquivos CSV e os filtros por `REG_ANS` garantem que apenas operadoras ativas sejam consideradas.

---

## Autora

Para mais informações, sinta-se à vontade para entrar em contato:

<div align="left">
  <img src="https://github.com/user-attachments/assets/57cac2a3-49b1-4a0a-aef3-e968523971eb" width="15%" alt="autora" />
</div>

- [Github](https://github.com/luizadaso)
- [Linkedin](https://www.linkedin.com/in/luizadaso)
