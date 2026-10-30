# Crédito Consignado

Sistema de backoffice para operadores que concedem e acompanham crédito consignado a aposentados e pensionistas do INSS.

## Linguagem

**Cliente**:
Pessoa física, aposentada ou pensionista do INSS, identificada por um CPF único no sistema.
_Avoid_: Beneficiário, segurado, tomador

**Benefício**:
Aposentadoria ou pensão do INSS de um Cliente, com número, espécie e margem consignável próprios. Um Cliente pode ter vários.
_Avoid_: Vínculo, matrícula

**Correspondente**:
A empresa que usa o sistema: intermedeia o crédito entre o Cliente e o Banco, sem emprestar dinheiro próprio.
_Avoid_: Financeira, instituição

**Operador**:
Funcionário do Correspondente que atende o Cliente e conduz a proposta no sistema.
_Avoid_: Atendente, usuário

**Banco**:
Instituição financeira que analisa a Proposta, concede o crédito e paga o Contrato. O Correspondente trabalha com vários.
_Avoid_: Financeira, credor

**Margem consignável**:
Valor máximo da renda mensal de um Benefício que pode ser comprometido com parcelas. É digitada pelo Operador junto com a data da consulta.
_Avoid_: Limite, saldo

**Proposta**:
Pedido de empréstimo consignado novo, feito sobre um Benefício e enviado a um Banco, com as condições que o Banco ofereceu (valor, prazo, parcela, taxa). Passa por Digitada, Enviada ao Banco, Em análise, Aprovada e Formalizada, ou termina Recusada (pelo Banco) ou Cancelada (por desistência).
_Avoid_: Pedido, solicitação, simulação

**Contrato**:
Empréstimo efetivado, nascido de uma única Proposta Formalizada. Passa por Averbado (o INSS confirmou o desconto), Pago (o Banco liberou o dinheiro ao Cliente) e Quitado, ou termina Cancelado se a averbação ou o pagamento falha.
_Avoid_: Empréstimo, operação
