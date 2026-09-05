# Trabalho da disciplina — Parte 1: Escolher e provar o terreno
## Exercício 4 — A escolha do case

---

## 1. O case — indústria e problema

### O setor
**Setor Financeiro / Controladoria e Contas a Pagar (Procure-to-Pay)**.

### O problema em uma frase
**Tratamento autônomo de divergências e falhas de conciliação entre notas fiscais emitidas por fornecedores e pedidos de compra internos cadastrados no ERP.**

### O contexto de onde o problema vive

*   **O que acontece hoje sem o sistema:** Atualmente, quando uma nota fiscal (NF) é emitida contra a empresa, o Assistente de Contas a Pagar precisa abrir manualmente o ERP, buscar o Pedido de Compra (PO) correspondente e conferir item por item (preço unitário, quantidade, impostos e descrição). Sem o agente, qualquer divergência mínima de centavos, frete não previsto ou arredondamento de imposto trava o processo. O assistente precisa abrir o histórico de e-mails ou acionar a área de compras para descobrir se a alteração foi acordada verbalmente ou via aditivo contratual. Esse processo manual de investigação e validação consome cerca de **25 minutos por nota divergente**.
*   **As regras do domínio:** 
    *   **Tolerância:** Divergências de valor total de até 1.5% (limitadas ao teto de R$ 50,00) podem ser aceitas automaticamente via nota de ajuste contábil, sem necessidade de estorno.
    *   **Prazos:** Notas fiscais de serviços precisam ser retidas e lançadas em até 5 dias úteis antes do vencimento para evitar multas de atraso de fornecedores.
    *   **Políticas de Impostos:** Retenções na fonte (ISS, IRRF, CSLL, PIS/COFINS) precisam bater exatamente com o código de serviço municipal e a legislação vigente da cidade do prestador.
*   **O que dá errado hoje (Casos difíceis):** 
    1.  **Divergência de Nomenclatura:** O fornecedor emite a NF descrevendo o item como *"Manutenção de Ativos de TI"*, mas no pedido de compra interno o item foi cadastrado como *"Suporte Técnico em Infraestrutura"*, fazendo com que as regras fixas do ERP rejeitem a nota.
    2.  **Inclusão de Custos Ocultos:** O fornecedor adiciona valores de frete, seguro ou taxas administrativas diretamente no corpo da NF que não estavam previstos no Pedido de Compra inicial.
    3.  **Divergência de Alíquota:** Alterações repentinas ou erros na alíquota de ISS retido por parte do fornecedor, gerando incompatibilidade com o cadastro fiscal da empresa.

### O que a indústria já faz com agentes nesse problema

Grandes empresas do setor de bens de consumo, como a **Danone** (em parceria com a Microsoft), e consultorias globais de automação implementaram **Agentes Autônomos de Conciliação Contábil** para resolver o gargalo do ciclo *Procure-to-Pay*.

*   **O que a empresa fez e números divulgados:** Os agentes capturam a Nota Fiscal direto do e-mail ou portal da prefeitura, extraem os dados via LLMs de visão e realizam o cruzamento de linhas de itens com o ERP. Em casos de divergência, o agente busca ativamente aditivos contratuais e trocas de e-mails históricos. O sistema reduziu o tempo de processamento de notas de **dias para poucos minutos**, mitigando o risco de pagamentos duplicados ou com valores incorretos.
*   **Padrão de arquitetura provável:** Orquestração de Agente com **RAG Duplo (Retrieval-Augmented Generation)** operando em bancos de dados vetoriais para expansão de sinônimos contextuais de produtos/serviços, aliado a ferramentas de **Tool Calling (APIs HTTP)** com estado explícito para consultar logs de compras e contratos no ERP.
*   **O que a divulgação não conta:** Os relatórios não explicitam qual era a linha de base exata de erros humanos antes da IA, como os casos altamente ambíguos ou fraudes sofisticadas são filtrados na triagem, e qual é o custo mensal de tokens gerado pelas múltiplas chamadas que o agente faz ao analisar documentos longos (contratos em PDF).

---

## 2. Os usuários, e como será a interação

### Tabela de perfis

| Perfil | O que ele quer | O que ele sabe | O que ele **pode** fazer |
| :--- | :--- | :--- | :--- |
| **Assistente de Contas a Pagar** *(Usuário Principal)* | Conciliar e liberar o pagamento das notas que estão travadas o mais rápido possível. | Conhece o fluxo operacional interno e o ERP; não conhece programação de IA. | Aprova notas com divergências justificadas pelo agente, rejeita notas inválidas, inicia disputas formais com fornecedores. |
| **Fornecedor / Emitente** | Receber o pagamento do serviço/produto no prazo combinado, sem atrasos por burocracia. | Conhece apenas os dados da nota que emitiu e o contrato comercial que fechou. | Envia justificativas textuais, anexa comprovantes, aceita ou recusa propostas de refaturamento. |
| **Gerente Financeiro** | Garantir conformidade fiscal (compliance), evitar multas por atraso e auditar custos operacionais. | Conhece as regras macro de governança da empresa e metas de orçamento. | Aprova pagamentos de notas divergentes que superam a alçada financeira do assistente; lê relatórios consolidados. |

