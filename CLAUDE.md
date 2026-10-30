# CLAUDE.md

Projeto Django 6.1 (Python 3.14) para o domínio de crédito consignado. O pacote de configuração é `core/`. Ainda não há apps próprios.

## Comandos

- Dev: `docker compose up --build` / `docker compose down`
- Prod: `docker compose -f docker-compose.prod.yml up -d --build` / `... down` (`down -v` apaga o volume do PostgreSQL)
- Sem Docker: `.venv/bin/python manage.py runserver`, `migrate`, `test`, `check`
- Dependências em `requirements.txt` (versões fixas). Ao adicionar uma, instale no `.venv` e atualize o arquivo.

## Configuração

- Tudo vem de variáveis de ambiente via django-environ em `core/settings.py`; o modelo está em `.env.example`. Nunca versionar `.env`.
- `SECRET_KEY` é obrigatória; `DEBUG` assume `False`.
- `DATABASE_URL`: SQLite em dev, PostgreSQL em prod (o `docker-compose.prod.yml` monta a URL a partir de `POSTGRES_*` e força `DEBUG=False`).
- E-mail usa `MAILERS` (Django 6.1). Não definir `EMAIL_HOST`, `EMAIL_PORT` etc. como settings do Django: com `MAILERS` presente isso levanta `ImproperlyConfigured`. O host lido do env fica na variável local `_email_host`.
- Idioma `pt-br`, fuso `America/Sao_Paulo`.
- Estáticos servidos pelo whitenoise; `STATIC_ROOT` é `staticfiles/`.

## Convenções

- Código e comentários em português quando houver texto de domínio; mantenha o estilo do `settings.py` (aspas simples).
- Novos apps: `python manage.py startapp <nome>` e registrar em `INSTALLED_APPS`.
