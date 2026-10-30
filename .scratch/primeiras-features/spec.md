Status: ready-for-agent

# Primeiras features: base de acesso, Clientes e Benefícios, Bancos, Propostas e Contratos

## Problem Statement

O Correspondente que intermedeia crédito consignado do INSS hoje não tem um sistema próprio. O Operador atende o Cliente, consulta a margem do Benefício em outro lugar, envia a Proposta ao Banco e acompanha a resposta sem registro central. Não há como saber quem digitou o quê, em que etapa está cada Proposta, se a parcela cabe na margem, nem recuperar o histórico de um Cliente. Erros de digitação, propostas duplicadas e perda de acompanhamento são comuns.

## Solution

Um backoffice web, usado apenas pelos Operadores e Supervisores do Correspondente, onde:

- o Operador cadastra e busca Clientes e seus Benefícios, registrando a Margem consignável consultada;
- o Supervisor mantém o cadastro de Bancos;
- o Operador digita a Proposta de empréstimo consignado novo sobre um Benefício para um Banco, envia ao Banco e acompanha as etapas à mão;
- ao formalizar a Proposta, o sistema cria o Contrato, que o Operador acompanha até a quitação;
- tudo exige login, cada ação exige a permissão do seu grupo, nada é apagado e toda alteração fica registrada com autor e data.

O sistema não simula parcelas, não integra com o INSS nem com os Bancos, e não calcula comissão.

## User Stories

### Acesso

1. Como Operador, quero entrar com meu usuário e senha, para que só pessoas autorizadas acessem os dados dos Clientes.
2. Como Operador, quero ser levado à tela de login ao abrir qualquer endereço sem estar autenticado, para que nenhum dado apareça sem identificação.
3. Como Operador, quero sair do sistema, para que ninguém use minha sessão em um computador compartilhado.
4. Como Supervisor, quero que Operadores e Supervisores tenham permissões distintas, para que ações sensíveis fiquem restritas.
5. Como administrador do sistema, quero que os grupos Operador e Supervisor já existam com suas permissões depois da instalação, para que eu só precise criar os usuários e escolher o grupo.
6. Como Operador, quero ver uma mensagem clara quando tento uma ação sem permissão, para que eu saiba procurar um Supervisor.

### Clientes

7. Como Operador, quero cadastrar um Cliente com nome, CPF, data de nascimento, telefone e e-mail opcional, para que ele fique registrado para propostas futuras.
8. Como Operador, quero que o sistema recuse CPF com formato ou dígitos inválidos, para evitar erro de digitação.
9. Como Operador, quero digitar o CPF com ou sem pontos e traço, para que eu não precise me preocupar com a formatação.
10. Como Operador, quero que, ao cadastrar um CPF já existente, o sistema me leve à ficha do Cliente existente avisando que ele já está cadastrado, para não criar duplicidade.
11. Como Operador, quero buscar Clientes num único campo por CPF, parte do nome ou número do Benefício, para achar rápido quem estou atendendo.
12. Como Operador, quero ver na lista de Clientes o CPF parcialmente oculto, para que o dado pessoal não fique exposto à toa.
13. Como Operador, quero ver o CPF completo na ficha do Cliente, para conferir a identidade durante o atendimento.
14. Como Operador, quero editar os dados de contato e o nome do Cliente, para corrigir erros e manter o telefone atualizado.
15. Como Operador, quero ver na ficha do Cliente seus Benefícios, Propostas e Contratos, para ter o panorama completo em uma tela.
16. Como Operador, quero inativar um Cliente que não deve mais aparecer nas buscas, para manter a base limpa sem perder o histórico.
17. Como Operador, quero reativar um Cliente inativado, para voltar a atendê-lo.
18. Como Supervisor, quero consultar o histórico de alterações de um Cliente com autor e data, para auditar mudanças.

### Benefícios e Margem

