# Arquitetura do Agente de Conciliação Contábil

## Objetivo

O Agente de Conciliação Contábil tem como objetivo apoiar o processo Procure-to-Pay (P2P) na análise de divergências entre Notas Fiscais (NF), Pedidos de Compra (PO), contratos, aditivos contratuais e histórico de negociações.

O sistema não substitui o processo de aprovação financeira. Sua função é investigar, justificar, documentar e recomendar ações com base em evidências recuperadas de sistemas corporativos e de uma base de conhecimento especializada.

---

# Visão Geral da Arquitetura

```text
┌───────────────────────────┐
│ Usuário                   │
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│ Interpretação da Solicitação │
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│ Extração de Entidades     │
│ NF / PO / Contrato        │
└─────────────┬─────────────┘
              │
     ┌────────┴────────┐
     ▼                 ▼
┌──────────┐   ┌────────────────┐
│ ERP      │   │ RAG            │
│ Consulta │   │ Recuperação    │
│ Dados    │   │ Documental     │
└──────────┘   └────────────────┘
     │                 │
     └────────┬────────┘
              ▼
┌───────────────────────────┐
│ Análise da Divergência    │
└─────────────┬─────────────┘
              │
     ┌────────┴─────────┐
     ▼                  ▼
 Necessita           Não necessita
 aprovação           aprovação
 humana                humana
     ▼                  ▼
┌──────────┐     ┌────────────┐
│ HITL     │     │ Resposta   │
│ Aprovação│     │ Final      │
└────┬─────┘     └─────┬──────┘
     │                 │
     └──────┬──────────┘
            ▼
┌───────────────────────────┐
│ Registro da Execução      │
│ Memória e Auditoria       │
└───────────────────────────┘
```

---

# Componentes da Arquitetura

## Camada de Entrada

Responsável por receber solicitações em linguagem natural provenientes dos usuários.

Exemplos:

```text
Existe justificativa para a divergência entre a NF 45887 e o pedido 450019283?
```

```text
O fornecedor informou reajuste por e-mail. Posso aprovar a nota?
```

A entrada é composta por:

- texto livre;
- identificador do usuário;
- identificador da sessão;
- identificador da execução (`thread_id`);
- data e hora da solicitação.

---

## Camada de Interpretação

Responsável por compreender a intenção do usuário.

Funções:

- identificar o objetivo da solicitação;
- classificar a categoria do pedido;
- detectar informações ausentes;
- decidir quais ferramentas devem ser utilizadas.

Saídas possíveis:

```text
consulta_divergencia
```

```text
validacao_contrato
```

```text
consulta_historico
```

```text
fora_do_escopo
```

---

## Camada de Extração

Após identificar a intenção, o sistema extrai os identificadores necessários para investigação.

Entidades relevantes:

| Entidade | Exemplo |
|-----------|----------|
| Nota Fiscal | 45887 |
| Pedido de Compra | 450019283 |
| Contrato | CT-014 |
| Aditivo | AD-03 |
| Fornecedor | Empresa XYZ |
| Valor | R$ 1.250,00 |

A saída desta etapa é estruturada e utilizada pelas ferramentas posteriores.

---

# Ferramentas

O agente opera por meio de ferramentas especializadas.

## Consulta ao ERP

Responsável por recuperar dados estruturados.

Informações recuperadas:

- número da NF;
- valor da NF;
- valor do pedido;
- centro de custo;
- fornecedor;
- status da aprovação;
- histórico de pagamentos.

Motivo da consulta estruturada:

Esses dados possuem chave exata e não devem ser recuperados por similaridade semântica.

---

## Recuperação RAG

Responsável por localizar contexto e justificativas.

Fontes:

- contratos;
- aditivos;
- políticas internas;
- procedimentos financeiros;
- histórico de e-mails.

Utilização:

```text
Existe aditivo que explique a divergência?

Há acordo registrado em e-mail?

A política interna permite essa exceção?
```

---

## Consulta de Memória

Responsável por recuperar experiências anteriores.

Busca:

- casos similares;
- justificativas já aprovadas;
- exceções recorrentes;
- decisões anteriores.

Objetivo:

Evitar que divergências semelhantes sejam analisadas repetidamente como se fossem inéditas.

---

# Processo de Tomada de Decisão

Após recuperar informações do ERP, do RAG e da memória episódica, o agente realiza uma análise consolidada.

