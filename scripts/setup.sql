-- Criação do banco de dados
CREATE DATABASE IF NOT EXISTS `teste_de_banco_de_dados`;
USE `teste_de_banco_de_dados`;

-- Criação da tabela Relatorio_Operadoras_Ativas
CREATE TABLE IF NOT EXISTS `Relatorio_Operadoras_Ativas` (
    `REGISTRO_ANS` INT PRIMARY KEY,
    `RAZAO_SOCIAL` VARCHAR(255)
);

-- Criação da tabela dadosimportados
CREATE TABLE IF NOT EXISTS `dadosimportados` (
    `REG_ANS` INT,
    `DESCRICAO` VARCHAR(255),
    `VL_SALDO_FINAL` DECIMAL(30, 2),
    `VL_SALDO_INICIAL` DECIMAL(30, 2),
    `DATA` DATE,
    FOREIGN KEY (`REG_ANS`) REFERENCES `Relatorio_Operadoras_Ativas`(`REGISTRO_ANS`)
);