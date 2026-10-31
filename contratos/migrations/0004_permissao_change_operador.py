from django.db import migrations


def atribuir(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    permissao = Permission.objects.get(content_type__app_label='contratos', codename='change_contrato')
    Group.objects.get(name='Operador').permissions.add(permissao)


class Migration(migrations.Migration):
    dependencies = [
        ('contratos', '0003_contrato_motivo'),
    ]

    operations = [
        migrations.RunPython(atribuir, migrations.RunPython.noop),
    ]
