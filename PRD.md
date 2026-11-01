# PRD — Substituir a planilha de acompanhamento de consignado

**Status:** Decisões de domínio fechadas (ADR 0011 aceito)
**Origem:** planilha Excel usada hoje pelos Operadores para acompanhar as operações.

## 1. Contexto e problema

Hoje cada operação é uma linha de uma planilha com 12 colunas. Isso traz problemas:

- Os dados do Cliente (nome, CPF, nascimento, telefone) se repetem a cada operação.
- A **Situação** é texto livre e varia entre pessoas ("aguard averb inss", "aguarda averbacao"), o que impede filtrar e contar.
- Não há registro de quem alterou o quê, nem de quando.
- Não há validação: CPF, formato de valores (ex.: `R$ 1.2300,00`) e datas dependem de quem digita.
- Nada impede enviar uma parcela maior que a margem consignável do Benefício.
- Não há controle de acesso.

## 2. Objetivo

Que o Operador faça no sistema tudo o que faz hoje na planilha, com a mesma agilidade, e deixe de usá-la. O sistema também deve eliminar os problemas da seção 1.

**Fora do escopo (por ora):**

- Importação e exportação de planilha. O sistema começa vazio e as operações são digitadas nele.
- Margem própria do cartão com saque: a regra de margem é a mesma para todas as Modalidades.
- Convênio e API REST (ver `CLAUDE.md` e os ADRs).

## 3. Planilha atual (referência)

Colunas:

`NOME | CPF | Número do Benefício | Data de nascimento | Telefone | Valor do Crédito | Valor Liberado | Valor da Parcela | Quantidade de Parcelas | Nome Banco | Tipo de Contrato | Situação`

Valores de **Tipo de Contrato** encontrados:

- port + refin
- cartão com saque

Valores de **Situação** encontrados:

- `Pago em [data]`
- `aguard averb inss`
- `aguarda averbacao`
- `aguard saldo`
- `port autorizada`

Linha de exemplo:

| NOME | CPF | Benefício | Nascimento | Telefone | Crédito | Liberado | Parcela | Parcelas | Banco | Tipo | Situação |
|---|---|---|---|---|---|---|---|---|---|---|---|
| TESTE | 12345678909 | 1324297481 | 02/01/1964 | 82988888888 | R$ 1.2300,00 | R$ 436,49 | R$ 126,54 | 96 | facta | port+ refin | Pago em 30/07 |

## 4. Cobertura atual do sistema

### 4.1 Colunas já atendidas

| Coluna da planilha | No sistema |
|---|---|
| NOME, CPF, Data de nascimento, Telefone | `Cliente` |
| Número do Benefício | `Beneficio` (número único, espécie, vinculado ao Cliente) |
| Valor do Crédito | `Proposta.valor` e `Contrato.valor` |
| Valor da Parcela | `Proposta.parcela` e `Contrato.parcela` |
| Quantidade de Parcelas | `prazo` |
| Nome Banco | `Banco` (cadastro mantido pelo Supervisor) |
| Situação | `Proposta.status` e `Contrato.status` (etapas fixas e ordenadas) |

### 4.2 Onde o sistema já é melhor que a planilha

- **Cliente cadastrado uma vez.** Vários Benefícios por Cliente e várias Propostas por Benefício, sem repetir dados.
- **CPF validado** pelos dígitos verificadores, único no sistema e mascarado na tela.
- **Situação com etapas fixas.**
  - Proposta: Digitada → Enviada ao Banco → Em análise → Aprovada → Formalizada, ou Recusada / Cancelada.
  - Contrato: Aguardando averbação → Averbado → Pago → Quitado, ou Cancelado.
  - Cada etapa só é marcada a partir da anterior.
  - Recusar e cancelar exigem motivo.
  - Cancelar uma Proposta já Aprovada exige permissão de Supervisor.
- **Margem consignável** com data da consulta e histórico. O envio da Proposta é bloqueado se a parcela for maior que a margem ou se não houver margem. Com margem de mais de 30 dias, pede confirmação.
- **Auditoria.** Toda alteração guarda quem fez e quando. Cada Proposta tem o Operador responsável.
- **Busca e filtros.** Clientes por nome, CPF ou número do Benefício. Propostas e Contratos por status, Banco e Cliente. Listas paginadas.
- **Acesso por perfil** (Operador e Supervisor) com login obrigatório.
- **Valores monetários** em `Decimal`, com validação de valor positivo.

## 5. Lacunas

Itens da planilha que o sistema ainda não cobre.

