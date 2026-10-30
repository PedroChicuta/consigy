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

## ADRs

- Decisões arquiteturais ficam em `docs/adr/NNNN-titulo.md` (Nygard, em português; modelo em `0000-modelo.md`).
- Ao surgir uma decisão arquitetural, rascunhe o ADR como "Proposto" e só marque "Aceito" após confirmação do usuário. ADR aceito não se reescreve: crie um novo que o substitua.

## Arquitetura (decisões; ainda não implementadas)

Detalhes e justificativas nos ADRs 0002 a 0005.

- **Interface:** Django templates (SSR) com HTMX e Bootstrap. Sem API REST/SPA por ora. O público são só operadores de backoffice (sem multi-tenancy).
- **Camadas por app:** `models.py` (dados e invariantes simples), `services.py` (escrita e regras de negócio), `selectors.py` (leitura/consultas), `views.py` finas, que só chamam services/selectors. Não colocar regra de negócio em views, forms ou signals.
- **Assíncrono:** Celery + Redis (broker e beat). Tasks finas, que delegam para services.
- **Autenticação:** app `accounts` com `AbstractUser` customizado e `AUTH_USER_MODEL` definido antes da primeira migration. Permissões via grupos/permissões nativos do Django.
- **Auditoria:** `django-simple-history` (`HistoricalRecords`) nos modelos críticos.
- **Dinheiro e taxas:** `DecimalField`, nunca `float`.
- **Dados pessoais (CPF etc.):** sem criptografia de campo por ora (decisão adiada); não logar nem expor CPF sem necessidade.
- **Qualidade:** pytest-django, factory_boy, ruff (lint + format), pre-commit e GitHub Actions.
- **Domínio inicial:** consignado INSS para um correspondente bancário (ver `GLOSSARY.md`). Ordem: clientes e benefícios, bancos, propostas, contratos. Convênio fora do escopo por ora.

## Agent skills

### Issue tracker

Issues e specs ficam como markdown local em `.scratch/<feature>/`. Ver `docs/agents/issue-tracker.md`.

### Triage labels

Vocabulário padrão (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). Ver `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `GLOSSARY.md` na raiz + `docs/adr/`. Ver `docs/agents/domain.md`.
