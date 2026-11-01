# 9. Navegação com sidebar e barra superior

Data: 2026-10-31

## Status

Proposto

## Contexto

A única navegação era a barra superior (marca, tema, Sair); as áreas do sistema só eram alcançáveis digitando a URL. O Início era um placeholder com uma saudação fixa e um botão HTMX sem função de negócio. O ADR 0008 deixou o layout fora de escopo ("decidido à parte"); esta decisão o complementa sem alterá-lo.

## Decisão

- O layout autenticado tem **barra superior** enxuta (botão do menu, marca com link para o Início e menu do usuário) e **sidebar** com a navegação entre áreas. O login (anônimo) não tem sidebar nem menu do usuário.
- O **menu do usuário** é um dropdown (avatar com iniciais, nome e chevron) que concentra tema, Administração (só `is_staff`) e Sair.
- A sidebar agrupa as áreas em **Cadastros** (Clientes, Bancos) e **Processos** (Propostas, Contratos); cada grupo recolhe/expande pelo título, com chevron animado (collapse do Bootstrap; estado não persistido). Benefícios não tem item próprio: é acessado pelo detalhe do Cliente.
- Grupo sem nenhum item permitido não é exibido. Cada item só aparece se o Operador tiver a permissão `view_*` da área; o 403 continua valendo ao digitar a URL. O item da área atual é destacado pelo namespace da rota.
- Um único botão de menu: em telas largas recolhe/expande a sidebar com deslize (`margin-left` com transição, respeitando `prefers-reduced-motion`); a escolha fica no `localStorage` (como o tema) e é aplicada antes da renderização. Em telas estreitas o mesmo botão abre o offcanvas do Bootstrap.
- Estilos de layout ficam em `core/static/layout.css`, carregado depois do `tema.css`, que segue só com cores (ADR 0008). Ícones (chevron, menu) são SVG inline em `core/templates/componentes/`, sem biblioteca de ícones.
- Os itens vêm de um context processor (`core.navegacao`), que também fornece `nome_operador` (nome completo, ou `username` se vazio).
- Sem dashboard: o Início é só uma página de boas-vindas e continua sendo a aterrissagem pós-login. Um dashboard com indicadores reais será decidido à parte.
- Sem breadcrumbs por ora. `/design/` não entra na navegação.

## Consequências

- Adicionar uma área é acrescentar uma linha em `core/navegacao.py`.
- A lista de permissões do menu duplica a das views de lista; se uma permissão mudar, os dois lugares mudam.
- O recolher/expandir e o offcanvas não têm teste automatizado de comportamento (verificação manual); a preferência é por navegador, não por Operador.
