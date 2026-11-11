import os
import json
import requests

from dotenv import load_dotenv
from openai import OpenAI

# =========================
# CONFIGURAÇÃO
# =========================

load_dotenv()

client = OpenAI(
    base_url=os.environ.get(
        "LLM_BASE_URL",
        "https://openrouter.ai/api/v1"
    ),
    api_key=os.environ.get("OPENAI_API_KEY"),
)

MODELO = os.environ.get(
    "LLM_MODELO",
    "liquid/lfm-3-1.7b:free"
)

# =========================
# FERRAMENTAS
# =========================

def buscar_endereco(cep):
    try:

        cep = str(cep).replace("-", "").strip()

        response = requests.get(
            f"https://brasilapi.com.br/api/cep/v2/{cep}",
            timeout=10
        )

        if response.status_code == 404:
            return {
                "erro": f"CEP {cep} não encontrado."
            }

        response.raise_for_status()

        dados = response.json()

        return {
            "cep": dados["cep"],
            "rua": dados["street"],
            "bairro": dados["neighborhood"],
            "cidade": dados["city"],
            "estado": dados["state"]
        }

    except Exception as e:
        return {
            "erro": str(e)
        }


def listar_feriados(ano):

    try:

        response = requests.get(
            f"https://brasilapi.com.br/api/feriados/v1/{ano}",
            timeout=10
        )

        response.raise_for_status()

        return {
            "ano": ano,
            "feriados": response.json()
        }

    except Exception as e:
        return {
            "erro": str(e)
        }


FERRAMENTAS = {
    "buscar_endereco": buscar_endereco,
    "listar_feriados": listar_feriados
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "buscar_endereco",
            "description": "Consulta um CEP e retorna endereço.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cep": {
                        "type": "string"
                    }
                },
                "required": ["cep"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "listar_feriados",
            "description": "Lista os feriados de um ano.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ano": {
                        "type": "integer"
                    }
                },
                "required": ["ano"]
            }
        }
    }
]


# =========================
# ETAPA 1
# COLETA DOS DADOS
# =========================

messages = [
    {
        "role": "system",
        "content": """
Você é um assistente de entregas.

Colete:
- CEP de destino
- Data da entrega

Converse de forma amigável.

Quando possuir ambos os dados,
responda SOMENTE com JSON válido:

{
  "cep": "01310100",
  "data": "2026-02-16"
}

Regras:
- CEP somente números
- Data no formato yyyy-mm-dd
- Não escreva nada fora do JSON
"""
    }
]

print("=== Assistente de Entregas ===")

while True:

    response = client.chat.completions.create(
        model=MODELO,
        messages=messages
    )

    resposta = response.choices[0].message.content

    print("\nBot:", resposta)

    try:

        coleta = json.loads(resposta)

        if "cep" in coleta and "data" in coleta:
            print("\nDados coletados com sucesso!")
            break

    except Exception:
        pass

    usuario = input("Você: ")

    messages.append({
        "role": "user",
        "content": usuario
    })

    messages.append({
        "role": "assistant",
        "content": resposta
    })


# =========================
# VALIDA JSON
# =========================

try:

    coleta = json.loads(resposta)

except json.JSONDecodeError:

    print("Erro: JSON inválido.")
    exit()


# =========================
# ETAPA 2
# AGENTE COM FERRAMENTAS
# =========================

messages = [
    {
        "role": "system",
        "content": """
Você é um assistente de entregas.

Utilize as ferramentas disponíveis.

Passos:

1. Consultar o endereço do CEP.
2. Consultar os feriados do ano.
3. Verificar se a data da entrega é feriado.
4. Gerar um resumo final.

Nunca invente endereço.
Nunca invente feriado.

Se a ferramenta retornar erro,
explique o problema ao usuário.
"""
    },
    {
        "role": "user",
        "content": json.dumps(
            coleta,
            ensure_ascii=False
        )
    }
]

for passo in range(8):

    response = client.chat.completions.create(
        model=MODELO,
        messages=messages,
        tools=TOOLS
    )

    resposta = response.choices[0].message

    messages.append(resposta)

    # resposta final
    if not resposta.tool_calls:

        print("\n=== RESULTADO ===")
        print(resposta.content)
        break

    # executa ferramentas
    for chamada in resposta.tool_calls:

        argumentos = json.loads(
            chamada.function.arguments or "{}"
        )

        print(
            f"[ferramenta] "
            f"{chamada.function.name}"
            f"({argumentos})"
        )

        resultado = FERRAMENTAS[
            chamada.function.name
        ](**argumentos)

        messages.append({
            "role": "tool",
            "tool_call_id": chamada.id,
            "content": json.dumps(
                resultado,
                ensure_ascii=False
            )
        })

else:

    print(
        "Não consegui concluir a tarefa em 8 passos."
    )