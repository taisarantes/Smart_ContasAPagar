# RAG (Retrieval Augmented Generation)

## Objetivo

O sistema utiliza Retrieval Augmented Generation (RAG) para complementar o conhecimento do modelo com documentos específicos do processo Procure-to-Pay (P2P). O objetivo é permitir que o agente produza análises fundamentadas em evidências documentais reais da organização, reduzindo o risco de conclusões incorretas ou não auditáveis.

O RAG não substitui as consultas estruturadas ao ERP. Seu papel é recuperar contexto, justificativas e conhecimento organizacional que não estão disponíveis em bancos relacionais ou não podem ser representados apenas por identificadores e valores.

---

# Papel do RAG na Arquitetura

O RAG é utilizado sempre que a análise exige interpretação documental.

Exemplos:

- Verificar se existe cláusula contratual que justifique um reajuste.
- Localizar aditivos que alteraram condições originalmente contratadas.
- Encontrar negociações realizadas por e-mail.
- Consultar procedimentos internos de aprovação.
- Identificar exceções já formalizadas anteriormente.

O RAG não é utilizado para recuperar:

- valores monetários atuais;
- status de documentos;
- datas de pagamento;
- identificadores de pedidos;
- dados cadastrais.

Essas informações permanecem sob responsabilidade das consultas estruturadas ao ERP.

---

# Conhecimento Recuperado

## Contratos de Fornecedores

Os contratos representam a principal fonte de justificativas para divergências financeiras.

Exemplos de informações recuperadas:

- regras de reajuste;
- cláusulas de faturamento;
- tolerâncias previstas;
- regras tributárias específicas;
- serviços contratados.

---

## Aditivos Contratuais

Os aditivos complementam ou alteram contratos já existentes.

Exemplos:

- reajustes posteriores;
- mudança de escopo;
- alterações de prazo;
- mudanças de valor contratado.

Como os aditivos frequentemente substituem regras anteriores, seus metadados incluem obrigatoriamente data de vigência e versão.

---

## Histórico de E-mails

Diversas exceções de negócio são registradas apenas em trocas de mensagens entre:

- fornecedores;
- compras;
- financeiro;
- gestores;
- áreas solicitantes.

Os e-mails permitem recuperar justificativas que não aparecem em contratos ou no ERP.

---

## Políticas Internas

Documentos utilizados para validar:

- limites de aprovação;
- tolerâncias financeiras;
- critérios de escalonamento;
- responsabilidades organizacionais.

---

## Procedimentos Operacionais

Documentação que descreve:

- fluxos de aprovação;
- tratamento de exceções;
- operação do processo Procure-to-Pay.

---

# Fontes Indexadas

## Documentos incluídos

| Fonte | Motivo |
|---------|---------|
| Contratos ativos | Justificam condições comerciais |
| Aditivos contratuais | Alteram contratos vigentes |
| E-mails corporativos relacionados ao processo | Registram negociações e exceções |
| Políticas internas | Definem regras de negócio |
| Procedimentos operacionais | Definem o fluxo correto do processo |

---

## Documentos excluídos

| Fonte | Motivo |
|---------|---------|
| Pedidos de Compra | Melhor acesso por consulta estruturada |
| Notas Fiscais | Melhor acesso por identificador |
| Cadastro de fornecedores | Dados estruturados |
| Histórico financeiro operacional | Dados estruturados |
| Status de aprovações | Dados transacionais |

Essas informações possuem melhor desempenho e precisão quando consultadas diretamente no ERP.

---

# Estratégia de Chunking

O projeto utiliza chunking orientado à estrutura de cada documento.

Não existe uma estratégia única aplicada a todo o corpus.

---

## Contratos

### Unidade Natural

Cláusula contratual.

### Justificativa

As cláusulas representam unidades semânticas completas e possuem significado jurídico próprio.

### Exemplo

```text
Cláusula 5 – Reajuste de Preço

O fornecedor poderá aplicar reajuste anual
com base no índice IPCA.
```

Cada chunk preserva:

- título da cláusula;
- seção;
- texto completo.

---

## Aditivos

### Unidade Natural

Aditivo completo ou cláusula alterada.

### Justificativa

Os aditivos normalmente são curtos e tratam mudanças específicas.

Na maioria dos casos um documento inteiro corresponde a um único chunk.

---

## E-mails

### Unidade Natural

Mensagem individual.

### Justificativa

