# Plano de Prompt Engineering

## Objetivo

Este documento descreve as estratégias de Prompt Engineering utilizadas pelo Agente de Conciliação Contábil para Procure-to-Pay (P2P). O objetivo é garantir que o agente produza respostas auditáveis, rastreáveis e alinhadas aos processos de negócio da organização.

O agente atua sobre divergências entre Notas Fiscais, Pedidos de Compra, contratos, aditivos e histórico de negociações. Como se trata de um domínio financeiro sujeito a auditoria, os prompts priorizam precisão, rastreabilidade e justificativa documental em detrimento de criatividade.

---

# Princípios Gerais

Todos os prompts seguem os seguintes princípios:

1. Utilizar apenas informações recuperadas pelo sistema.
2. Nunca inventar documentos, contratos ou justificativas.
3. Citar explicitamente as fontes utilizadas.
4. Declarar insuficiência de evidência quando necessário.
5. Produzir saídas estruturadas sempre que possível.
6. Separar claramente análise, evidência e conclusão.
7. Tratar ambiguidades explicitamente.

---

# Fluxo Geral do Agente

```text
Entrada do usuário
        ↓
Classificação da solicitação
        ↓
Extração de entidades
        ↓
Consulta ao ERP
        ↓
Recuperação RAG
        ↓
Análise da divergência
        ↓
Necessidade de aprovação?
       / \
      sim não
      ↓    ↓
 Human    Resposta
 Review    Final
      \    /
       ↓  ↓
     Resultado
```

---

# Etapa 1 — Classificação da Solicitação

## Objetivo

Determinar o tipo de solicitação recebida para direcionar o fluxo do agente.

## Técnica

Classificação por instrução explícita.

## Entrada

```text
Existe justificativa para a divergência da nota fiscal 45981?
```

## Prompt Base

```text
Você é responsável por classificar solicitações relacionadas ao processo Procure-to-Pay.

Classifique a solicitação em apenas uma categoria:

- consulta_divergencia
- justificativa_documental
- validacao_contrato
- consulta_historico
- aprovacao_manual
- fora_do_escopo

Responda apenas o nome da categoria.
```

## Saída Esperada

```text
consulta_divergencia
```

## Justificativa

Essa etapa possui baixa variabilidade e não requer geração de texto natural.

Configuração recomendada:

```text
temperature = 0
```

---

# Etapa 2 — Extração de Entidades

## Objetivo

Identificar elementos relevantes para consulta.

## Entidades

- Nota Fiscal
- Pedido de Compra
- Contrato
- Fornecedor
- Data
- Valor

## Técnica

Extração estruturada com schema.

## Prompt Base

```text
Extraia as entidades presentes na solicitação.

Retorne apenas JSON válido.

Campos:

{
  "nota_fiscal": "",
  "pedido_compra": "",
  "fornecedor": "",
  "contrato": "",
  "valor": "",
  "data": ""
}

Caso algum campo não exista, use null.
```

## Exemplo

Entrada:

```text
Existe justificativa para a diferença entre a NF 45887 e o pedido 450019283?
```

Saída:

```json
{
  "nota_fiscal": "45887",
  "pedido_compra": "450019283",
  "fornecedor": null,
  "contrato": null,
  "valor": null,
  "data": null
}
```

## Justificativa

Essa fase produz dados consumidos por código e não por pessoas.

Configuração recomendada:

```text
temperature = 0
response_format = json
```

---

# Etapa 3 — Recuperação RAG

## Objetivo

Localizar documentos relevantes para o caso atual.

## Fontes

- Contratos
- Aditivos
- Políticas internas
- Histórico de e-mails
- Procedimentos financeiros

## Prompt de Recuperação

```text
Utilize a solicitação abaixo para localizar os documentos mais relevantes.

Priorize:

1. Contratos relacionados ao fornecedor.
2. Aditivos mais recentes.
3. E-mails contendo acordos financeiros.
4. Políticas aplicáveis ao caso.

Desconsidere documentos sem relação direta com os identificadores informados.
```

## Justificativa

A recuperação deve maximizar precisão e minimizar ruído.

Não há geração de resposta ao usuário nesta etapa.

---

# Etapa 4 — Avaliação de Evidências

## Objetivo

Determinar se os documentos recuperados justificam a divergência.

## Prompt Base

```text
Analise os documentos fornecidos.

Determine:

1. Existe justificativa documental?
2. Qual documento sustenta essa conclusão?
3. Existe conflito entre fontes?
4. Há informação insuficiente?

Responda utilizando apenas as evidências fornecidas.

Não invente contratos, cláusulas ou decisões.
```

