# 4. Celery e Redis para processamento assíncrono

Data: 2026-10-30

## Status

Aceito

## Contexto

Haverá integrações externas (consulta de margem, averbação), envio de e-mails e geração de relatórios, que não devem bloquear a requisição. Também serão necessárias tarefas agendadas.

## Decisão

Usaremos Celery com Redis como broker, e Celery beat para agendamento. As tasks serão finas e delegarão para services (ver ADR-0003). Redis será adicionado aos arquivos do Docker Compose.

## Consequências

- Solução madura, com retries, agendamento e monitoramento disponíveis.
- Mais dois componentes de infraestrutura (Redis e workers) em dev e prod.
- Alternativas como Django Tasks ou filas sobre PostgreSQL ficaram de fora por ora por serem menos maduras ou menos adequadas ao agendamento.
