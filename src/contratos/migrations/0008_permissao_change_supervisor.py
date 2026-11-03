from django.contrib.auth.management import create_permissions
from django.db import migrations


def atribuir(apps, schema_editor):
    app_config = apps.get_app_config('contratos')
    app_config.models_module = True
    create_permissions(app_config, apps=apps, verbosity=0)

    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    grupo, _ = Group.objects.get_or_create(name='Supervisor')
    permissao = Permission.objects.get(
        content_type__app_label='contratos', codename='change_contrato'
    )
    grupo.permissions.add(permissao)


class Migration(migrations.Migration):
    dependencies = [
        ('contratos', '0007_modalidade'),
    ]

    operations = [
        migrations.RunPython(atribuir, migrations.RunPython.noop),
    ]
