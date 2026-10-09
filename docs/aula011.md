Exercício 11 – Avaliação do Agente de Conciliação de Notas Fiscais e Pedidos de Compra

1. Os casos – Golden Dataset v1
Classes definidas
Classe A – Divergências justificáveis
Classe B – Divergências inválidas
Classe C – Casos de escalonamento
Classe D – Casos de recusa/borda
#	Entrada	Esperado	Origem	Classe	Por que existe1	NF com valor 1% acima do PO e diferença de R$ 20,00	Aprovação automática	Sintético revisado	A	Testa tolerância financeira
2	NF com valor 1,4% acima e R$ 45,00 de diferença	Aprovação automática	Sintético revisado	A	Limite superior da política
3	NF com nomenclatura diferente ("Suporte Técnico" vs "Manutenção de Infraestrutura") e contrato compatível	Aprovar com justificativa	Caso sintético	A	Valida correspondência semântica
4	NF divergente com aditivo identificado em e-mail aprovado	Aprovar com justificativa	Caso do cenário principal	A	Exercita consulta ao histórico
5	NF com frete previsto em aditivo contratual	Aprovar com ajuste	Sintético revisado	A	Valida leitura de contratos
6	NF com diferença de 2% acima do PO	Rejeitar	Sintético revisado	B	Ultrapassa limite percentual
7	NF com diferença de R$ 75,00	Rejeitar	Sintético revisado	B	Ultrapassa teto monetário
8	Alíquota de ISS divergente do cadastro fiscal	Rejeitar	Caso de domínio	B	Risco fiscal
9	Fornecedor adiciona taxa administrativa sem documentação	Rejeitar	Sintético revisado	B	Detecta cobrança indevida
10	Serviço cobrado consta como cancelado nos registros internos	Rejeitar	Caso descrito no trabalho	B	Contradição entre fontes
11	Divergência de R$ 6.000,00 com documentação válida	Escalonar gerente	Sintético revisado	C	Ultrapassa alçada
12	Fornecedor sem contrato ativo	Escalonar gerente	Caso de domínio	C	Regra obrigatória
13	Contrato e e-mails apresentam evidências conflitantes	Escalonar gerente	Sintético revisado	C	Ambiguidade documental
14	Três fontes trazem conclusões diferentes	Escalonar gerente	Sintético revisado	C	Caso complexo
15	Pergunta fora do domínio: "Qual a previsão do tempo?"	Recusar educadamente	Sintético	D	Teste de escopo
16	Nenhuma informação encontrada para a NF consultada	Informar insuficiência de dados	Sintético	D	Testa ausência de evidência
17	NF com campos obrigatórios ausentes	Solicitar correção	Sintético	D	Entrada malformada
18	PO inexistente informado pelo usuário	Informar erro de referência	Sintético	D	Valida consistência
19	Diferença exatamente de 1,5% e R$ 50,00	Aprovação automática	Sintético revisado	D	Caso de borda
20	Contrato PDF ilegível ou corrompido	Solicitar intervenção humana	Sintético	D	Robustez documental
Casos provenientes de artefatos anteriores

Os seguintes tipos de caso aproveitam elementos já existentes no desenvolvimento do agente:

Casos de divergência de nomenclatura.
Casos de aditivos contratuais encontrados em e-mails.
Casos de contradição entre nota fiscal e registros internos.
Casos de ausência de contrato ativo.
Casos de tolerância financeira.

Atualmente a maior parte dos casos é sintética revisada. Quando o sistema entrar em produção, os casos reais serão coletados a partir dos tickets de conciliação financeira, das exceções registradas no ERP e dos escalonamentos realizados para o gerente financeiro.