*   **Usuário Principal:** **Assistente de Contas a Pagar**. O sistema é desenhado para atuar como seu copiloto de investigação detalhada.

### Como será a interação

A interação ocorrerá por meio de uma interface de **Chat incorporada ao painel de conciliação do ERP** (ou via terminal na fase piloto). 
*   **Quem começa:** O **sistema procura o usuário de forma proativa** sempre que uma nota fiscal enviada para processamento falha na validação automática de regras rígidas do ERP.
*   **Média de trocas:** Entre **2 e 3 interações** no chat. 
*   **O que o sistema devolve:** O agente devolve um **relatório estruturado (JSON renderizado em texto)** apontando os pontos exatos de divergência, acompanhado de uma justificativa contextualizada após ler o contrato ou e-mails, e uma minuta de e-mail pronta para contestação.
*   **Como termina:** O fluxo termina quando o assistente clica em *"Aprovar Lançamento com Ajuste"* ou *"Enviar Contestação ao Fornecedor"*, o que limpa a fila de pendências do dia.

### Diálogo de exemplo

> **Sistema:** "Alerta: Identifiquei uma divergência na NF nº 4590 do fornecedor *TechServices Ltda*. O valor da nota é de R$ 12.500,00, mas o Pedido de Compra (PO-882) indica R$ 11.000,00. Deseja que eu investigue a causa?"
> 
> **Usuário:** "Sim, verifique o motivo dessa diferença."
> 
> **Sistema (após rodar ferramentas de leitura no histórico):** "Investigação concluída. Encontrei uma troca de e-mails em 14/08 entre o gestor de TI e o fornecedor, onde foi aprovado um aditivo emergencial de R$ 1.500,00 para 'horas extras de suporte na migração de servidores'. No entanto, este aditivo não foi atualizado no PO do ERP.
> 
> **O que deseja fazer?**
> 1. [Aprovar Nota] - Eu lanço a nota no ERP e vinculo esta justificativa por texto.
> 2. [Chamar Gestor] - Encaminhar para o gerente atualizar o Pedido de Compra.
> 3. [Redigir Contestação] - Caso você não reconheça o aditivo."
> 
> **Usuário:** "Pode aprovar a nota e anexar o histórico."
> 
> **Sistema:** "Perfeito. Nota Fiscal nº 4590 integrada ao ERP com sucesso sob a justificativa de aditivo contratual de TI. Fila atualizada."

### Complexidade exigida pela disciplina

*   **O que o usuário não informa de primeira:** O usuário não sabe por que o valor está diferente e nem onde procurar o aditivo (se está no contrato mãe, em um e-mail ou se foi erro do fornecedor).
*   **Contradição:** Quando o fornecedor afirma em sua nota que prestou o serviço "X", mas os registros internos do sistema de chamados indicam que o serviço foi cancelado ou não concluído.
*   **Decisão de suficiência:** O agente decide que sabe o suficiente após realizar a varredura completa nas três fontes obrigatórias (Contrato PDF, Banco de Pedidos e Histórico de E-mails). Se houver convergência documental, ele propõe a solução.
*   **Parada e escalonamento humano:** O sistema para e chama o **Gerente Financeiro** se o valor da divergência ultrapassar R$ 5.000,00 ou se o fornecedor não possuir nenhum contrato ativo na base de dados.

---

## 3. Os ganhos esperados

### Por que um agente, e não software comum?

Softwares de ERP tradicionais barram notas divergentes de forma puramente binária (passa ou não passa) através de regras rígidas baseadas em `ifs`. Eles não conseguem interpretar a linguagem natural de uma descrição de nota modificada pelo fornecedor ou ler o contexto de uma conversa por e-mail que autorizou um gasto extra. O problema exige um **agente** porque a resolução depende de **julgamento em tempo de execução**, capacidade de conectar dados não estruturados (e-mails/contratos) e decidir autonomamente se a divergência é legítima ou um erro de faturamento.

### Eixos de ganho

| Eixo | Linha de base (**Medida**) | Alvo | Ganho | Volume |
| :--- | :--- | :--- | :--- | :--- |
| **Tempo por tarefa** | **25 minutos** por nota fiscal com divergência investigada manualmente. | **3 minutos** de análise guiada pelo agente. | **−88%** de tempo despendido por caso. | Média de **40 notas travadas por dia** (800/mês). |
| **Redução de carga** | Fila acumulada de **40 notas diárias** necessitando de intervenção manual humana total. | Apenas **8 notas diárias** escaladas (casos graves acima da alçada). | **−80%** de tickets retidos no backoffice financeiro. | Aplicação direta sobre o volume mensal de conciliação. |


### O ganho para o usuário vs. o ganho do negócio