A análise busca responder:

1. Existe divergência?
2. A divergência possui justificativa?
3. Existe conflito entre documentos?
4. Há evidência suficiente?
5. É necessária aprovação humana?

---

# Integração com RAG

A recuperação documental segue as decisões estabelecidas em `docs/rag.md`.

São indexados:

- contratos;
- aditivos;
- políticas;
- procedimentos;
- histórico de negociações.

Não são indexados:

- valores atuais;
- status de documentos;
- informações operacionais do ERP.

Esses elementos permanecem sob consulta estruturada.

---

# Integração com Memória

A arquitetura utiliza dois níveis de memória.

## Curto Prazo

Mantida durante a execução.

Contém:

- contexto atual;
- documentos recuperados;
- consultas realizadas;
- resultados intermediários;
- estado do workflow.

Persistida por checkpoint.

---

## Longo Prazo

Compartilhada entre execuções.

Dividida em:

### Memória Episódica

Casos anteriores.

Exemplo:

```text
Fornecedor XYZ teve divergência semelhante em março.
```

### Memória Semântica

Conhecimento consolidado.

Exemplo:

```text
Limite atual de tolerância: 1,5%.
```

### Memória Procedural

Instruções operacionais permanentes.

Exemplo:

```text
Toda divergência acima de determinado valor exige aprovação humana.
```

---

# Human-in-the-Loop

O sistema não possui autonomia irrestrita.

Existem situações que obrigam intervenção humana.

## Casos obrigatórios

### Divergência acima do limite financeiro

Exemplo:

```text
Diferença superior ao limite definido na política financeira.
```

### Evidência insuficiente

Exemplo:

```text
Não existe contrato nem histórico de negociação recuperável.
```

### Conflito documental

Exemplo:

```text
Contrato e aditivo apresentam regras incompatíveis.
```

### Exceções não previstas

Exemplo:

```text
Situação jamais registrada anteriormente.
```

Nessas situações o fluxo é interrompido até decisão humana.

---

# Ponto de Interrupção

O agente utiliza um mecanismo de pausa controlada.

```text
Análise
   ↓
Necessita aprovação?
   ↓
SIM
   ↓
Checkpoint
   ↓
Aguardar humano
   ↓
Retomar execução
```

Benefícios:

- evita perda de contexto;
- impede duplicação de ações;
- mantém rastreabilidade;
- permite auditoria.

---

# Critérios de Encerramento

Uma execução termina quando uma das situações abaixo ocorre.

## Sucesso

O agente encontrou evidências suficientes e produziu uma resposta fundamentada.

## Recusa

Não existem evidências suficientes para responder.

## Escalonamento

O caso foi transferido para aprovação humana.

## Erro operacional

Ferramenta indisponível ou recuperação incompleta.

---

# Arquitetura de Auditoria

Todas as execuções produzem registros auditáveis.

Elementos registrados:

- entrada recebida;
- entidades extraídas;
- consultas realizadas;
- documentos recuperados;
- fontes utilizadas;
- decisão final;
- participação humana;
- timestamp;
- identificador da execução.

Esses registros permitem:

- reprodução de casos;
- investigação de erros;
- validação de conformidade;
- rastreamento de decisões.

---

# Padrões Arquiteturais Utilizados

| Padrão | Aplicação |
|----------|-------------|
| Agent + Tools | Consulta ao ERP, RAG e memória |
| Retrieval Augmented Generation (RAG) | Recuperação documental |
| Human-in-the-Loop | Aprovação financeira |
| Persistent Memory | Aprendizado entre execuções |
| Checkpointing | Retomada de fluxos interrompidos |
| Structured Output | Contrato de resposta |
| Graph Workflow | Orquestração do fluxo em LangGraph |

---

# Justificativa da Arquitetura

A arquitetura escolhida reflete a natureza do domínio financeiro.

A maior parte das decisões depende de documentos corporativos, histórico de negociações e regras internas que não fazem parte do conhecimento do modelo.

Por esse motivo, o sistema foi projetado para combinar:

1. Consulta estruturada aos sistemas corporativos;
2. Recuperação documental via RAG;
3. Memória de casos anteriores;
4. Participação humana quando necessário.

O resultado é um agente capaz de produzir análises fundamentadas, rastreáveis e auditáveis, mantendo conformidade com os controles financeiros e reduzindo o esforço operacional do processo de conciliação.