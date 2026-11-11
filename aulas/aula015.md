# Plano de observabilidade — agente de trocas

## 1. Perguntas

| Interessado | Pergunta | Decisão que a resposta muda |
|---|---|---|
| o negócio | Qual o percentual de conversas que terminam em aprovação, recusa ou transição humana? | Modificar a flexibilidade da política comercial de trocas ou expandir o escopo de atuação do agente. |
| a operação | Quantas trocas foram registradas de forma errônea fora do prazo de 30 dias estabelecido? | Paralisar a ferramenta `registrar_troca` temporariamente para correção de prompts ou auditoria manual dos pedidos afetados. |
| quem paga | Qual é o custo médio acumulado por token consumido por cada atendimento resolvido? | Substituir o modelo de LLM atual por uma alternativa menor/destilada ou otimizar o tamanho do contexto do prompt. |
| quem responde pelo sistema | Com que frequência o agente atinge o limite máximo do orçamento de 6 passos sem concluir a tarefa? | Refatorar as assinaturas das ferramentas (`tools`) ou reestruturar as instruções de fluxo lógico e tomada de decisão. |

---

## 2. O *trace* de uma conversa

**Árvore de *spans* de uma conversa típica:**

```text
invoke_agent  agente-de-trocas
├── chat mistral-small-latest
├── execute_tool consultar_pedido
├── chat mistral-small-latest
├── execute_tool consultar_politica
├── chat mistral-small-latest
├── execute_tool registrar_troca
└── chat mistral-small-latest
```

**Atributos próprios na raiz:**

| Atributo | Valores possíveis | Para que serve |
|---|---|---|
| `loja.troca.resultado` | `aprovada`, `recusada`, `encaminhada`, `erro` | Agrupar e contabilizar os desfechos lógicos do atendimento sem precisar fazer parse de texto livre. |
| `agente.passos_utilizados` | `1`, `2`, `3`, `4`, `5`, `6` | Monitorar a eficiência de conversação da IA e identificar gargalos antes de estourar o orçamento de chamadas. |
| `loja.pedido.id` | String (ex: `"48219"`) | Rastrear e correlacionar falhas técnicas ou auditorias de conformidade com registros específicos no banco de dados. |

---

## 3. Modos de falha

| Componente | Falha | Ruidosa ou silenciosa | Sinal que a torna visível |
|---|---|---|---|
| Modelo (LLM) | Ignorar a data de compra e aprovar troca com prazo superior aos 30 dias exigidos. | silenciosa | `loja.troca.resultado = aprovada` associado a um payload de pedido com data retroativa inválida. |
| Modelo (LLM) | Entrar em loop infinito chamando repetidamente a mesma ferramenta de consulta. | silenciosa | Atributo `agente.passos_utilizados = 6` resultando em encaminhamento forçado por estouro de orçamento. |
| Ferramenta | Banco de dados offline ou erro de rede interno ao executar a função `consultar_pedido`. | ruidosa | Span `execute_tool` com status marcado como `Error` e presença de traceback de exceção. |
| Ferramenta | Função `registrar_troca` retorna sucesso para a LLM, mas falha na gravação persistente física do banco SQL. | silenciosa | Log de observabilidade indicando troca aprovada, porém inexistente no cruzamento com a base transacional. |

---

## 4. Objetivos

| Tipo | Indicador | Objetivo | Janela |
|---|---|---|---|
| operacional | Duração total do span `invoke_agent` (Latência P95) | $\le$ 5 segundos | 7 dias |
| a promessa da loja | Percentual de atendimentos com desfechos (`aprovada` ou `recusada`) sem transição | $\ge$ 60% das conversas | 28 dias |

---

## 5. Alertas

| Alerta | Condição e limiar | SLO de origem | Quem é avisado | O que faz |
|---|---|---|---|---|
| custo | Custo diário acumulado de tokens ultrapassa 120% do esperado nas últimas 4 horas. | Orçamento financeiro do modelo | Analista de FinOps / Gerente de Produto | Investiga anomalias de acessos em lote ou comportamentos de loops de repetição da LLM. |
| degradação silenciosa | Taxa de encaminhamento para atendente humano ultrapassa 45% na última hora. | A promessa da loja ($\ge$ 60% de resolução) | Engenheiro de Prompt / Desenvolvedor IA | Inspeciona amostras de traces para verificar se novas categorias de produtos estão confundindo o modelo. |
