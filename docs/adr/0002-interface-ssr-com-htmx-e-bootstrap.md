# 2. Interface SSR com HTMX e Bootstrap

Data: 2026-10-30

## Status

Aceito

## Contexto

O sistema é usado apenas por operadores de backoffice, com muitos formulários e tabelas. Não há, por ora, clientes finais, parceiros nem integrações que exijam uma API pública. Uma API REST com SPA separada exigiria dois deploys, duas camadas de validação e mais código para o mesmo resultado.

## Decisão

A interface será renderizada no servidor com templates do Django. Usaremos HTMX para interatividade parcial e Bootstrap para os componentes visuais. Não haverá API REST nem SPA por ora.

## Consequências

- Um único deploy e uma única base de código, com validação centralizada nos forms do Django.
- Desenvolvimento rápido de telas CRUD no backoffice.
- Se surgirem clientes finais, parceiros ou integrações externas, será preciso expor uma API em um novo ADR. Por isso a lógica de negócio fica em services, e não nas views (ver ADR-0003).
- O `CORS_ALLOWED_ORIGINS` já configurado fica sem uso até lá.
