# Grafo do Agente de Conciliação Contábil

## Objetivo

O agente é implementado como um grafo utilizando LangGraph. O grafo organiza o fluxo de análise de divergências entre Notas Fiscais, Pedidos de Compra, contratos, aditivos e histórico de negociações, garantindo rastreabilidade, recuperação de estado, recuperação documental, utilização de memória e intervenção humana quando necessário.

A escolha por uma arquitetura baseada em grafo permite representar explicitamente decisões, bifurcações, interrupções e retomadas, evitando fluxos rígidos de execução e tornando o comportamento do sistema observável e auditável.

---

# Visão Geral do Grafo

```text
START
  |
  v
Receber Solicitação
  |
  v
Classificar Solicitação
  |
  v
Extrair Entidades
  |
  v
Validar Dados
  |
  +--------------------+
  |                    |
  | Dados insuficientes|
  |                    |
  v                    |
Solicitar Complemento  |
  |                    |
  +--------------------+
  |
  v
Consultar ERP
  |
  v
Recuperar Conhecimento (RAG)
  |
  v
Consultar Memória
  |
  v
Analisar Divergência
  |
  +-------------------+
  |                   |
  | Aprovação Humana? |
  |                   |
  +---------+---------+
            |
      +-----+-----+
      |           |
     Sim         Não
      |           |
      v           v
Checkpoint     Gerar
e Pausa        Resposta
(HITL)         Final
      |           |
      +-----+-----+
            |
            v
Registrar Caso
            |
            v
END
```

---

# Nós do Grafo

## 1. Receber Solicitação

### Responsabilidade

Receber a entrada em linguagem natural enviada pelo usuário.

### Entrada

```text
Existe justificativa para a divergência da NF 45887?
```

### Saída

```json
{
  "texto": "...",
  "user_id": "...",
  "thread_id": "..."
}
```

---

## 2. Classificar Solicitação

### Responsabilidade

Determinar o tipo de solicitação recebida.

### Possíveis Classes

```text
consulta_divergencia
validacao_contrato
consulta_historico
aprovacao_manual
fora_do_escopo
```

### Padrão Utilizado

Router Pattern

O nó decide qual caminho seguir no restante da execução.

---

## 3. Extrair Entidades

### Responsabilidade

Identificar os elementos relevantes do domínio.

### Entidades

- Nota Fiscal
- Pedido de Compra
- Contrato
- Fornecedor
- Valor
- Data

### Exemplo

Entrada:

```text
Existe justificativa para a NF 45887 do fornecedor XYZ?
```

Saída:

```json
{
  "nota_fiscal": "45887",
  "fornecedor": "XYZ"
}
```

---

## 4. Validar Dados

### Responsabilidade

Determinar se existem informações suficientes para prosseguir.

### Possíveis Resultados

#### Dados suficientes

Fluxo continua.

#### Dados insuficientes

Fluxo direcionado para solicitação de complementação.

---

## 5. Solicitar Complemento

### Responsabilidade

Solicitar informações adicionais quando a entrada não possui informações suficientes.

### Exemplo

Entrada:

```text
Existe uma divergência.
```

Saída:

```text
Informe o número da Nota Fiscal,
Pedido de Compra ou fornecedor.
```

### Padrão Utilizado

Human Interaction Pattern

O agente interrompe o fluxo aguardando nova informação.

---

## 6. Consultar ERP

### Responsabilidade

Recuperar informações estruturadas.

### Dados Consultados

- Nota Fiscal
- Pedido de Compra
- Valor faturado
- Valor contratado
- Fornecedor
- Centro de custo
- Status de aprovação

### Justificativa

Esses dados possuem identificadores exatos e não devem ser recuperados por similaridade vetorial.

### Ferramenta

ERP corporativo.

---

## 7. Recuperar Conhecimento (RAG)

### Responsabilidade

Recuperar evidências documentais.

### Fontes

- Contratos
- Aditivos
- Histórico de e-mails
- Políticas internas
- Procedimentos

### Resultado

Conjunto de documentos relevantes para análise.

### Padrão Utilizado

Retriever Pattern

---

## 8. Consultar Memória

### Responsabilidade

Buscar conhecimento acumulado em execuções anteriores.

### Memórias Consultadas

#### Episódica

Casos semelhantes já resolvidos.

#### Semântica

Regras estruturadas.

#### Procedural

