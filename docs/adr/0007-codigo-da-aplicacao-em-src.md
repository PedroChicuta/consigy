# 7. Código da aplicação em `src/`

Data: 2026-10-31

## Status

Proposto

## Contexto

Apps, `core/`, `templates/` e `manage.py` ficavam na raiz, misturados com Dockerfile, compose, docs, scripts e arquivos de configuração. Com mais apps previstos, a raiz perde legibilidade e fica difícil separar o código da aplicação da infraestrutura.

## Decisão

- Todo o código Python e HTML da aplicação fica em `src/`: `core/`, os apps e `manage.py`.
- Templates ficam dentro de cada app, em `<app>/templates/<app>/` (achados por `APP_DIRS`; os nomes lógicos, como `clientes/form.html`, não mudam). Os compartilhados (`base.html`, `403.html`) ficam em `core/templates/`, registrado em `TEMPLATES['DIRS']`; `core` segue como pacote de configuração, fora de `INSTALLED_APPS`. Partials de um app podem ser incluídos por outro pelo nome lógico.
- `src/` é o source root (diretório de trabalho e `pythonpath`); os imports continuam sem prefixo (`clientes.services`, `core.settings`), então `INSTALLED_APPS` e migrations não mudam.
- `BASE_DIR` é `src/`; `ROOT_DIR` é a raiz do repositório e abriga `.env`, `db.sqlite3` e `staticfiles/`.
- Docker usa `WORKDIR`/`working_dir` `/app/src`. `requirements.txt`, `docs/`, `scripts/` e `pyproject.toml` ficam na raiz.
- pytest roda da raiz (`pythonpath` e `testpaths` em `src`); ruff usa `src = ["src"]`.

## Consequências

- Raiz limpa e fronteira clara entre aplicação e infraestrutura.
- Comandos do Django passam a rodar de `src/`; pytest e ruff continuam na raiz.
- `DATABASE_URL` com SQLite relativo passaria a depender do diretório de trabalho; por isso o padrão é deixá-lo vazio e usar `ROOT_DIR`.