## Saída Esperada

```json
{
  "possui_justificativa": true,
  "documento_principal": "Aditivo AD-03",
  "conflito": false,
  "suficiente": true
}
```

## Justificativa

A conclusão precisa ser auditável.

A etapa não produz comunicação final ao usuário.

Configuração recomendada:

```text
temperature = 0
```

---

# Etapa 5 — Geração da Justificativa

## Objetivo

Explicar ao usuário o motivo da conclusão.

## Prompt Base

```text
Utilize exclusivamente as evidências fornecidas.

Estruture a resposta em:

- Conclusão
- Evidências
- Documento principal
- Próximo passo

Todas as afirmações devem ser sustentadas pelas fontes apresentadas.

Caso não existam evidências suficientes, declare explicitamente a insuficiência.
```

## Exemplo de Saída

```text
Conclusão:
A divergência é justificável.

Evidências:
O aditivo contratual AD-03 autoriza reajuste de 4% para o período analisado.

Documento principal:
Aditivo AD-03.

Próximo passo:
Encaminhar o caso para aprovação financeira.
```

## Configuração

```text
temperature = 0.2
```

## Justificativa

Pequena flexibilidade na redação melhora a legibilidade mantendo consistência factual.

---

# Etapa 6 — Solicitação de Aprovação Humana

## Objetivo

Preparar um resumo que permita tomada de decisão por um colaborador.

## Situações

- Divergência acima do limite de tolerância.
- Conflito entre documentos.
- Evidência insuficiente.
- Impacto financeiro relevante.

## Prompt Base

```text
Resuma o caso para aprovação humana.

Apresente:

- Contexto
- Divergência encontrada
- Evidências encontradas
- Riscos
- Recomendação do agente

Não tomar decisão final.

A decisão pertence ao aprovador humano.
```

## Exemplo

```text
Contexto:
Divergência entre NF 45887 e PO 450019283.

Evidências:
Aditivo AD-03 prevê reajuste.

Riscos:
O valor excede o limite de aprovação automática.

Recomendação:
Submeter para aprovação do coordenador financeiro.
```

## Justificativa

O objetivo é apoiar o humano, não substituí-lo.

---

# Etapa 7 — Produção da Resposta Final

## Objetivo

Construir a saída final validada do sistema.

## Prompt Base

```text
Gere a resposta final.

Obrigatoriamente informe:

- resultado
- fonte
- justificativa
- suficiente

Caso a evidência seja insuficiente, a resposta deve ser uma recusa fundamentada.
```

## Exemplos

### Resposta com evidência

```json
{
  "resultado": "Divergência justificada por aditivo contratual.",
  "fonte": [
    "Contrato CT-014",
    "Aditivo AD-03"
  ],
  "suficiente": true,
  "justificativa": "O aditivo autoriza reajuste de preço para o período da nota fiscal."
}
```

### Resposta com recusa

```json
{
  "resultado": "Não foi possível concluir a análise.",
  "fonte": [],
  "suficiente": false,
  "justificativa": "Nenhuma documentação relacionada à divergência foi encontrada."
}
```

---

# Técnicas Utilizadas

| Técnica | Utilização |
|----------|-----------|
| Instrução explícita | Classificação de solicitações |
| JSON estruturado | Extração de entidades |
| Grounding em documentos | Recuperação RAG |
| Verificação de evidências | Análise da divergência |
| Resposta fundamentada | Geração da justificativa |
| Human-in-the-loop | Casos críticos |
| Recusa explícita | Evidência insuficiente |

---

# Estratégias Rejeitadas

## Cadeias de raciocínio expostas ao usuário

Não serão exibidas ao usuário final.

Motivo:

- aumentam custo;
- dificultam auditoria;
- podem expor interpretações intermediárias.

---

## Respostas sem citação

Não serão permitidas.

Motivo:

O domínio financeiro exige rastreabilidade documental.

---

## Conclusões sem verificação documental

Não serão permitidas.

Motivo:

O objetivo do sistema é justamente apoiar decisões baseadas em evidências.

---

# Critério de Sucesso

O sistema será considerado correto quando:

1. A resposta estiver fundamentada em documentos recuperados.
2. Todas as fontes estiverem identificadas.
3. A conclusão puder ser auditada.
4. A insuficiência de evidências for declarada explicitamente.
5. Casos que exigem aprovação humana forem interrompidos corretamente.
6. A mesma entrada produzir respostas consistentes quando a memória e a base documental permanecerem inalteradas.