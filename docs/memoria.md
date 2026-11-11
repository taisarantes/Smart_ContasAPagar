# Memória do Agente de Conciliação Contábil

## Contexto

O agente proposto para o processo de conciliação contábil entre Notas Fiscais (NF) e Pedidos de Compra (PO) atua analisando divergências financeiras, tributárias e contratuais em um fluxo Procure-to-Pay (P2P). Seu objetivo é reduzir o esforço manual do time de Contas a Pagar, consultando contratos, aditivos, histórico de negociações e dados estruturados do ERP para sugerir justificativas e encaminhamentos.

A memória do sistema deve permitir que o agente aprenda com casos anteriores, recupere decisões relevantes e mantenha a continuidade de execuções longas. Ao mesmo tempo, precisa evitar o acúmulo de informações obsoletas, contraditórias ou sensíveis.

---

# Decisão 1 – Como o agente lembra

## 1.1 Os dois níveis, separados

| Aspecto | Curto prazo | Longo prazo |
|----------|-------------|-------------|
| O que é | Estado da execução atual de uma análise de divergência | Conhecimento acumulado entre execuções |
| Conteúdo | Prompt do sistema, dados da NF analisada, objetivo da execução, histórico da investigação, documentos recuperados e decisões intermediárias | Memórias episódicas, semânticas e procedurais |
| Persistido como | Checkpoint por execução | Índice vetorial, banco chave-valor e documentos textuais |
| Lido | Na retomada da execução | Sempre que houver necessidade de recuperação |
| Acesso | Identificador da execução | Similaridade ou chave |
| Ciclo de vida | Termina quando o caso é encerrado | Acumula ao longo do tempo |

### Conteúdo do checkpoint

Para que uma execução seja retomável sem repetir efeitos colaterais, o checkpoint armazenará:

- Identificador do caso analisado;
- Número da NF;
- Número do Pedido de Compra;
- Etapa atual do fluxo;
- Documentos já recuperados;
- Justificativas encontradas;
- Ferramentas executadas;
- Respostas recebidas do ERP;
- Aprovações pendentes;
- Aprovações já realizadas;
- Timestamp da última atualização.

Essa estrutura permite:

1. Retomar uma análise interrompida sem executar novamente consultas ou registrar justificativas duplicadas;
2. Receber aprovações humanas horas depois do início da execução;
3. Reproduzir integralmente um caso para fins de auditoria ou depuração.

---

## 1.2 O curto prazo: orçamento da janela

Considerando uma janela de contexto de aproximadamente 16.000 tokens, o orçamento inicial será:

| Fonte | Limite |
|---------|---------|
| System Prompt | 2.000 tokens |
| Objetivo atual | 500 tokens |
| Trajetória da execução | 2.500 tokens |
| Memória recuperada | 3.000 tokens |
| Trechos recuperados via RAG | 8.000 tokens |

### Política de descarte

Quando o limite for excedido:

1. Descartar trajetórias antigas da execução;
2. Reduzir a quantidade de memória recuperada;
3. Reduzir documentos recuperados menos relevantes;
4. Preservar o system prompt;
5. Preservar o objetivo atual.

A prioridade é manter o contexto operacional mais recente da análise.

### Conteúdo armazenado no checkpoint

O checkpoint guardará:

- Estado atual da investigação;
- Consultas efetuadas;
- Resultados intermediários;
- Aprovações aguardando resposta;
- Lista de documentos utilizados;
- Identificadores técnicos da execução.

O checkpoint não armazenará embeddings nem documentos completos, apenas referências.

---

## 1.3 O longo prazo: as três memórias do case

| Tipo | O que guarda no case | Estrutura | Como é recuperada |
|--------|----------------------|------------|-------------------|
| Episódica | Casos anteriores de divergência e respectivas soluções | Índice vetorial | Similaridade semântica |
| Semântica | Regras aprovadas, parâmetros, exceções conhecidas e políticas vigentes | Banco chave-valor | Consulta por chave |
| Procedural | Instruções de operação do agente | Texto no System Prompt | Carregamento no início da execução |

### Memória episódica

Exemplos:

- Divergência causada por imposto não previsto no pedido;
- Exceção contratual aprovada anteriormente;
- Caso resolvido por aditivo contratual;
- Divergência tratada por retenção tributária específica.

A recuperação ocorre por similaridade com o caso atual.

### Memória semântica

Exemplos:

- Limite de tolerância financeira vigente;
- Fluxo de aprovação;
- Regras tributárias aceitas;
- Parâmetros do processo P2P;
- Lista de tipos de divergência.

A recuperação ocorre por chave ou filtro estruturado.

### Memória procedural

Exemplos:

- Como analisar um caso;
- Ordem de consulta das fontes;
- Critérios de escalonamento;
- Regras de justificativa obrigatória.

Essa memória permanece no prompt do sistema.

---

## 1.4 Quem escreve e o que não entra

### Política de escrita

A gravação ocorrerá de formas diferentes:

| Conteúdo | Quem grava |
|-----------|------------|
| Casos concluídos | Código |
| Metadados de execução | Código |
| Aprendizados operacionais | Humano |
| Regras permanentes | Humano mediante validação |

### Volume esperado

Por execução:

- 1 registro episódico principal;
- até 5 registros auxiliares;
- aproximadamente 500 a 1.500 caracteres por registro.

### O que não entra na memória

Os seguintes itens não serão armazenados permanentemente:

#### Dados sensíveis

- CPF;
- CNPJ de terceiros quando não necessário;
- Dados bancários;
- Credenciais;
- Senhas;
- Tokens de acesso.

#### Informações não verificadas

- Alegações sem comprovação documental;
- Informações extraídas apenas de linguagem natural sem validação;
- Hipóteses geradas pelo modelo.

#### Informações deriváveis

- Valores calculados;
- Indicadores temporários;
- Resultados que podem ser obtidos novamente do ERP.

O armazenamento será restrito a conhecimento reutilizável.

---

# Decisão 2 – Como o agente esquece

## 2.1 Contradição – o fato mudou

Um exemplo de contradição no domínio do projeto ocorre quando uma política financeira muda.

### Exemplo

Versão antiga:

```text
Diferenças inferiores a 1% podem ser aprovadas automaticamente.