# 12. Fluxos operacionais contínuos, painel inicial e Modalidades na interface

Data: 2026-11-02

## Status

Aceito

## Contexto

O teste ponta a ponta dos fluxos implementados (`Banco -> Cliente -> Benefício -> Margem -> Proposta -> Contrato`) mostrou atritos recorrentes na rotina do Operador e do Supervisor:

- O **Início** era apenas uma saudação estática (conforme escopo inicial do ADR 0009), forçando o Operador a abrir o menu lateral a cada atendimento e sem visibilidade imediata das Propostas e Contratos que exigem ação.
- O primeiro atendimento de um Cliente exigia alternar entre quatro telas desconectadas (`Novo Cliente -> Detalhe do Cliente -> Novo Benefício -> Detalhe do Benefício para Margem -> Nova Proposta`), sem pré-selecionar o Benefício na criação da Proposta e sem exibir breadcrumbs para retorno rápido.
- O formulário de **Nova Proposta** carregava todos os Benefícios da base num `<select>` único, não exibia a Margem consignável vigente e só validava `parcela > margem` após salvar, num segundo clique em "Enviar ao Banco".
- Ao formalizar uma Proposta, o Operador permanecia na tela da Proposta em vez de seguir para o Contrato recém-criado, e formulários de encerramento ficavam permanentemente abertos na tela.
- **Modalidade** era o único cadastro operacional mantido exclusivamente no admin do Django (ADR 0011), enquanto **Banco** já possuía telas e `services.py` próprios, e o grupo `Supervisor` não possuía permissão `change_contrato`.

Esta decisão complementa os ADRs 0009 (Início e breadcrumbs) e 0010 (múltiplas ações de submissão e retorno contextual em formulários) e substitui parcialmente o ADR 0011 no ponto que restringia o cadastro de Modalidade ao admin do Django.

## Decisão

- **Início operacional (`/`):** a página inicial passa a ser a central de atendimento, contendo busca rápida de Cliente por CPF ou nome (via HTMX, oferecendo atalho direto para `/clientes/novo/?cpf=...` quando o CPF buscado for válido e inexistente) e duas filas acionáveis: **Propostas em andamento** (com filtro "Minhas" vs "Todas", padrão "Minhas" para Operador e "Todas" para Supervisor) e **Contratos pendentes** (`Aguardando averbação` e `Averbado`).
- **Jornada encadeada de atendimento:** mantemos formulários curtos (ADR 0010), mas encadeados por botões secundários de avanço contínuo:
  - Em `Novo Cliente`: `Salvar` e `Salvar e adicionar Benefício`.
  - Em `Novo Benefício`: inclusão opcional da **Margem consignável inicial** (com data da consulta padrão igual à data atual) na mesma transação, com botões `Salvar` e `Salvar e criar Proposta` (redirecionando para `/propostas/nova/?beneficio=<pk>`).
- **Criação e envio contextual de Proposta:**
  - Quando aberta a partir de um Cliente/Benefício (`?beneficio=<pk>`), a Proposta traz o Benefício pré-selecionado; quando aberta pelo menu lateral (`/propostas/nova/`), substitui o `<select>` global por busca HTMX de Cliente/Benefício.
  - O formulário exibe dinamicamente (HTMX) o resumo do Cliente, Benefício e **Margem consignável vigente**, permitindo registrar/atualizar a Margem inline sem perder o preenchimento da Proposta.
  - O formulário oferece dois botões: `Salvar como Digitada` (permite rascunho mesmo com impedimento de Margem, sinalizando aviso no detalhe) e `Salvar e Enviar ao Banco` (executa criação + envio na mesma transação, devolvendo erros de Margem no próprio formulário).
- **Passagem `Proposta -> Contrato` e ações de encerramento:**
  - Mantemos a progressão estrita etapa por etapa definida no ADR 0011, pré-preenchendo a data atual ao marcar Contrato como `Pago`.
  - Ao formalizar uma Proposta, o sistema redireciona diretamente para o detalhe do **Contrato** criado; na Proposta formalizada, um card de destaque substitui a listagem tabular repetida.
  - Os formulários de encerramento (`Recusada pelo Banco` e `Desistência` na Proposta; `Cancelar Contrato` no Contrato) ficam recolhidos em ações discretas/colapsáveis e só aparecem nos status permitidos (sem `Recusada pelo Banco` enquanto `Digitada`, e sem encerramento em status finais).
- **Modalidades na interface e permissões do Supervisor:**
  - O cadastro de **Modalidade** migra do admin do Django para telas próprias no grupo **Cadastros** da sidebar (`/propostas/modalidades/` ou app dedicado/rotas sob `propostas`), seguindo o padrão de `views.py` + `services.py` + `selectors.py` usado em `bancos` (substituindo esse trecho do ADR 0011).
  - O grupo `Supervisor` recebe `contratos.change_contrato` via migration de dados, podendo operar Contratos além de auditá-los.
- **Navegação contextual e leitura:** telas internas passam a exibir breadcrumb enxuto no topo, botões `Cancelar` respeitam a origem (`?next=` ou entidade pai), a listagem de Contratos passa a exibir o Cliente, e valores monetários e telefones seguem formatação brasileira (`R$ 25.000,00`, `(11) 98888-7777`).

## Consequências

- O primeiro atendimento completo (do CPF inédito até a Proposta enviada ao Banco) cai de múltiplas idas e vindas manuais para uma linha contínua sem seleção redundante de Benefício.
- Remover o `<select>` global de Benefícios evita degradação de performance e usabilidade conforme a base de Clientes cresce.
- Estender `formularios/pagina.html` (ADR 0010) para suportar botão secundário de avanço (`Salvar e ...`) e URL de retorno contextual mantém o padrão único de formulários sem duplicar templates.
- Trazer Modalidades para telas + `services.py` elimina a exceção arquitetural registrada no ADR 0011 e garante `_history_user` consistente sem depender do admin.