Instruções operacionais permanentes.

### Exemplo

```text
Fornecedor XYZ já apresentou divergência semelhante
em março de 2026.
```

---

## 9. Analisar Divergência

### Responsabilidade

Consolidar todas as evidências.

### Entradas

- Dados ERP
- Documentos recuperados
- Casos anteriores
- Regras procedurais

### Perguntas Respondidas

```text
Há divergência?

A divergência é justificável?

Existe conflito documental?

Existe evidência suficiente?

Necessita aprovação humana?
```

### Resultado

Objeto estruturado com a conclusão da análise.

---

## 10. Aprovação Humana

### Responsabilidade

Encaminhar casos que exigem intervenção humana.

### Critérios

#### Divergência financeira elevada

#### Ausência de evidências

#### Conflito documental

#### Exceções fora das regras conhecidas

### Padrão Utilizado

Human-in-the-Loop (HITL)

---

## 11. Gerar Resposta Final

### Responsabilidade

Produzir o objeto de resposta validado.

### Estrutura

```json
{
  "resultado": "...",
  "fonte": [],
  "suficiente": true,
  "justificativa": "..."
}
```

### Regras

- toda resposta deve citar fontes;
- toda resposta deve indicar suficiência;
- toda conclusão deve ser explicável.

---

## 12. Registrar Caso

### Responsabilidade

Persistir informações relevantes para auditoria e memória.

### Registros

- execução;
- documentos utilizados;
- decisão tomada;
- intervenção humana;
- timestamps;
- justificativas.

### Destino

- logs;
- memória episódica;
- checkpoint.

---

# Arestas do Grafo

## Fluxo Principal

```text
Receber Solicitação
    ↓
Classificar Solicitação
    ↓
Extrair Entidades
    ↓
Validar Dados
    ↓
Consultar ERP
    ↓
Recuperar Conhecimento
    ↓
Consultar Memória
    ↓
Analisar Divergência
    ↓
Gerar Resposta
```

---

## Fluxo de Complementação

```text
Validar Dados
    ↓
Dados insuficientes
    ↓
Solicitar Complemento
    ↓
Retornar para Validação
```

---

## Fluxo de Aprovação

```text
Analisar Divergência
    ↓
Necessita aprovação
    ↓
Checkpoint
    ↓
Aguardar humano
    ↓
Retomar execução
    ↓
Gerar Resposta
```

---

# Estado Compartilhado

O estado é transportado ao longo de todo o grafo.

## Campos Principais

```python
State = {
    "thread_id",
    "user_id",
    "solicitacao",
    "entidades",
    "dados_erp",
    "documentos_rag",
    "memoria",
    "analise",
    "aprovacao",
    "resposta"
}
```

---

# Checkpoint

## Objetivo

Permitir retomada segura após interrupções.

## Informações Persistidas

- etapa atual;
- entidades identificadas;
- consultas realizadas;
- documentos recuperados;
- análise parcial;
- pendências humanas.

## Benefícios

- retomada sem repetir ações;
- tolerância a falhas;
- auditoria;
- depuração.

---

# Padrões de LangGraph Utilizados

| Padrão | Aplicação |
|----------|-----------|
| Router | Classificação da solicitação |
| Tool Calling | Consulta ao ERP e RAG |
| Retrieval | Recuperação documental |
| Checkpointing | Persistência de estado |
| Human-in-the-Loop | Aprovações financeiras |
| StateGraph | Compartilhamento de contexto |
| Memory Integration | Recuperação de experiências anteriores |

---

# Tratamento de Falhas

## Dados insuficientes

Retornar para coleta de informações.

---

## Recuperação vazia

Retornar resposta com suficiência negativa.

---

## Falha de ferramenta

Registrar erro e interromper execução.

---

## Aprovação não respondida

Manter checkpoint e aguardar resposta humana.

---

# Justificativa da Topologia

A topologia foi projetada em função do processo real de conciliação financeira.

O fluxo exige:

1. consulta de informações estruturadas;
2. recuperação documental;
3. recuperação de experiências anteriores;
4. tomada de decisão baseada em evidências;
5. aprovação humana para exceções.

Essas características tornam inadequado um fluxo linear simples. O modelo em grafo permite representar explicitamente os ciclos de complementação de dados, a recuperação de conhecimento, os pontos de parada e as decisões condicionais que ocorrem naturalmente durante a análise de divergências financeiras.