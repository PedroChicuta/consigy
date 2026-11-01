# 11. Modalidade como cadastro, com etapas de portabilidade condicionais

Data: 2026-11-01

## Status

Aceito

## Contexto

A planilha que o time usa hoje classifica cada operação por "Tipo de Contrato" (portabilidade com refinanciamento, cartão com saque) e acompanha etapas que o fluxo atual de Proposta não tem ("aguardando saldo", "portabilidade autorizada"). Até aqui o sistema só conhece o consignado novo.

Novas modalidades podem aparecer sem que o time queira esperar uma mudança de código. Os demais cadastros (Banco) são mantidos por telas do sistema, com `services.py` (ADR 0003 e 0006); o admin do Django só serve para usuários.

## Decisão

- **Modalidade é um modelo**, não uma lista fixa no código. Tem nome único, `ativo` e o indicador "envolve portabilidade", com histórico de alterações (ADR 0005).
- **Cadastro pelo admin do Django**, restrito ao Supervisor. Não passa por `services.py`, porque a única regra é a unicidade do nome. Se a Modalidade ganhar regra de negócio, o cadastro migra para telas e services.
- A Proposta tem uma Modalidade obrigatória, copiada para o Contrato quando ele nasce.
- Uma Modalidade inativa não aceita Propostas novas, mas Propostas e Contratos existentes a mantêm. Uma Modalidade com Proposta não pode ser apagada, só inativada.
- O fluxo da Proposta ganha duas etapas, **Aguardando saldo** e **Portabilidade autorizada**, entre Em análise e Aprovada, nessa ordem. Só valem para Modalidades que envolvem portabilidade; as demais seguem o fluxo atual sem passar por elas.
- A regra de margem continua única para todas as Modalidades: a parcela não pode superar a Margem consignável vigente. A margem própria do cartão fica fora do escopo por ora.
- Uma migration cria a Modalidade "Consignado novo" e liga a ela as Propostas e Contratos existentes.

## Consequências

- Uma Modalidade nova que siga um fluxo já existente (com ou sem portabilidade) não exige código, só um cadastro no admin.
- Uma Modalidade com fluxo diferente dos dois existentes, como o cartão com margem própria, continua exigindo mudança de código e talvez outro ADR.
- O fluxo de status da Proposta passa a depender da Modalidade, e `avancar_proposta` precisa validar a ordem das etapas conforme o indicador. Isso aumenta os casos de teste de transição.
- A Modalidade fica fora do padrão de cadastros (telas + services). Quem mantém o código precisa saber da exceção.
- O admin não aplica `_history_user` por padrão. É preciso garantir que as edições de Modalidade registrem o usuário no histórico.
