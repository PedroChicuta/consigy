# 3. Organização em services e selectors por app

Data: 2026-10-30

## Status

Aceito

## Contexto

Regras de negócio de crédito consignado (margem, simulação, status de proposta) tendem a crescer. Colocá-las em views, forms ou signals as espalha e dificulta o reuso por tasks do Celery e por futuras interfaces.

## Decisão

Cada app seguirá a estrutura:

- `models.py`: dados e invariantes simples.
- `services.py`: escrita e regras de negócio.
- `selectors.py`: leitura e consultas.
- `views.py`: finas, apenas chamam services e selectors.

Regras de negócio não ficam em views, forms ou signals. Tasks do Celery também delegam para services.

## Consequências

- Regras reutilizáveis por views, tasks e comandos de gerenciamento, e fáceis de testar sem HTTP.
- Um pouco mais de arquivos e indireção que o Django padrão.
- Exige disciplina nas revisões para que a regra não vaze para as views.
