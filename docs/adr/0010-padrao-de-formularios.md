# 10. Padrão de formulários

Data: 2026-11-01

## Status

Aceito

## Contexto

Cada template de formulário repetia o mesmo laço de campos e só o `PropostaForm` aplicava classes do Bootstrap nos widgets; os demais saíam com inputs sem estilo. Erros apareciam como texto vermelho solto, sem ligação acessível com o campo, e os formulários embutidos nas telas de detalhe (Margem, Observações, motivos de encerramento) usavam inputs escritos à mão, sem rótulo.

## Decisão

- Um **renderer global** (`FORM_RENDERER = 'core.formularios.RendererBootstrap'`, sobre `TemplatesSetting`) define o HTML de todo formulário, inclusive os futuros. Os `forms.py` não declaram classes CSS.
- Um `BoundField` próprio aplica `form-control`, `form-select` ou `form-check-input` conforme o widget, preservando classes já declaradas, e `is-invalid` quando há erro.
- Cada campo mostra rótulo, "(opcional)" quando não é obrigatório (sem asterisco nos obrigatórios), texto de ajuda e erros abaixo do input, ligados por `aria-describedby`. Erros gerais e de campos ocultos aparecem em alerta no topo.
- Os campos ficam numa grade de duas colunas; textarea e checkbox ocupam a linha toda, e um formulário com um único campo também.
- **Página de formulário:** `formularios/pagina.html` (título, descrição opcional, card com os campos e rodapé com Cancelar e Salvar à direita). Validação só no servidor (`novalidate`).
- **Formulário embutido:** `formularios/_cartao.html` (card com título opcional e botão no rodapé). Os de motivo deixam a validação do navegador ligada para barrar o envio vazio, já que a view só redireciona com mensagem.
- O login usa o mesmo HTML de campo (`as_field_group`), num card centralizado.
- `/design/` mostra o padrão renderizado, inclusive com erros.

## Consequências

- Formulário novo fica no padrão sem esforço: basta `{{ form }}` ou estender `formularios/pagina.html`.
- A largura de cada campo segue o tipo de widget; layouts específicos (três colunas, agrupamento por seção) exigiriam estender o padrão.
- `django.forms` entra em `INSTALLED_APPS` para o `TemplatesSetting` achar os templates de widget do Django.
- Rótulos padrão do Django sem tradução pt-br (como o `empty_label` do Django 6.1) precisam ser definidos no form.