19. Como Operador, quero cadastrar um Benefício para um Cliente com número e espécie (aposentadoria ou pensão), para vincular propostas a ele.
20. Como Operador, quero cadastrar mais de um Benefício para o mesmo Cliente, para atender quem tem aposentadoria e pensão.
21. Como Operador, quero registrar a Margem consignável do Benefício junto com a data da consulta, para que a Proposta seja validada contra um valor conhecido.
22. Como Operador, quero ver a margem atual e a data da consulta na ficha do Benefício, para saber se preciso consultar de novo.
23. Como Operador, quero ver o histórico de margens digitadas de um Benefício, para entender como ela evoluiu.
24. Como Operador, quero ser avisado quando a margem tem mais de 30 dias, para pedir uma nova consulta.
25. Como Operador, quero inativar um Benefício que não vale mais, para que ele não seja escolhido em novas Propostas.
26. Como Operador, quero que o mesmo número de Benefício não seja cadastrado duas vezes, para evitar registros conflitantes.

### Bancos

27. Como Supervisor, quero cadastrar um Banco com nome e código, para que as Propostas possam ser enviadas a ele.
28. Como Supervisor, quero editar os dados de um Banco, para corrigir informações.
29. Como Supervisor, quero inativar um Banco com o qual o Correspondente deixou de trabalhar, para que ele não apareça em novas Propostas.
30. Como Operador, quero escolher apenas entre Bancos ativos ao digitar uma Proposta, para não enviar para quem não atendemos mais.
31. Como Operador, quero ver a lista de Bancos, para saber com quem trabalhamos, sem poder alterá-la.
32. Como Supervisor, quero que não existam dois Bancos com o mesmo código, para evitar duplicidade.

### Propostas

33. Como Operador, quero digitar uma Proposta escolhendo o Benefício, o Banco, o valor, o prazo, a parcela e a taxa oferecidos, para registrar o que o Banco ofereceu.
34. Como Operador, quero que a Proposta nasça no status Digitada, para saber que ainda não foi enviada.
35. Como Operador, quero editar livremente as condições de uma Proposta Digitada, para corrigir erros antes de enviar.
36. Como Operador, quero enviar a Proposta ao Banco marcando-a como Enviada ao Banco, para registrar que o pedido foi feito.
37. Como Operador, quero que o envio seja bloqueado quando a parcela for maior que a margem do Benefício, para não mandar uma Proposta inviável.
38. Como Operador, quero ver uma mensagem clara dizendo a parcela e a margem quando o envio é bloqueado, para saber o que corrigir.
39. Como Operador, quero ser avisado quando a margem tem mais de 30 dias ao enviar e poder confirmar para prosseguir, para decidir se vale reconsultar.
40. Como Operador, quero que as condições fiquem travadas depois do envio, para que a Proposta enviada seja a mesma que o Banco recebeu.
41. Como Operador, quero editar observações da Proposta em qualquer etapa, para anotar o que o Banco ou o Cliente disse.
42. Como Operador, quero marcar a Proposta como Em análise quando o Banco confirmar o recebimento, para acompanhar o andamento.
43. Como Operador, quero marcar a Proposta como Aprovada quando o Banco aprovar, para seguir à formalização.
44. Como Operador, quero marcar a Proposta como Recusada quando o Banco negar, para encerrar o acompanhamento.
45. Como Operador, quero marcar a Proposta como Formalizada quando o Cliente assinar, para que o Contrato seja criado.
46. Como Operador, quero que o status só avance na ordem, sem pular etapas, para manter o processo confiável.
47. Como Operador, quero cancelar uma Proposta até Em análise informando o motivo, para registrar a desistência.
48. Como Supervisor, quero cancelar uma Proposta já Aprovada informando o motivo, para que cancelamentos tardios passem por responsável.
49. Como Operador, quero que Propostas Recusadas ou Canceladas não possam ser reabertas, para preservar o registro do que aconteceu.
50. Como Operador, quero ver o motivo do cancelamento na Proposta, para entender por que ela terminou.
51. Como Operador, quero ver qual Operador digitou a Proposta, para saber com quem falar sobre ela.
52. Como Operador, quero listar as Propostas filtrando por status, Banco e Cliente, para acompanhar o que está em aberto.
53. Como Supervisor, quero consultar o histórico de uma Proposta com quem mudou cada status e quando, para auditar o andamento.
54. Como Operador, quero ver todas as Propostas da equipe, e não só as minhas, para cobrir um colega.