| # | Lacuna | Detalhe |
|---|---|---|
| L1 | **Valor Liberado** | Valor que o Cliente recebe. Em port + refin é menor que o Crédito, pois parte quita o contrato antigo. Não existe campo. |
| L2 | **Tipo de Contrato** | O sistema só conhece "consignado novo". Portabilidade com refinanciamento e cartão com saque não existem. |
| L3 | **Etapas de portabilidade** | "aguard saldo" e "port autorizada" não existem no fluxo atual. |
| L4 | **Data de pagamento** | "Pago em [data]": o sistema só guarda o status. A data só aparece no histórico de alterações. |

## 6. Decisões de domínio

Fechadas na entrevista de definição; termos novos em `GLOSSARY.md`, decisão estrutural em `docs/adr/0011-modalidade-como-cadastro-com-etapas-de-portabilidade.md`.

| # | Decisão |
|---|---|
| D1 | "Tipo de Contrato" da planilha vira **Modalidade**, definida na Proposta e copiada para o Contrato. Cartão com saque entra na primeira versão, no mesmo fluxo de Proposta e Contrato, com prazo e parcela como as demais. |
| D2 | Modalidade é um **cadastro** (não uma lista fixa), mantido no **admin do Django** pelo Supervisor. Valores iniciais: Consignado novo, Portabilidade + refinanciamento, Cartão com saque. |
| D3 | Modalidade inativa não aceita Propostas novas e as existentes a mantêm. Uma Modalidade com Proposta não pode ser apagada. |
| D4 | **Valor Liberado** é digitado pelo Operador, deve ser positivo e não pode superar o Valor do Crédito. Não é calculado. |
| D5 | **Data de pagamento** é obrigatória ao marcar o Contrato como Pago. Padrão: hoje; editável; não pode ser futura. |
| D6 | "aguard averb inss" e "aguarda averbacao" são o mesmo estado, **Aguardando averbação** do Contrato. |
| D7 | Duas etapas novas na Proposta, **Aguardando saldo** e **Portabilidade autorizada**, entre Em análise e Aprovada, nessa ordem. Só valem para Modalidades marcadas "envolve portabilidade". |
| D8 | A regra de margem (parcela ≤ Margem vigente) vale para todas as Modalidades. A margem própria do cartão fica fora do escopo. |
| D9 | Uma migration cria a Modalidade "Consignado novo" e liga a ela as Propostas e Contratos existentes. O Valor Liberado deles é igual ao Valor do Crédito. |

## 7. Requisitos

### R1 — Modalidade (L2)
- Cadastro de Modalidade no admin do Django: nome único, ativa, "envolve portabilidade". Histórico de alterações, com o usuário registrado.
- Escolher a Modalidade ao digitar a Proposta; mostrá-la na lista e no detalhe de Propostas e Contratos.
- Filtrar Propostas e Contratos por Modalidade.

### R2 — Valor Liberado (L1)
- Campo na Proposta, copiado para o Contrato ao formalizar, exibido na lista e no detalhe.
- Validado conforme D4.

### R3 — Etapas de portabilidade (L3)
- Para Modalidades que envolvem portabilidade, a Proposta passa por Aguardando saldo e Portabilidade autorizada antes de Aprovada, em ordem.
- Para as demais, o fluxo atual não muda.
- As novas etapas aparecem no filtro de status e no histórico.

### R4 — Data de pagamento (L4)
- Pedida ao marcar o Contrato como Pago; guardada no Contrato; exibida na lista e no detalhe.
- Filtrar Contratos pagos por período.

## 8. Critérios de aceite

- O Operador cadastra uma operação equivalente à linha de exemplo da seção 3, com todos os campos.
- Toda coluna da planilha tem um campo correspondente na tela de Proposta ou de Contrato.
- O Supervisor cria uma Modalidade nova no admin e ela aparece na digitação de Propostas.
- É possível filtrar por Modalidade e por situação, e achar todos os Contratos pagos em um mês.
- Uma Proposta de portabilidade não chega a Aprovada sem passar por Aguardando saldo e Portabilidade autorizada. Uma de consignado novo não é obrigada a passar por elas.
- As regras de margem continuam valendo para todas as Modalidades.
- Propostas e Contratos anteriores à mudança continuam acessíveis, com Modalidade "Consignado novo".

## 9. Decisões em aberto

| # | Pergunta | Observações |
|---|---|---|
| A1 | Quais Bancos o Supervisor precisa cadastrar de início? | Na amostra aparece só "facta". |
| A2 | Margem própria do cartão com saque. | Adiada (D8). Reavaliar quando o time usar cartão em volume. |

## 10. Impacto na documentação

- `GLOSSARY.md`: Modalidade e Valor liberado adicionados; Proposta e Contrato atualizados (feito).
- `docs/adr/0011-...md`: aceito.
- Migrations para os campos novos em `Proposta` e `Contrato` e para o modelo `Modalidade`.
