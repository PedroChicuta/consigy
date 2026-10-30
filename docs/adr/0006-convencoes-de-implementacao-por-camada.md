# 6. Convenções de implementação por camada

Data: 2026-10-30

## Status

Proposto

## Contexto

O ADR-0003 define as camadas (models, services, selectors, views), mas não como cada uma é escrita. Sem convenções, cada app tende a resolver transação, erros, forms e testes de um jeito.

## Decisão

- **Services:** funções de módulo com argumentos só por palavra-chave (`*`), nome começando por verbo (`criar_cliente`). Se o arquivo crescer, vira o pacote `services/` com um módulo por agregado.
- **Transações:** o service que escreve é a única fronteira transacional (`@transaction.atomic`). Efeitos externos (e-mail, tasks do Celery) usam `transaction.on_commit`.
- **Erros de negócio:** exceções que herdam de `ErroDeNegocio`, em `exceptions.py` por app. `ValidationError` fica restrito a forms e `clean()` de models.
- **Forms:** validam formato e tipo e entregam dados limpos ao service. A view nunca chama `save()` de form direto.
- **Selectors:** retornam `QuerySet` ou instâncias, com `select_related`/`prefetch_related` e filtros dentro do selector.
- **Testes:** pytest-django e factory_boy; services testados contra o banco real, sem mock de ORM; `tests/` por app com `test_services.py`, `test_selectors.py` e `test_views.py` (views só com fluxo feliz e permissões).
- **HTMX e Bootstrap:** `django-htmx`; templates completos com fragmentos em `templates/<app>/partials/_nome.html`; a mesma view e URL responde com o fragmento quando `request.htmx`. A estilização usa Bootstrap.
- **Acesso:** login obrigatório global por middleware; cada view declara a permissão nativa exigida; grupos ("Operador", "Supervisor") criados por migration de dados.
- **Idioma:** identificadores de domínio em português sem acento (`Cliente`, `criar_cliente`, apps `clientes`); vocabulário técnico em inglês; mensagens ao operador em português com acento.

## Consequências

- Padrão único entre apps, regras testáveis sem HTTP e transações previsíveis.
- Mais arquivos e disciplina de revisão para que regra não vaze para views e forms.
- Mistura de português e inglês no código, aceita para manter o domínio fiel ao vocabulário do negócio.
