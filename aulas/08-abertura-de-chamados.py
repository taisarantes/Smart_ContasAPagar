# 08-abertura-de-chamados.py

import os
import json
import time
from dotenv import load_dotenv
from openai import OpenAI

# =====================================================================
# CONFIGURAÇÃO
# =====================================================================

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
)

MODELO = os.getenv("LLM_MODELO")

# Preços consultados na documentação do modelo utilizado.
# Atualize conforme o modelo escolhido.
# Valores por 1 milhão de tokens.

PRECOS = {
    "input": 0.15,
    "output": 0.60
}

# =====================================================================
# DADOS
# =====================================================================

MENSAGENS = [
    (
        "Meu pedido 48219 era pra chegar terça e até hoje nada. Já são 5 dias!",
        "entrega_atrasada",
        "48219"
    ),

    (
        "bom dia, o entregador deixou na rua de tras, numero 45. o meu é 145",
        "endereco_errado",
        None
    ),

    (
        "A caixa do pedido 77310 chegou toda amassada e a tampa do liquidificador trincou",
        "produto_avariado",
        "77310"
    ),

    (
        "vocês entregam no sábado?",
        "duvida",
        None
    ),

    (
        "Só pra dizer que o rapaz da entrega foi super educado, obrigada!",
        "elogio",
        None
    ),

    (
        "Pedido 90021 cancelado e recomprado como 90455, o 90455 não chegou",
        "entrega_atrasada",
        "90455"
    ),

    (
        "PEDIDO 12 MIL 340 ENTREGUE NO CEP ERRADO, EU MORO NO 04567890 E FOI PRO 04567089",
        "endereco_errado",
        "12340"
    ),

    (
        "Recebi o pedido n 55.102 com a tela rachada. Quero trocar.",
        "produto_avariado",
        "55102"
    ),
]

CATEGORIAS = [
    "entrega_atrasada",
    "endereco_errado",
    "produto_avariado",
    "duvida",
    "elogio"
]

CAMPOS = [
    "Categoria:",
    "Urgência:",
    "Pedido:",
    "Título:",
    "Descrição:",
    "Ação sugerida:"
]

# =====================================================================
# ETAPA 1 - EXTRAÇÃO
# =====================================================================

# temperature=0
# Extração é processamento de dados.
# A mesma mensagem deve gerar a mesma resposta.
#
# max_tokens=120
# JSON pequeno. Deve acomodar o pior caso.
#
# frequency_penalty=0
# Penalizar repetição atrapalharia a geração das chaves.
#
# presence_penalty=0
# Não queremos explorar informações novas.

EXTRACAO = {
    "temperature": 0,
    "max_tokens": 120,
    "frequency_penalty": 0,
    "presence_penalty": 0,
}

# =====================================================================
# ETAPA 2 - REDAÇÃO
# =====================================================================

# temperature=0.5
# Aqui existe espaço para variação controlada.
# O objetivo é escrever melhor, sem inventar fatos.
#
# max_tokens=300
# Espaço suficiente para título, descrição e ação.
#
# frequency_penalty=0
# Não há benefício claro neste cenário.
#
# presence_penalty=0
# Não incentivar criação de conteúdo novo.

REDACAO = {
    "temperature": 0.5,
    "max_tokens": 300,
    "frequency_penalty": 0,
    "presence_penalty": 0,
}

# =====================================================================
# CONTROLE DE CUSTO
# =====================================================================

tokens_extracao_prompt = 0
tokens_extracao_completion = 0

tokens_redacao_prompt = 0
tokens_redacao_completion = 0

# =====================================================================
# CHAMADAS COM RETRY
# =====================================================================


def chamar_modelo(messages, parametros):

    for tentativa in range(5):

        try:

            response = client.chat.completions.create(
                model=MODELO,
                messages=messages,
                temperature=parametros["temperature"],
                max_tokens=parametros["max_tokens"],
                frequency_penalty=parametros["frequency_penalty"],
                presence_penalty=parametros["presence_penalty"]
            )

            escolha = response.choices[0]

            if escolha.finish_reason == "length":
                raise RuntimeError(
                    "Resposta truncada (finish_reason=length)"
                )

            return response

        except Exception as e:

            if "429" in str(e):

                espera = 2 ** tentativa

                print(
                    f"[429] aguardando {espera}s..."
                )

                time.sleep(espera)

                continue

            raise

    raise RuntimeError(
        "Número máximo de tentativas excedido."
    )


# =====================================================================
# ETAPA 1
# =====================================================================

