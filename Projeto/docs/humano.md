# Human-in-the-Loop (HITL)

## Objetivo

Embora o Agente de Conciliação Contábil seja capaz de analisar divergências utilizando informações provenientes do ERP, documentos recuperados via RAG e memória de casos anteriores, determinadas decisões continuam sendo responsabilidade humana.

O objetivo do Human-in-the-Loop (HITL) é garantir que exceções críticas, situações ambíguas ou decisões com impacto financeiro relevante sejam revisadas por um colaborador autorizado antes da conclusão do processo.

O agente atua como suporte à decisão, não como substituto do processo de governança financeira.

---

# Papel do Humano no Processo

O agente foi projetado para executar atividades de investigação, recuperação de evidências e elaboração de justificativas.

A aprovação final continua sendo responsabilidade humana quando:

- existe risco financeiro significativo;
- há conflito entre documentos;
- não existe evidência suficiente para tomada de decisão automática;
- a situação não está prevista nas políticas existentes.

O objetivo é equilibrar automação e controle.

---

# Pontos de Intervenção Humana

## Aprovação Financeira

O principal ponto de parada ocorre quando a divergência identificada excede os limites definidos pelas políticas da organização.

### Exemplo

```text
Pedido de Compra: R$ 100.000,00

Nota Fiscal: R$ 107.000,00

Diferença: R$ 7.000,00
```

O agente pode localizar justificativas e apresentar evidências, mas a autorização para pagamento permanece sob responsabilidade do aprovador financeiro.

---

## Evidência Insuficiente

Quando o agente não encontra documentação suficiente para justificar ou rejeitar uma divergência.

### Exemplo

```text
Existe divergência entre NF e Pedido,
mas não foram encontrados:

- contratos relevantes;
- aditivos;
- histórico de negociação;
- exceções anteriores similares.
```

Nessa situação o agente não tenta adivinhar uma conclusão.

O caso é encaminhado para avaliação humana.

---

## Conflito Documental

Pode ocorrer quando diferentes fontes apresentam conclusões incompatíveis.

### Exemplo

Contrato:

```text
Não permite reajuste.
```

Aditivo:

```text
Permite reajuste de até 4%.
```

Política interna:

```text
Permite reajuste somente mediante aprovação.
```

Embora todos os documentos sejam relevantes, a decisão final exige interpretação do contexto e validação humana.

---

## Casos Não Catalogados

Ocorrências inéditas ou muito raras.

### Exemplo

```text
Fornecedor internacional.

Moeda diferente.

Regras tributárias especiais.

Não existem casos semelhantes registrados.
```

O agente registra a situação e solicita revisão humana.

---

# Fluxo de Aprovação

## Fluxo Normal

```text
Análise
   ↓
Evidência suficiente?
   ↓
SIM
   ↓
Resposta
```

## Fluxo com Aprovação Humana

```text
Análise
   ↓
Necessita aprovação?
   ↓
SIM
   ↓
Checkpoint
   ↓
Interrupção
   ↓
Aguardando humano
   ↓
Decisão recebida
   ↓
Retomada
   ↓
Resposta final
```

---

# Dados Entregues ao Aprovador

O agente não encaminha documentos brutos sem contexto.

Antes de interromper a execução, ele produz um resumo estruturado.

## Conteúdo do Resumo

### Contexto

Descrição resumida do problema.

### Divergência Encontrada

Diferença identificada pelo sistema.

### Evidências Recuperadas

Documentos relevantes encontrados:

- contratos;
- aditivos;
- e-mails;
- políticas.

### Riscos

Possíveis impactos da decisão.

### Recomendação

Posicionamento sugerido pelo agente.

---

## Exemplo

```text
Contexto:
Divergência identificada entre NF 45887 e
Pedido 450019283.

Evidências:
Aditivo AD-03 prevê reajuste de 4%.

Risco:
Valor excede limite de aprovação automática.

Recomendação:
Aprovar a divergência mediante validação financeira.
```

---

# Interrupção do Grafo

A interrupção ocorre por meio do mecanismo de checkpoint do LangGraph.

Antes da parada são persistidos:

- identificador da execução;
- estado atual do grafo;
- documentos recuperados;
- análises produzidas;
- recomendações geradas;
- pendências da aprovação.

Dessa forma, a execução pode ser retomada exatamente do ponto em que foi interrompida.

---

# Tempo de Espera

A aprovação pode ocorrer minutos ou horas após o início da execução.

Por esse motivo o estado da execução deve ser persistido integralmente.

O sistema não mantém aprovações aguardando apenas em memória temporária.

---

# Aprovação Recebida

Quando a decisão humana é registrada, o grafo é retomado.

## Aprovação

Fluxo:

```text
Humano aprova
        ↓
Registrar decisão
        ↓
Atualizar histórico
        ↓
Concluir execução
```

---

## Rejeição

Fluxo:

```text
Humano rejeita
        ↓
Registrar motivo
        ↓
Encerrar análise
        ↓
Produzir resposta
```

---

## Solicitação de Revisão

Fluxo:

```text
Humano solicita nova análise
        ↓
Retornar para investigação
        ↓
Reexecutar consultas
        ↓
Produzir novo parecer
```

---

# Ausência de Resposta Humana

Nem toda solicitação recebe resposta imediata.

## Comportamento do Sistema

Enquanto não houver decisão:

```text
Status:
Aguardando aprovação humana
```

O caso permanece aberto.

Nenhuma decisão automática é tomada após a interrupção.

---

# Registro para Auditoria

Toda intervenção humana é registrada.

## Informações Registradas

- aprovador;
- data da decisão;
- decisão tomada;
- justificativa;
- caso relacionado;
- documentos utilizados na análise.

---

# Integração com Memória

Decisões humanas representam uma das principais fontes de aprendizado do agente.

Após validação, o caso pode alimentar a memória episódica.

## Exemplo

```text
Fornecedor XYZ

Divergência de reajuste

Aprovada com base em aditivo AD-03
```

Casos semelhantes poderão ser recuperados futuramente durante a análise de novas ocorrências.

A decisão humana não substitui regras formais da organização.

Ela é armazenada como experiência passada, não como política permanente.

---

# O Que o Humano Decide

O humano decide:

- aprovar ou rejeitar exceções;
- interpretar conflitos documentais;
- validar casos inéditos;
- assumir responsabilidades financeiras.

---

# O Que o Humano Não Faz

O humano não executa:

- busca documental;
- recuperação de contratos;
- consultas ao ERP;
- consolidação de evidências;
- comparação entre documentos.

Essas tarefas permanecem automatizadas pelo agente.

---

# Critérios para Acionar Human-in-the-Loop

| Situação | Aciona HITL |
|-----------|-------------|
| Evidência insuficiente | Sim |
| Conflito documental | Sim |
| Exceção não prevista | Sim |
| Divergência financeira relevante | Sim |
| Caso comum e documentado | Não |
| Regra claramente definida | Não |

---

# Benefícios da Estratégia

A utilização de Human-in-the-Loop permite:

- preservar governança financeira;
- manter responsabilidade humana sobre decisões críticas;
- reduzir riscos de automação excessiva;
- aumentar confiança nas análises produzidas;
- transformar o agente em ferramenta de apoio à decisão e não em mecanismo autônomo de aprovação.

Essa abordagem é compatível com os requisitos de auditoria, rastreabilidade e conformidade normalmente exigidos em processos financeiros e de contas a pagar.