import django.db.models.deletion
from django.db import migrations, models


def copiar_modalidade(apps, schema_editor):
    """Contratos antigos ficam com a Modalidade da Proposta de origem (Consignado novo)."""
    Modalidade = apps.get_model('propostas', 'Modalidade')
    Contrato = apps.get_model('contratos', 'Contrato')
    novo, _ = Modalidade.objects.get_or_create(nome='Consignado novo')
    for contrato in Contrato.objects.select_related('proposta'):
        contrato.modalidade_id = contrato.proposta.modalidade_id or novo.pk
        contrato.save(update_fields=['modalidade'])
    apps.get_model('contratos', 'HistoricalContrato').objects.filter(
        modalidade__isnull=True
    ).update(modalidade=novo.pk)


class Migration(migrations.Migration):
    dependencies = [
        ('contratos', '0006_contrato_data_pagamento_and_more'),
        ('propostas', '0008_valor_liberado'),
    ]

    operations = [
        migrations.AddField(
            model_name='contrato',
            name='modalidade',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='contratos',
                to='propostas.modalidade',
            ),
        ),
        migrations.AddField(
            model_name='historicalcontrato',
            name='modalidade',
            field=models.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name='+',
                to='propostas.modalidade',
            ),
        ),
        migrations.RunPython(copiar_modalidade, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='contrato',
            name='modalidade',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='contratos',
                to='propostas.modalidade',
            ),
        ),
    ]