O contexto da negociação geralmente se encontra completo em um único e-mail.

Fragmentar mensagens reduziria a qualidade da recuperação.

---

## Políticas Internas

### Unidade Natural

Seção ou procedimento.

### Exemplo

```text
Política de Aprovação Financeira

4. Aprovação de Divergências
```

O chunk herda o cabeçalho da política para manter significado isolado.

---

# Metadados dos Chunks

Todos os chunks armazenam metadados para filtragem antes da busca vetorial.

## Contratos

```text
tipo_documento
fornecedor
numero_contrato
versao
data_vigencia
```

---

## Aditivos

```text
tipo_documento
contrato_relacionado
versao
data_vigencia
```

---

## E-mails

```text
assunto
data
remetente
destinatario
fornecedor
```

---

## Políticas

```text
documento
secao
versao
vigencia
```

---

# Estratégia de Recuperação

O sistema utiliza recuperação híbrida.

## Passo 1 — Filtro Estruturado

Aplicação de filtros baseados em:

- fornecedor;
- contrato;
- período;
- tipo de documento.

Objetivo:

Reduzir o universo de documentos antes da busca semântica.

---

## Passo 2 — Similaridade Vetorial

Após a filtragem inicial, os documentos restantes são ranqueados por similaridade com a solicitação recebida.

Objetivo:

Encontrar conteúdo semanticamente relacionado ao problema analisado.

---

## Passo 3 — Reordenação Temporal

Quando múltiplos documentos semelhantes são encontrados, aplica-se priorização por vigência.

Critério:

```text
Documento vigente mais recente
      >
Documento histórico
```

Essa etapa reduz problemas causados por regras revogadas ou substituídas.

---

# Critério de Suficiência

Nem toda recuperação resulta em resposta.

O agente considera uma consulta suficiente apenas quando:

1. Existe documento relevante recuperado;
2. A fonte possui relação direta com a solicitação;
3. Não existe conflito documental não resolvido.

Caso contrário:

```json
{
  "suficiente": false
}
```

e o sistema emite uma recusa fundamentada.

---

# Citação das Fontes

Todo resultado produzido pelo agente precisa informar explicitamente os documentos utilizados.

Exemplo:

```text
Fontes utilizadas:

- Contrato CT-014
- Aditivo AD-03
- E-mail de negociação de 14/03/2026
```

O agente nunca deve apresentar uma conclusão sem indicar as evidências que a sustentam.

---

# Integração com a Memória

O RAG não é utilizado como memória do agente.

### RAG

Recupera conhecimento documental.

Exemplo:

```text
O contrato permite reajuste de 4%.
```

### Memória Episódica

Recupera experiências anteriores.

Exemplo:

```text
Uma divergência semelhante foi aprovada para o mesmo fornecedor.
```

Essa separação evita que casos históricos sejam confundidos com regras oficiais.

---

# Volume Estimado

A primeira versão do sistema considera:

| Fonte | Volume Estimado |
|---------|----------------|
| Contratos | 100 a 300 |
| Aditivos | 200 a 600 |
| Políticas internas | 20 a 50 |
| Procedimentos | 20 a 50 |
| E-mails relevantes | alguns milhares |

A estimativa total permanece na ordem de milhares de chunks.

Nessa escala, um banco vetorial leve é suficiente para a primeira versão do projeto.

---

# Limitações Conhecidas

O RAG não resolve sozinho:

- inconsistências de dados no ERP;
- ausência de documentação;
- conflitos de negócio sem registro formal;
- documentos digitalizados sem OCR;
- regras que nunca foram documentadas.

Nesses cenários o agente deverá:

1. declarar insuficiência de evidências;
2. encaminhar para análise humana;
3. registrar a limitação encontrada.

---

# Justificativa da Estratégia Escolhida

A estratégia adotada busca equilibrar precisão e auditabilidade.

O processo de conciliação financeira depende de documentos corporativos específicos que não fazem parte do treinamento do modelo. Além disso, a simples busca vetorial não é suficiente para lidar com vigência, versões e identificadores estruturados.

Por esse motivo, o sistema combina:

1. filtros estruturados por metadados;
2. recuperação vetorial para contexto semântico;
3. ordenação por vigência;
4. validação de suficiência;
5. citação obrigatória das fontes.

Essa abordagem reduz alucinações, melhora a rastreabilidade e mantém conformidade com os requisitos de auditoria do processo Procure-to-Pay.