### Contratos

55. Como Operador, quero que o Contrato seja criado automaticamente ao formalizar a Proposta, com os valores dela, para não digitar duas vezes.
56. Como Operador, quero que cada Contrato tenha uma única Proposta de origem, para rastrear sua história.
57. Como Operador, quero marcar o Contrato como Averbado quando o INSS confirmar o desconto, para acompanhar a efetivação.
58. Como Operador, quero marcar o Contrato como Pago quando o Banco liberar o dinheiro ao Cliente, para registrar a conclusão da operação.
59. Como Operador, quero marcar o Contrato como Quitado quando terminar ou for pago antecipadamente, para encerrá-lo.
60. Como Operador, quero marcar o Contrato como Cancelado quando a averbação ou o pagamento falhar, informando o motivo, para registrar o problema.
61. Como Operador, quero listar os Contratos por status e por Cliente, para acompanhar a carteira.
62. Como Supervisor, quero consultar o histórico do Contrato com autor e data de cada mudança, para auditar.

### Transversais

63. Como Supervisor, quero que nenhum Cliente, Benefício, Banco, Proposta ou Contrato possa ser apagado, só inativado ou cancelado, para que o histórico fique completo.
64. Como Supervisor, quero que valores de dinheiro e taxa nunca sofram arredondamento de ponto flutuante, para que os números batam com os do Banco.
65. Como Operador, quero que todas as telas e mensagens estejam em português, para trabalhar com clareza.
66. Como Operador, quero que as listas e formulários se atualizem sem recarregar a página inteira, para trabalhar com agilidade.

## Implementation Decisions

**Apps e ordem**
- Apps em português sem acento, na ordem de entrega: acesso (já previsto no ADR-0005), clientes (com Benefícios e Margem), bancos, propostas e contratos.
- Cada app segue as camadas do ADR-0003 e as convenções do ADR-0006, hoje Proposto e a ser aceito junto com este spec.

**Acesso**
- Usuário customizado definido antes da primeira migration.
- Login obrigatório em todo o sistema; só a tela de login e os estáticos são públicos.
- Dois grupos, Operador e Supervisor, criados por migration de dados com as permissões nativas do Django. O Operador cadastra e edita Clientes, Benefícios e Propostas e acompanha Contratos. O Supervisor tem tudo do Operador e mais gestão de Bancos e cancelamento de Proposta Aprovada.
- Operadores veem todos os registros; não há carteira por Operador.

**Cliente**
- Pessoa física com nome, CPF, data de nascimento, telefone e e-mail opcional.
- CPF único, guardado só com dígitos, validado por dígitos verificadores, exibido com máscara.
- Cadastro de CPF existente leva à ficha existente, sem erro seco.
- Listas mostram CPF parcialmente oculto; só a ficha mostra o completo. CPF não vai para logs.
- Inativação em vez de exclusão.

**Benefício**
- Pertence a um Cliente; tem número único, espécie (aposentadoria ou pensão) e situação ativa ou inativa.
- A Margem consignável é registrada como valor com a data da consulta; cada nova digitação gera um registro histórico. A margem vigente é a mais recente.
- Margem com mais de 30 dias é considerada antiga.

**Banco**
- Nome e código únicos, ativo ou inativo. Só Supervisor cria, edita e inativa; Operador só lê.