def extrair_dados(mensagem):

    global tokens_extracao_prompt
    global tokens_extracao_completion

    prompt = f"""
Você é responsável pela abertura de chamados.

Retorne APENAS JSON válido.

Categorias possíveis:
{CATEGORIAS}

Regras:

- categoria deve ser um dos valores válidos.
- pedido deve conter apenas dígitos.
- se não existir pedido, retornar null.
- CEP não é pedido.
- número de casa não é pedido.
- remover pontuação do pedido.
- converter pedidos escritos por extenso.
- se houver dois pedidos, escolher o pedido reclamado.
- se houver elogio e reclamação, priorizar a reclamação.

Formato:

{{
    "categoria": "...",
    "pedido": "...",
    "urgencia": "baixa|media|alta"
}}

Mensagem:

{mensagem}
"""

    resposta = chamar_modelo(
        [
            {
                "role": "user",
                "content": prompt
            }
        ],
        EXTRACAO
    )

    usage = resposta.usage

    tokens_extracao_prompt += usage.prompt_tokens
    tokens_extracao_completion += usage.completion_tokens

    texto = resposta.choices[0].message.content

    return json.loads(texto)


# =====================================================================
# ETAPA 2
# =====================================================================

def gerar_chamado(numero, mensagem, dados):

    global tokens_redacao_prompt
    global tokens_redacao_completion

    pedido = dados["pedido"]

    if pedido is None:
        pedido = "não informado"

    prompt = f"""
Você escreve chamados internos.

NÃO invente:
- nomes
- datas
- endereços
- números
- fatos

Use apenas a mensagem e os dados informados.

Mensagem:
{mensagem}

Dados:
{json.dumps(dados, ensure_ascii=False)}

Produza SOMENTE:

Título:
Descrição:
Ação sugerida:

A ação sugerida é obrigatória.

Ela deve:

- começar com verbo
- indicar quem deve agir
- ser específica
- ser acionável

Ações genéricas são proibidas:
"Verificar situação"
"Analisar caso"
"Encaminhar para análise"
"""

    resposta = chamar_modelo(
        [
            {"role": "user", "content": prompt}
        ],
        REDACAO
    )

    usage = resposta.usage

    tokens_redacao_prompt += usage.prompt_tokens
    tokens_redacao_completion += usage.completion_tokens

    corpo = resposta.choices[0].message.content

    chamado = f"""
=== CHAMADO #{numero:04d} ===

Categoria: {dados["categoria"]}
Urgência: {dados["urgencia"]}
Pedido: {pedido}

{corpo}
"""

    faltando = [
        campo
        for campo in CAMPOS
        if campo not in chamado
    ]

    if faltando:
        raise ValueError(
            f"Chamado incompleto: {faltando}"
        )

    return chamado


# =====================================================================
# CUSTO
# =====================================================================

def calcular_custo(prompt_tokens, completion_tokens):

    return (
        (prompt_tokens / 1_000_000) * PRECOS["input"]
        +
        (completion_tokens / 1_000_000) * PRECOS["output"]
    )


# =====================================================================
# PROCESSAMENTO
# =====================================================================

acertos_categoria = 0
acertos_pedido = 0

sucessos = 0
falhas = 0

print("\n=== PROCESSANDO MENSAGENS ===\n")

for indice, item in enumerate(MENSAGENS, start=1):

    mensagem = item[0]
    categoria_correta = item[1]
    pedido_correto = item[2]

    try:

        dados = extrair_dados(mensagem)

        if dados["categoria"] == categoria_correta:
            acertos_categoria += 1

        if dados["pedido"] == pedido_correto:
            acertos_pedido += 1

        chamado = gerar_chamado(
            indice,
            mensagem,
            dados
        )

        print(chamado)
        print("-" * 80)

        sucessos += 1

    except Exception as e:

        falhas += 1

        print(
            f"[ERRO] mensagem {indice}: {e}"
        )

# =====================================================================
# CUSTOS
# =====================================================================

custo_extracao = calcular_custo(
    tokens_extracao_prompt,
    tokens_extracao_completion
)

custo_redacao = calcular_custo(
    tokens_redacao_prompt,
    tokens_redacao_completion
)

custo_total = (
    custo_extracao +
    custo_redacao
)

media_por_chamado = (
    custo_total / sucessos
    if sucessos
    else 0
)

projecao_800 = media_por_chamado * 800

# Em geral a redação costuma custar mais.
# O prompt é maior e a saída é muito maior.
# Na extração o output é apenas um JSON pequeno.

print()
print("=== GABARITO ===")
print(
    f"Categoria: {acertos_categoria}/8"
)
print(
    f"Pedido: {acertos_pedido}/8"
)

print()
print("=== CUSTOS ===")
print(
    f"Extração: US$ {custo_extracao:.6f}"
)
print(
    f"Redação: US$ {custo_redacao:.6f}"
)
print(
    f"Total: US$ {custo_total:.6f}"
)

print(
    f"Custo médio/chamado: US$ {media_por_chamado:.6f}"
)

print(
    f"Projeção 800 chamados/dia: US$ {projecao_800:.4f}"
)

print()
print("=== RESUMO ===")
print(f"Sucessos: {sucessos}")
print(f"Falhas: {falhas}")