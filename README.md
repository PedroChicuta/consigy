# Consignado

Projeto Django (6.1) com SQLite em desenvolvimento e PostgreSQL em produção, ambos via Docker.

## Pré-requisitos

- Docker e Docker Compose
- (Opcional, sem Docker) Python 3.14

## Configuração inicial

```bash
cp .env.example .env
```

Edite o `.env` e troque pelo menos `SECRET_KEY`. Para gerar uma chave:

```bash
python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

## Desenvolvimento (SQLite)

Subir:

```bash
docker compose up --build
```

A aplicação fica em http://localhost:8000 (admin em `/admin/`). O código é montado como volume, então alterações recarregam sozinhas. As migrations rodam automaticamente ao subir.

Descer:

```bash
docker compose down
```

O banco é o arquivo `db.sqlite3` na raiz do projeto, então os dados sobrevivem ao `down`. Para zerar, apague o arquivo.

Comandos úteis (com o container no ar):

```bash
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py test
docker compose logs -f web
```

## Produção (PostgreSQL)

No `.env`, defina valores reais para `SECRET_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `POSTGRES_PASSWORD` e, se for enviar e-mails, as variáveis `EMAIL_*`.

Subir:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Ao iniciar, o container roda `migrate` e `collectstatic` e depois o gunicorn na porta 8000. O compose de produção força `DEBUG=False` e monta a `DATABASE_URL` a partir das variáveis `POSTGRES_*`.

Descer (mantém os dados do banco):

```bash
docker compose -f docker-compose.prod.yml down
```

Descer apagando o volume do PostgreSQL (**apaga todos os dados**):

```bash
docker compose -f docker-compose.prod.yml down -v
```

Comandos úteis:

```bash
docker compose -f docker-compose.prod.yml logs -f web
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

## Sem Docker

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # ajuste a SECRET_KEY
cd src
python manage.py migrate
python manage.py runserver
```

## Variáveis de ambiente

Todas estão documentadas em `.env.example`: Django (`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`), idioma e fuso, banco (`DATABASE_URL`, `POSTGRES_*`), `CSRF_TRUSTED_ORIGINS`, `CORS_ALLOWED_ORIGINS` e SMTP. Se `EMAIL_HOST` estiver vazio, os e-mails são impressos no console.