2. Propriedades esperadas por nível
Nível	Propriedade esperada	Avaliação esperada	O que é falhar no domínioDeterminístico	Veredito correto para casos com gabarito	Comparação direta com resultado esperado	Aprovar NF acima da tolerância
Determinístico	Classificação correta (aprovar, rejeitar ou escalar)	Igualdade exata	Escalar caso que deveria ser aprovado
Determinístico	Estrutura do relatório válida	Validação de schema JSON	Campos obrigatórios ausentes
Determinístico	Valor calculado da divergência correto	Comparação numérica	Divergência calculada erroneamente
Trajetória	Consultou PO antes da decisão	Verificação do trace	Decisão sem consultar ERP
Trajetória	Consultou contrato quando existe divergência	Verificação do trace	Ignorar contrato disponível
Trajetória	Consultou histórico de e-mails	Verificação do trace	Não procurar evidências complementares
Trajetória	Fontes lidas na ordem prevista	Análise do trace	Tomar decisão antes de completar investigação
Resultado	Registro criado apenas uma vez	Verificação do estado final	Duplicidade de lançamento
Resultado	Escalonamento registrado corretamente	Verificação de log	Caso crítico sem encaminhamento
Resultado	Justificativa anexada ao processo	Consulta ao ERP	Aprovação sem rastreabilidade
Resultado	Status final compatível com o veredito	Verificação do banco	NF aprovada marcada como rejeitada
Juiz LLM	Justificativa sustenta a decisão tomada	Rubrica binária	Texto cita evidências não relacionadas
Juiz LLM	Evidências utilizadas são relevantes	Rubrica binária	Contrato citado não corresponde ao caso
Juiz LLM	Explicação compreensível para auditoria	Rubrica binária	Relatório ambíguo ou contraditório
Propriedades mais críticas

As falhas mais graves são:

Aprovar uma nota fiscal indevida.
Rejeitar uma nota fiscal legítima.
Não escalar casos acima da alçada.
Produzir justificativas sem evidências reais.

Essas falhas podem gerar perdas financeiras, multas fiscais ou problemas de auditoria.

3. O juiz e sua validação
Propriedade escolhida

A justificativa sustenta corretamente o veredito proposto.

Rubrica binária
SIM

A justificativa:

cita pelo menos uma evidência encontrada;
a evidência está diretamente relacionada à divergência;
a evidência suporta a decisão final.
NÃO

A justificativa:

não apresenta evidência;
utiliza evidência irrelevante;
apresenta evidência incompatível com a conclusão;
contém afirmações não encontradas nas fontes analisadas.
Exemplo positivo

Caso 4:

Divergência de R$ 1.500,00.
E-mail encontrado autorizando horas extras.
Decisão: aprovar.

Justificativa aprovada porque a evidência encontrada explica exatamente o valor divergente.

Exemplo negativo

Caso 9:

Taxa administrativa adicionada à NF.
Nenhum contrato ou e-mail menciona a cobrança.
Decisão correta seria rejeitar.

Uma justificativa que aprove citando apenas "histórico de relacionamento com o fornecedor" recebe nota NÃO.

Validação do juiz
Amostra inicial: 50 respostas do agente.
Rotuladores:
equipe do projeto;
Assistente de Contas a Pagar;
Gerente Financeiro.
Cada caso será avaliado por dois revisores humanos.
Critério de adoção

O juiz somente será adotado se alcançar:

Concordância mínima de 85% com os avaliadores humanos.

Abaixo desse valor, a rubrica deverá ser revisada.

Viés principal
Viés de verbosidade

Risco: o juiz favorecer justificativas longas mesmo quando incorretas.

Mitigação

A rubrica não considera tamanho do texto. Apenas verifica se:

Existe evidência.
A evidência é relevante.
A evidência suporta a conclusão.
4. O ruído e a regra que separa melhora de acaso
Fontes de não determinismo
Fonte	EstratégiaTemperatura do modelo	Controlar (temperatura fixa)
Recuperação RAG	Medir
Atualização da base documental	Congelar durante a avaliação
Histórico de memória da conversa	Reiniciar contexto a cada execução
Ordem de recuperação de documentos	Medir
Repetições por caso

Cada caso será executado:

5 vezes.

Motivo:

permite observar variação da recuperação de contexto;
reduz influência de resultados ocasionais;
mantém custo viável para a disciplina.
pass@k ou pass^k
Escolha: pass^k

O agente influencia decisões financeiras e pode aprovar ou rejeitar documentos.

Portanto, não basta acertar uma vez. O comportamento precisa ser consistente em todas as execuções.

O critério adequado é pass^k, exigindo sucesso repetido.

Regra de promoção

Uma nova versão do sistema será aprovada somente se:

Melhorar o resultado global em pelo menos 3 pontos percentuais sobre a versão atual.
Não reduzir mais que 2 pontos percentuais em nenhuma classe do dataset.
Não aumentar a taxa de falsos positivos (aprovações incorretas).
Manter pelo menos 95% de acerto nos casos de escalonamento obrigatório.

Data da definição: 09/10/2026.

Essa regra impede que uma melhoria em casos fáceis esconda regressões graves em situações de risco financeiro ou fiscal.