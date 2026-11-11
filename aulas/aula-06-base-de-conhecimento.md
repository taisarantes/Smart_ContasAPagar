# Aula 06 – Base de Conhecimento do Agente de Conciliação Contábil

## 1. Qual informação especializada o agente precisa, e por que ela não está no modelo

O agente proposto para o processo de conciliação entre Notas Fiscais (NF) e Pedidos de Compra (PO) precisa acessar informações que não fazem parte do conhecimento geral de um modelo de linguagem. Embora um LLM compreenda conceitos de contas a pagar, contratos, notas fiscais, retenções tributárias e processos Procure-to-Pay, ele não possui acesso aos documentos e regras específicas da organização.

| Informação | Motivo para vir de fora do modelo |
|------------|-----------------------------------|
| Contratos firmados com fornecedores | Informação privada da empresa |
| Aditivos contratuais | Informação privada e frequentemente atualizada |
| Histórico de e-mails entre fornecedores e colaboradores | Informação privada |
| Políticas internas de aprovação financeira | Informação privada |
| Limites de alçada para aprovação | Informação privada |
| Procedimentos internos do ERP | Informação privada e específica da organização |
| Histórico de justificativas de divergências anteriores | Informação privada |
| Parametrizações fiscais adotadas pela empresa | Informação específica e sujeita a alterações |

Além das informações privadas, existem dados que o modelo até pode conhecer parcialmente, mas não com a precisão necessária para uma decisão financeira. Por exemplo, retenções tributárias, códigos de serviço e exceções de contratos podem conter detalhes que o modelo tende a generalizar ou reproduzir incorretamente.

Por outro lado, algumas informações já fazem parte do conhecimento geral do modelo e não precisam ser indexadas:

- Conceitos de Nota Fiscal eletrônica (NF-e);
- Conceitos de Pedido de Compra (PO);
- Fluxo Procure-to-Pay (P2P);
- Noções de compliance financeiro;
- Terminologia contábil e tributária comum;
- Boas práticas de contas a pagar.

Indexar esse conhecimento geral aumentaria custo e volume de contexto sem gerar benefício prático.

---

## 2. Onde esses dados estão, e em que estado

As fontes de informação necessárias ao agente encontram-se distribuídas entre sistemas corporativos e repositórios documentais.

| Fonte | Onde vive | Formato | Proprietário | Frequência de atualização | Acesso |
|---------|------------|----------|--------------|---------------------------|---------|
| Contratos de fornecedores | SharePoint ou pasta corporativa | PDF/DOCX | Compras/Jurídico | Baixa | Necessário solicitar acesso de leitura |
| Aditivos contratuais | SharePoint ou GED corporativo | PDF/DOCX | Compras/Jurídico | Média | Necessário solicitar acesso de leitura |
| Histórico de e-mails | Exchange/Outlook | E-mail | Áreas de negócio | Alta | Necessário acesso controlado às caixas relevantes |
| Políticas internas | Intranet corporativa | HTML/PDF | Financeiro | Baixa | Normalmente disponível internamente |
| Cadastro de fornecedores | ERP | Banco de dados | Financeiro | Alta | API ou consulta direta |
| Pedidos de Compra | ERP | Banco de dados | Compras | Alta | API ou consulta direta |
| Notas fiscais recebidas | ERP / Repositório fiscal | XML/PDF | Fiscal | Alta | API ou integração direta |

Os contratos e aditivos representam as principais fontes para recuperação semântica. Caso existam PDFs digitalizados sem camada de texto, será necessário aplicar OCR antes da indexação.

O histórico de e-mails também possui grande relevância, pois muitos dos casos de divergência descritos no projeto surgem de acordos realizados fora do ERP e formalizados apenas por troca de mensagens.

---

## 3. O que vai para o índice — e o que não vai

Nem todas as fontes identificadas devem ser indexadas para busca semântica.

### O que entra no índice

Serão indexados documentos que contenham justificativas, contexto de negócio ou decisões em linguagem natural:

- Contratos ativos de fornecedores;
- Aditivos contratuais;
- Políticas e procedimentos internos;
- Histórico de e-mails relacionados a compras e faturamento;
- Instruções operacionais de contas a pagar.

### Estimativa de volume

Considerando uma operação de médio porte:

- 100 a 300 contratos ativos;
- 200 a 600 aditivos;
- alguns milhares de e-mails relevantes por ano;
- poucas dezenas de documentos normativos internos.

Assumindo de 5 a 20 chunks por documento contratual e um chunk por e-mail, o volume inicial provavelmente ficará na faixa de milhares de chunks, e não milhões.

Nessa escala, uma solução simples de embeddings com armazenamento local ou banco vetorial leve já é suficiente para uma primeira versão do sistema.

### O que fica fora do índice

Os seguintes dados não devem ser indexados:

- Valor atual de uma nota fiscal;
- Valor atual de um pedido de compra;
- Datas de vencimento;
- Situação do pagamento;
- Cadastro de fornecedor;
- Centro de custo;
- Status de aprovação.

Essas informações mudam constantemente e já possuem estrutura definida.

### O que será resolvido por consulta estruturada

As seguintes informações devem ser obtidas diretamente por consulta ao ERP ou banco relacional:

- Número do pedido;
- Valor do pedido;
- Valor da nota fiscal;
- Datas;
- Fornecedor;
- Status da conciliação;
- Centro de custo;
- Identificadores de contratos.

Esses casos exigem filtros exatos, consultas por chave ou comparação de valores, sendo inadequados para recuperação vetorial.

---

## 4. Estratégia de chunking

O projeto utilizará estratégias diferentes para cada tipo documental.

### Contratos

**Unidade natural:** cláusula ou seção.

Os contratos possuem estrutura hierárquica bem definida e a divisão por cláusulas preserva o contexto jurídico. Cada chunk deverá herdar o título da cláusula e da seção correspondente.

**Metadados:**

- tipo_documento;
- fornecedor;
- número_contrato;
- data_assinatura;
- versão;
- origem.

### Aditivos

**Unidade natural:** aditivo completo ou cláusula alterada.

Normalmente os aditivos são curtos e tratam de alterações específicas. Em muitos casos um único aditivo poderá ser mantido como um único chunk.

**Metadados:**

- tipo_documento;
- fornecedor;
- contrato_relacionado;
- data;
- versão.

### E-mails

**Unidade natural:** mensagem individual.

A decisão de negócio normalmente está concentrada em uma mensagem específica. Portanto, não há benefício em fragmentar o texto em blocos menores.

**Metadados:**

- remetente;
- destinatário;
- data;
- assunto;
- fornecedor relacionado.

### Políticas internas

**Unidade natural:** seção ou procedimento.

A divisão por seções preserva o significado das regras e facilita a recuperação precisa.

Sempre que houver referência a itens anteriores, o chunk deverá herdar os títulos necessários para manter a compreensão isolada.

**Metadados:**

- documento;
- capítulo;
- seção;
- versão;
- data de vigência.

### Considerações finais sobre chunking

A escolha do método de corte depende da natureza do documento. Contratos, e-mails e políticas possuem estruturas distintas e exigem estratégias diferentes. O princípio adotado será que cada chunk seja capaz de fazer sentido sozinho, mantendo contexto suficiente para que o agente explique e justifique uma decisão de conciliação sem depender da leitura integral da fonte original.
