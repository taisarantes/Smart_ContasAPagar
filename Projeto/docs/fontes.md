# Fontes de Dados

## Objetivo

Este documento descreve todas as fontes de informação utilizadas pelo Agente de Conciliação Contábil, sua finalidade dentro do processo de análise de divergências e a forma como cada uma é acessada.

O objetivo é deixar explícita a separação entre:

- consultas estruturadas;
- recuperação documental via RAG;
- memória do agente;
- informações que não são utilizadas.

Essa documentação complementa os documentos `rag.md`, `memoria.md` e `arquitetura.md`, servindo como referência para manutenção, auditoria e evolução da solução.

---

# Visão Geral

O agente opera sobre diferentes categorias de fontes.

| Categoria | Finalidade |
|------------|------------|
| ERP | Dados estruturados e transacionais |
| Contratos | Regras comerciais e obrigações |
| Aditivos | Alterações contratuais |
| E-mails | Contexto de negociação |
| Políticas | Regras corporativas |
| Procedimentos | Operação do processo |
| Memória | Conhecimento acumulado |

---

# Fontes Estruturadas

## ERP Corporativo

### Finalidade

Fornecer informações transacionais atualizadas necessárias para análise das divergências.

### Informações Recuperadas

- Nota Fiscal;
- Pedido de Compra;
- fornecedor;
- centro de custo;
- valor da NF;
- valor do pedido;
- status do pagamento;
- status da aprovação;
- datas relevantes;
- identificadores internos.

### Tipo de Acesso

Consulta estruturada.

### Motivo

Os dados possuem identificadores únicos e exigem precisão absoluta.

Exemplos:

```text
Qual o valor da NF 45887?

Qual o valor do pedido 450019283?
```

Essas informações não devem ser recuperadas por busca semântica.

---

## Cadastro de Fornecedores

### Finalidade

Recuperar informações cadastrais dos fornecedores envolvidos.

### Informações Recuperadas

- razão social;
- identificador interno;
- categoria;
- situação cadastral;
- histórico básico de relacionamento.

### Tipo de Acesso

Consulta estruturada.

### Utilização

Validação de informações e contextualização da análise.

---

# Fontes Documentais (RAG)

## Contratos

### Finalidade

Representam a principal fonte de regras comerciais aplicáveis aos fornecedores.

### Informações Utilizadas

- reajustes;
- prazos;
- serviços contratados;
- condições comerciais;
- tolerâncias;
- cláusulas de faturamento.

### Tipo de Acesso

Recuperação RAG.

### Estrutura de Indexação

Chunk por cláusula.

### Metadados

```text
fornecedor
numero_contrato
versao
vigencia
```

---

## Aditivos Contratuais

### Finalidade

Registrar alterações posteriores aos contratos.

### Informações Utilizadas

- reajustes de valores;
- mudanças de escopo;
- prorrogações;
- alterações de condições.

### Tipo de Acesso

Recuperação RAG.

### Estrutura de Indexação

Aditivo completo ou cláusula alterada.

### Metadados

```text
contrato_relacionado
vigencia
versao
```

---

## Histórico de E-mails

### Finalidade

Recuperar negociações e exceções formalizadas fora do ERP.

### Informações Utilizadas

- acordos comerciais;
- aprovações excepcionais;
- justificativas;
- alterações de última hora;
- negociações com fornecedores.

### Tipo de Acesso

Recuperação RAG.

### Estrutura de Indexação

Mensagem individual.

### Metadados

```text
data
remetente
destinatario
fornecedor
assunto
```

### Importância

Diversas justificativas de divergências não aparecem em contratos nem no ERP, estando registradas apenas em trocas de e-mail.

---

## Políticas Internas

### Finalidade

Definir regras corporativas aplicáveis ao processo financeiro.

### Informações Utilizadas

- limites de aprovação;
- critérios de escalonamento;
- tolerâncias;
- responsabilidades organizacionais.

### Tipo de Acesso

Recuperação RAG.

### Estrutura de Indexação

Seção ou capítulo.

---

## Procedimentos Operacionais

### Finalidade

Orientar a execução correta do processo Procure-to-Pay.

### Informações Utilizadas

- fluxos de aprovação;
- responsabilidades;
- procedimentos de exceção;
- tratamento de divergências.

### Tipo de Acesso

Recuperação RAG.

### Estrutura de Indexação

Procedimento completo ou etapa operacional.

---

# Fontes de Memória

## Memória Episódica

### Finalidade

Armazenar casos anteriores relevantes.

### Exemplos

```text
Fornecedor XYZ apresentou divergência semelhante.

Diferença aprovada por aditivo contratual.
```

### Recuperação

Similaridade semântica.

### Persistência

Longo prazo.

---

## Memória Semântica

### Finalidade

Armazenar regras e fatos consolidados.

### Exemplos

```text
Limite atual de aprovação.

Regra vigente de tolerância financeira.
```

### Recuperação

Consulta por chave.

### Persistência

Longo prazo.

---

## Memória Procedural

### Finalidade

Definir o comportamento do agente.

### Exemplos

```text
Como analisar divergências.

Quando solicitar aprovação humana.

Como responder com insuficiência.
```

### Recuperação

Carregada no início da execução por meio do System Prompt.

---

# Fontes Humanas

## Aprovador Financeiro

### Finalidade

Tomar decisões quando a automação não possui autoridade suficiente.

### Acionamento

- divergências acima do limite;
- conflito documental;
- exceções;
- ausência de evidência.

### Tipo de Interação

Human-in-the-Loop.

---

## Especialistas de Negócio

### Finalidade

Atualizar conhecimento organizacional.

### Responsabilidades

- validar regras;
- revisar documentos;
- atualizar políticas;
- corrigir informações incorretas.

---

# Fontes Excluídas

Algumas informações não serão utilizadas pelo agente.

## Dados Sensíveis

- senhas;
- tokens;
- credenciais;
- chaves de acesso.

### Motivo

Segurança.

---

## Dados Pessoais Sem Relação com o Processo

- informações pessoais de colaboradores;
- dados não relacionados à análise financeira.

### Motivo

Privacidade e conformidade.

---

## Informações Não Verificadas

- opiniões;
- hipóteses;
- informações sem fonte documental.

### Motivo

Evitar propagação de informações incorretas.

---

# Prioridade das Fontes

Quando múltiplas fontes responderem à mesma pergunta, a prioridade será:

```text
1. ERP
2. Contrato vigente
3. Aditivo vigente
4. Política interna
5. Procedimento operacional
6. Histórico de e-mails
7. Memória episódica
```

## Justificativa

A ordem prioriza fontes formais e auditáveis.

Experiências anteriores auxiliam na investigação, mas não substituem documentos oficiais.

---

# Conflitos Entre Fontes

Quando houver conflito:

## Exemplo

Contrato:

```text
Não permite reajuste.
```

Aditivo:

```text
Permite reajuste de 4%.
```

O agente utilizará os metadados de vigência para determinar qual documento possui precedência.

Regra:

```text
Documento mais recente e vigente
        >
Documento histórico
```

Se o conflito permanecer, o caso será encaminhado para aprovação humana.

---

# Resumo

A arquitetura do agente utiliza múltiplas fontes especializadas para responder perguntas sobre divergências financeiras no processo Procure-to-Pay.

Cada fonte possui um papel específico:

- ERP para dados estruturados;
- RAG para contexto documental;
- Memória para aprendizado entre execuções;
- Humanos para exceções e decisões críticas.

A correta separação dessas responsabilidades reduz erros, melhora a auditabilidade e garante que as decisões produzidas pelo sistema sejam sustentadas por evidências verificáveis.