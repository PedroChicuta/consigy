from decimal import Decimal

import pytest
from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

ANTES = [
    ('propostas', '0007_modalidade_obrigatoria'),
    ('contratos', '0004_permissao_change_operador'),
]
DEPOIS = [('propostas', '0008_valor_liberado'), ('contratos', '0005_valor_liberado')]


def test_nao_ha_migrations_pendentes(db):
    call_command('makemigrations', '--check', '--dry-run', verbosity=0)


@pytest.mark.django_db(transaction=True)
def test_migration_copia_valor_para_registros_antigos():
    executor = MigrationExecutor(connection)
    executor.migrate(ANTES)
    apps = executor.loader.project_state(ANTES).apps
    try:
        # O histórico não tem FKs rígidas, então basta ele para exercitar a cópia.
        HistoricalProposta = apps.get_model('propostas', 'HistoricalProposta')
        HistoricalProposta.objects.create(
            id=1,
            beneficio_id=1,
            banco_id=1,
            modalidade_id=1,
            operador_id=1,
            status='digitada',
            valor=Decimal('5000.00'),
            prazo=12,
            parcela=Decimal('100.00'),
            taxa=Decimal('1.0000'),
            criado_em='2026-01-01T00:00:00Z',
            history_date='2026-01-01T00:00:00Z',
            history_type='+',
        )

        executor = MigrationExecutor(connection)
        executor.migrate(DEPOIS)
        apps = executor.loader.project_state(DEPOIS).apps
        historico = apps.get_model('propostas', 'HistoricalProposta').objects.get(id=1)
        assert historico.valor_liberado == Decimal('5000.00')
    finally:
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
