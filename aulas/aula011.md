# Exercício 11 – Avaliação do Agente de Conciliação de Notas Fiscais e Pedidos de Compra

# 1. Os casos – Golden Dataset v1

## Classes definidas

- **Classe A – Divergências justificáveis**
- **Classe B – Divergências inválidas**
- **Classe C – Casos de escalonamento**
- **Classe D – Casos de recusa/borda**

### Casos de teste

| # | Entrada | Esperado | Origem | Classe | Por que existe |
|---|---|---|---|---|---|
| 1 | NF com valor 1% acima do PO e diferença de R$ 20,00 | Aprovação automática | Sintético revisado | A | Testa tolerância financeira |
| 2 | NF com valor 1,4% acima e R$ 45,00 de diferença | Aprovação automática | Sintético revisado | A | Limite superior da política |
| 3 | NF com nomenclatura diferente ("Suporte Técnico" vs "Manutenção de Infraestrutura") e contrato compatível | Aprovar com justificativa | Caso sintético | A | Valida correspondência semântica |
| 4 | NF divergente com aditivo identificado em e-mail aprovado | Aprovar com justificativa | Caso do cenário principal | A | Exercita consulta ao histórico |
| 5 | NF com frete previsto em aditivo contratual | Aprovar com ajuste | Sintético revisado | A | Valida leitura de contratos |
| 6 | NF com diferença de 2% acima do PO | Rejeitar | Sintético revisado | B | Ultrapassa limite percentual |
| 7 | NF com diferença de R$ 75,00 | Rejeitar | Sintético revisado | B | Ultrapassa teto monetário |
| 8 | Alíquota de ISS divergente do cadastro fiscal | Rejeitar | Caso de domínio | B | Risco fiscal |
| 9 | Fornecedor adiciona taxa administrativa sem documentação | Rejeitar | Sintético revisado | B | Detecta cobrança indevida |
| 10 | Serviço cobrado consta como cancelado nos registros internos | Rejeitar | Caso descrito no trabalho | B | Contradição entre fontes |
| 11 | Divergência de R$ 6.000,00 com documentação válida | Escalonar gerente | Sintético revisado | C | Ultrapassa alçada |
| 12 | Fornecedor sem contrato ativo | Escalonar gerente | Caso de domínio | C | Regra obrigatória |
| 13 | Contrato e e-mails apresentam evidências conflitantes | Escalonar gerente | Sintético revisado | C | Ambiguidade documental |
| 14 | Três fontes trazem conclusões diferentes | Escalonar gerente | Sintético revisado | C | Caso complexo |
| 15 | Pergunta fora do domínio: "Qual a previsão do tempo?" | Recusar educadamente | Sintético | D | Teste de escopo |
| 16 | Nenhuma informação encontrada para a NF consultada | Informar insuficiência de dados | Sintético | D | Testa ausência de evidência |
| 17 | NF com campos obrigatórios ausentes | Solicitar correção | Sintético | D | Entrada malformada |
| 18 | PO inexistente informado pelo usuário | Informar erro de referência | Sintético | D | Valida consistência |
| 19 | Diferença exatamente de 1,5% e R$ 50,00 | Aprovação automática | Sintético revisado | D | Caso de borda |
| 20 | Contrato PDF ilegível ou corrompido | Solicitar intervenção humana | Sintético | D | Robustez documental |

## Casos provenientes de artefatos anteriores

Os seguintes cenários aproveitam situações já identificadas durante o desenvolvimento da solução:

- Divergências de nomenclatura entre Nota Fiscal e Pedido de Compra;
- Aditivos contratuais identificados em históricos de e-mail;
- Contradições entre Nota Fiscal e registros internos;
- Ausência de contrato ativo para o fornecedor;
- Casos dentro da margem de tolerância financeira.

Atualmente a maior parte do conjunto de testes é composta por dados sintéticos revisados. Em ambiente produtivo, novos casos deverão ser incorporados a partir dos tickets de conciliação financeira, exceções registradas no ERP e históricos de escalonamento para gestores.

---

# 2. Propriedades esperadas por nível

## Propriedades determinísticas

| Propriedade esperada | Avaliação esperada | O que caracteriza falha |
|---|---|---|
| Veredito correto para casos com gabarito | Comparação direta com resultado esperado | Aprovar NF acima da tolerância |
| Classificação correta (aprovar, rejeitar ou escalar) | Igualdade exata | Escalar caso que deveria ser aprovado |
| Estrutura do relatório válida | Validação de schema JSON | Campos obrigatórios ausentes |
| Valor calculado da divergência correto | Comparação numérica | Divergência calculada incorretamente |

## Propriedades de trajetória

| Propriedade esperada | Avaliação esperada | O que caracteriza falha |
|---|---|---|
| Consultou Pedido de Compra antes da decisão | Verificação do trace | Decisão sem consultar ERP |
| Consultou contrato quando existe divergência | Verificação do trace | Ignorar contrato disponível |
| Consultou histórico de e-mails | Verificação do trace | Não procurar evidências complementares |
| Fontes lidas na ordem prevista | Análise do trace | Tomar decisão antes de concluir a investigação |

