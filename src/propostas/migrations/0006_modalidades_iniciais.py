from django.contrib.auth.management import create_permissions
from django.db import migrations

MODALIDADES = [
    ('Consignado novo', False),
    ('Portabilidade + refinanciamento', True),
    ('Cartão com saque', False),
]
PERMISSOES_SUPERVISOR = [
    'add_modalidade',
    'change_modalidade',
    'view_modalidade',
    'view_historicalmodalidade',
]


def criar_modalidades(apps, schema_editor):
    Modalidade = apps.get_model('propostas', 'Modalidade')
    for nome, portabilidade in MODALIDADES:
        Modalidade.objects.get_or_create(
            nome=nome, defaults={'envolve_portabilidade': portabilidade}
        )
    novo = Modalidade.objects.get(nome='Consignado novo')
    apps.get_model('propostas', 'Proposta').objects.filter(modalidade__isnull=True).update(
        modalidade=novo
    )
    apps.get_model('propostas', 'HistoricalProposta').objects.filter(
        modalidade__isnull=True
    ).update(modalidade=novo.pk)


def atribuir_permissoes(apps, schema_editor):
    app_config = apps.get_app_config('propostas')
    app_config.models_module = True
    create_permissions(app_config, apps=apps, verbosity=0)

    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    Group.objects.get(name='Supervisor').permissions.add(
        *Permission.objects.filter(
            content_type__app_label='propostas', codename__in=PERMISSOES_SUPERVISOR
        )
    )


def aplicar(apps, schema_editor):
    criar_modalidades(apps, schema_editor)
    atribuir_permissoes(apps, schema_editor)


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0002_grupos_operador_supervisor'),
        ('auth', '0012_alter_user_first_name_max_length'),
        ('propostas', '0005_modalidade'),
    ]

    operations = [migrations.RunPython(aplicar, migrations.RunPython.noop)]