**Proposta**
- Refere-se a um Benefício e a um Banco ativos; guarda valor, prazo, parcela e taxa informados pelo Operador (o sistema não calcula nada), observações, o Operador que a digitou e, quando houver, o motivo de recusa ou cancelamento.
- Status: Digitada, Enviada ao Banco, Em análise, Aprovada, Formalizada, Recusada e Cancelada. As transições são feitas pelo Operador à mão e avançam só na ordem.
- Recusada e Cancelada são finais e valem de qualquer etapa antes de Formalizada; cancelar exige motivo. Cancelar depois de Aprovada exige o grupo Supervisor.
- Enviar ao Banco é bloqueado se a parcela for maior que a margem vigente do Benefício. Margem antiga só avisa e exige confirmação do Operador.
- Condições (Banco, Benefício, valor, prazo, parcela, taxa) editáveis só em Digitada. Observações editáveis em qualquer etapa.
- Todas as regras acima são do service; a view só traduz o resultado e os erros de negócio para a tela.

**Contrato**
- Criado automaticamente, na mesma transação, ao formalizar a Proposta, copiando seus valores. Cada Contrato tem exatamente uma Proposta de origem.
- Status: Averbado, Pago, Quitado e Cancelado, mudados à mão pelo Operador. Cancelar exige motivo. Não há controle de parcelas.

**Dados e auditoria**
- Valores monetários e taxas em campos decimais, nunca ponto flutuante.
- Histórico de alterações em Cliente, Benefício, Banco, Proposta e Contrato, com autor e data.
- Nada é apagado; usa-se inativação ou cancelamento.

**Interface**
- Páginas renderizadas no servidor com Bootstrap para a estilização e HTMX para atualizações parciais (buscas, filtros, mudança de status), com fragmentos de template reaproveitados pela mesma view.
- Textos em português com acento; identificadores do domínio em português sem acento.

## Testing Decisions

- **Um bom teste** verifica o comportamento observável: o que o service ou selector devolve, o que ele grava e qual erro de negócio levanta. Ele não verifica como o código faz isso por dentro.
- **Seam principal:** as funções públicas de services e selectors de cada app, testadas contra o banco real (SQLite), sem mock de ORM e sem HTTP. Cobre CPF único e inválido, busca por CPF/nome/número do Benefício, histórico de margem, bloqueio de parcela maior que a margem, aviso de margem antiga, travamento de condições, ordem e finais dos status, motivo obrigatório, cancelamento tardio só por Supervisor, criação automática do Contrato e transições do Contrato.
- **Seam secundário, enxuto:** as views, só com o fluxo feliz e as permissões (login obrigatório, Operador contra Supervisor).
- Bancos de teste montados com factories; testes organizados por app, um arquivo por camada.
- **Prior art:** não há testes no projeto ainda; este spec inaugura o padrão do ADR-0006 (pytest-django e factory_boy).

## Out of Scope

- Simulação ou cálculo de parcelas, juros e CET.
- Integração com o INSS (consulta de margem, averbação) e com os Bancos.
- Refinanciamento, portabilidade e cartão consignado.
- Comissão do Correspondente.
- Convênio, outros consignantes (órgãos públicos, empresas) e matrícula.
- Controle de parcelas do Contrato.
- Carteira de Clientes por Operador.
- Endereço, documentos e dados bancários do Cliente.
- Criptografia de campos de dados pessoais (decisão adiada no ADR-0005).
- API REST, SPA e interface para clientes finais.
- Relatórios e dashboards.
- Notificações a Clientes por e-mail ou SMS.
- Exclusão de qualquer registro.

## Further Notes

- Vocabulário: usar sempre os termos do `GLOSSARY.md` (Cliente, Benefício, Margem consignável, Correspondente, Operador, Banco, Proposta, Contrato). Evitar beneficiário, vínculo, matrícula, financeira e simulação.
- O ADR-0006 está Proposto e vale como convenção deste trabalho; deve ser aceito pelo usuário antes de implementar.
- O ADR-0005 avisa que dados pessoais ficam sem criptografia por ora; revisar antes de usar dados reais em produção.
- Próximo passo: `/to-tickets` para quebrar este spec em tickets verticais, na ordem acesso, Clientes e Benefícios, Bancos, Propostas e Contratos.
