# 5. Usuário customizado e histórico de alterações

Data: 2026-10-30

## Status

Aceito

## Contexto

Trocar o modelo de usuário depois da primeira migration é doloroso. Além disso, dados de crédito exigem rastreabilidade de quem alterou o quê e quando.

## Decisão

- Criaremos o app `accounts` com um `User` que estende `AbstractUser` e definiremos `AUTH_USER_MODEL` antes da primeira migration.
- Permissões serão controladas pelos grupos e permissões nativos do Django.
- Modelos críticos usarão `django-simple-history` (`HistoricalRecords`), que guarda a versão completa a cada alteração.
- Valores monetários e taxas usam `DecimalField`.
- Criptografia de campos de dados pessoais (CPF etc.) fica adiada.

## Consequências

- Flexibilidade futura para o usuário (campos extras, login por outro identificador).
- Trilha de auditoria completa, ao custo de tabelas históricas adicionais e mais armazenamento.
- Dados pessoais ficam em texto puro no banco por ora; deve ser revisitado em um novo ADR antes de ir para produção com dados reais.
