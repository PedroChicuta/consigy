# 8. Tema visual: só cores sobre o Bootstrap

Data: 2026-11-01

## Status

Proposto

## Contexto

O backoffice usava o Bootstrap 5.3.3 (ADR 0002) sem identidade visual própria nem preferência de tema do Operador. Era preciso uma identidade (verde escuro `#14532D`) com modo claro e escuro, sem introduzir etapa de build (Sass, Node) e sem alterar layout ou componentes.

## Decisão

- O tema muda **apenas cores** sobre o Bootstrap: sobrescrevemos variáveis CSS do Bootstrap em um único arquivo (`src/core/static/tema.css`), carregado depois do CSS do Bootstrap no template base. Sem Sass e sem etapa de build; o whitenoise serve o arquivo.
- Claro e escuro usam o mecanismo nativo do Bootstrap 5.3 (`data-bs-theme` no elemento raiz).
- Na primeira visita vale `prefers-color-scheme`; ao alternar, a escolha vai para o `localStorage` do navegador. Um script no `<head>` aplica o tema antes da renderização para evitar flash. Sem biblioteca JS.
- A cor primária é usada só em ações; o verde de sucesso do Bootstrap permanece e é usado só em estados, sempre com texto.
- Um teste automático calcula o contraste WCAG AA (mínimo 4,5:1) dos pares de cor nos dois modos.
- A página `/design/` serve de referência dos componentes e só existe com `DEBUG` ligado.

### Fora de escopo

- Mudanças de layout, tipografia, espaçamento ou componentes novos (decididos à parte).
- Preferência de tema no cadastro do Operador (campo em `accounts`, migration, endpoint).
- Biblioteca de componentes, Storybook, Sass ou build.
- Testes automatizados de navegador (clique do botão e `localStorage` são verificados manualmente).
- Logo, ícones próprios e identidade além da paleta.

## Consequências

- Trocar a paleta é editar um único arquivo; atualizar o Bootstrap fica simples por não haver override de layout.
- A preferência fica por navegador, não por Operador; migrar para um campo do usuário no futuro é possível sem retrabalho no tema.
- Ajustes de cor podem quebrar o contraste, mas o teste acusa a regressão.
- O `localStorage` e o botão de tema não têm cobertura automatizada.