## Propriedades de resultado

| Propriedade esperada | Avaliação esperada | O que caracteriza falha |
|---|---|---|
| Registro criado apenas uma vez | Verificação do estado final | Duplicidade de lançamento |
| Escalonamento registrado corretamente | Verificação de logs | Caso crítico sem encaminhamento |
| Justificativa anexada ao processo | Consulta ao ERP | Aprovação sem rastreabilidade |
| Status final compatível com o veredito | Verificação do banco | NF aprovada marcada como rejeitada |

## Avaliação por juiz LLM

| Propriedade esperada | Avaliação |
|---|---|
| Justificativa sustenta a decisão tomada | Rubrica binária |
| Evidências utilizadas são relevantes | Rubrica binária |
| Explicação compreensível para auditoria | Rubrica binária |

### Falhas mais críticas do domínio

1. Aprovar uma Nota Fiscal indevida.
2. Rejeitar uma Nota Fiscal legítima.
3. Não escalar casos acima da alçada financeira.
4. Produzir justificativas sem evidências reais.

Essas falhas podem resultar em perdas financeiras, riscos fiscais e problemas de auditoria.

---

# 3. O juiz e sua validação

## Propriedade escolhida

**A justificativa sustenta corretamente o veredito proposto.**

## Rubrica binária

### Resultado: SIM

A justificativa:

- cita pelo menos uma evidência encontrada;
- utiliza evidência diretamente relacionada à divergência;
- apresenta evidência compatível com a decisão final.

### Resultado: NÃO

A justificativa:

- não apresenta evidências;
- utiliza evidências irrelevantes;
- apresenta evidências incompatíveis com a conclusão;
- contém afirmações não encontradas nas fontes consultadas.

## Exemplo positivo

### Caso 4

**Situação:**

- Divergência de R$ 1.500,00;
- E-mail encontrado autorizando horas extras;
- Decisão do agente: Aprovar.

**Avaliação:** SIM

A justificativa é considerada válida porque a evidência encontrada explica diretamente o valor divergente identificado na Nota Fiscal.

## Exemplo negativo

### Caso 9

**Situação:**

- Taxa administrativa adicionada à Nota Fiscal;
- Nenhum contrato ou e-mail menciona a cobrança;
- Decisão correta: Rejeitar.

**Avaliação:** NÃO

Uma justificativa que aprova a cobrança utilizando apenas o argumento de "bom relacionamento com o fornecedor" não possui suporte documental suficiente e deve ser reprovada.

## Processo de validação do juiz

### Amostra inicial

- 50 respostas geradas pelo agente.

### Avaliadores humanos

- Equipe do projeto;
- Assistente de Contas a Pagar;
- Gerente Financeiro.

Cada resposta será analisada por pelo menos dois avaliadores independentes.

### Critério de adoção

O juiz será aprovado apenas se alcançar:

**Concordância mínima de 85% em relação aos avaliadores humanos.**

Caso esse percentual não seja atingido, a rubrica deverá ser revisada e ajustada.

## Principal viés identificado

### Viés de verbosidade

Existe o risco de o juiz considerar justificativas longas como melhores, mesmo quando incorretas.

### Estratégia de mitigação

A avaliação não considera tamanho do texto.

O juiz verifica apenas:

1. Existência de evidência;
2. Relevância da evidência;
3. Compatibilidade da evidência com a conclusão.

---

# 4. O ruído e a regra que separa melhora de acaso

## Fontes de não determinismo

| Fonte de variação | Estratégia |
|---|---|
| Temperatura do modelo | Controlar (valor fixo) |
| Recuperação RAG | Medir |
| Atualização da base documental | Congelar durante a avaliação |
| Histórico da conversa | Reiniciar contexto em cada execução |
| Ordem de recuperação dos documentos | Medir |

## Quantidade de repetições

Cada caso será executado:

**5 vezes.**

### Justificativa

- Permite observar variações na recuperação de contexto;
- Reduz a influência de resultados ocasionais;
- Mantém o custo computacional viável para a disciplina.

## Escolha entre pass@k e pass^k

### Métrica escolhida: pass^k

Como o agente influencia decisões financeiras e fiscais, não basta acertar apenas uma vez.

É importante garantir consistência em todas as execuções.

Por esse motivo, a métrica escolhida é **pass^k**, que exige sucesso repetido e comportamento estável.

## Regra de promoção para novas versões

Uma nova versão do sistema somente será aprovada se atender simultaneamente aos seguintes critérios:

1. Melhorar o resultado global em pelo menos **3 pontos percentuais**;
2. Não reduzir mais de **2 pontos percentuais** em nenhuma classe do dataset;
3. Não aumentar a taxa de falsos positivos (aprovações incorretas);
4. Manter no mínimo **95% de acerto** nos casos de escalonamento obrigatório.

**Data da definição:** 09/10/2026.

Essa regra evita que melhorias em cenários simples escondam regressões em situações críticas com impacto financeiro, fiscal ou de auditoria.