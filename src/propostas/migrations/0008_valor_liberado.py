from django.db import migrations, models


def copiar_valor(apps, schema_editor):
    """Registros antigos ficam com Valor liberado igual ao Valor do Crédito."""
    for nome in ('Proposta', 'HistoricalProposta'):
        apps.get_model('propostas', nome).objects.update(valor_liberado=models.F('valor'))


class Migration(migrations.Migration):
    dependencies = [
        ('propostas', '0007_modalidade_obrigatoria'),
    ]

    operations = [
        migrations.AddField(
            model_name='proposta',
            name='valor_liberado',
            field=models.DecimalField(
                decimal_places=2, default=0, max_digits=12, verbose_name='valor liberado (R$)'
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='historicalproposta',
            name='valor_liberado',
            field=models.DecimalField(
                decimal_places=2, default=0, max_digits=12, verbose_name='valor liberado (R$)'
            ),
            preserve_default=False,
        ),
        migrations.RunPython(copiar_valor, migrations.RunPython.noop),
    ]
