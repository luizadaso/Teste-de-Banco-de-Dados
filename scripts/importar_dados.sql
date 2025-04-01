USE teste-de-banco-de-dados;

-- Tarefas de Preparação:
-- 3.1. e 3.2. Baixe os arquivos dos últimos 2 anos e os dados cadastrais das operadoras ativas no formato CSV.

-- Tarefas de Código:
-- 3.3. Crie queries para estruturar tabelas necessárias para o arquivo csv.

-- Tabela para demonstracoes_contabeis
CREATE TABLE demonstracoes_contabeis (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ano INT,
    mes INT,
    operadora_id INT,
    receita DECIMAL(15, 2),
    despesa DECIMAL(15, 2),
    lucro DECIMAL(15, 2),
    despesa_eventos_sinistros DECIMAL(15, 2) -- Adicionando a coluna para despesas específicas
);

-- Tabela para operadoras_ativas
CREATE TABLE operadoras_ativas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    registro_ans INT,
    cnpj VARCHAR(18),
    razao_social VARCHAR(255),
    nome_fantasia VARCHAR(255),
    modalidade VARCHAR(50),
    data_registro DATE,
    uf VARCHAR(2)
);

-- 3.4. Elabore queries para importar o conteúdo dos arquivos preparados, atentando para o encoding correto.

-- Importando dados para a tabela demonstracoes_contabeis
LOAD DATA INFILE '../downloads/demonstracoes_contabeis_2022.csv'
INTO TABLE demonstracoes_contabeis
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(ano, mes, operadora_id, receita, despesa, lucro, despesa_eventos_sinistros);

LOAD DATA INFILE '../downloads/demonstracoes_contabeis_2023.csv'
INTO TABLE demonstracoes_contabeis
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(ano, mes, operadora_id, receita, despesa, lucro, despesa_eventos_sinistros);

-- Importando dados para a tabela operadoras_ativas
LOAD DATA INFILE '../downloads/operadoras_ativas.csv'
INTO TABLE operadoras_ativas
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(registro_ans, cnpj, razao_social, nome_fantasia, modalidade, data_registro, uf);

-- 3.5. Desenvolva uma query analítica para responder:
-- Quais as 10 operadoras com maiores despesas em "EVENTOS/ SINISTROS CONHECIDOS OU AVISADOS DE ASSISTÊNCIA A SAÚDE MEDICO HOSPITALAR" no último trimestre?

SELECT 
    o.nome_fantasia,
    SUM(d.despesa_eventos_sinistros) AS total_despesa_eventos_sinistros
FROM 
    demonstracoes_contabeis d
JOIN 
    operadoras_ativas o ON d.operadora_id = o.registro_ans
WHERE 
    d.ano = YEAR(CURDATE()) AND d.mes >= MONTH(CURDATE()) - 3
GROUP BY 
    o.nome_fantasia
ORDER BY 
    total_despesa_eventos_sinistros DESC
LIMIT 10;

-- Quais as 10 operadoras com maiores despesas nessa categoria no último ano?

SELECT 
    o.nome_fantasia,
    SUM(d.despesa_eventos_sinistros) AS total_despesa_eventos_sinistros
FROM 
    demonstracoes_contabeis d
JOIN 
    operadoras_ativas o ON d.operadora_id = o.registro_ans
WHERE 
    d.ano = YEAR(CURDATE())
GROUP BY 
    o.nome_fantasia
ORDER BY 
    total_despesa_eventos_sinistros DESC
LIMIT 10;