# main.py

import os
import json
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

# ============================================================
# CONFIGURAÇÃO
# ============================================================

load_dotenv()

MODEL = os.getenv(
    "LLM_MODELO",
    "liquid/lfm-3-1.7b:free"
)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL")
)

# ============================================================
# MODELO DE SAÍDA
# ============================================================

class RespostaConciliacao(BaseModel):
    resultado: str
    fonte: list[str]
    suficiente: bool
    justificativa: str


# ============================================================
# PROMPT DO SISTEMA
# ============================================================

SYSTEM_PROMPT = """
Você é um agente especializado em Conciliação Contábil
Procure-to-Pay (P2P).

Sua função é analisar divergências entre:

- Notas Fiscais
- Pedidos de Compra
- Contratos
- Aditivos Contratuais
- Histórico de E-mails

Regras importantes:

1. Nunca invente contratos.
2. Nunca invente fornecedores.
3. Nunca invente justificativas.
4. Utilize apenas as evidências fornecidas.
5. Cite sempre as fontes utilizadas.
6. Se não houver evidências suficientes,
   responda que não foi possível concluir.

Responda apenas em JSON válido.

Formato:

{
    "resultado": "...",
    "fonte": ["..."],
    "suficiente": true,
    "justificativa": "..."
}
"""


# ============================================================
# ERP SIMULADO
# ============================================================

ERP_DADOS = {
    "45887": {
        "pedido": "450019283",
        "fornecedor": "Fornecedor XYZ",
        "valor_nf": 104000.00,
        "valor_pedido": 100000.00
    }
}


def consultar_erp(texto):

    resultados = []

    for nf, dados in ERP_DADOS.items():

        if nf in texto:
            resultados.append({
                "nf": nf,
                **dados
            })

    return resultados


# ============================================================
# RAG SIMPLES
# ============================================================

CORPUS_DIR = Path("corpus")


def carregar_documentos():

    docs = []

    if not CORPUS_DIR.exists():
        return docs

    for arquivo in CORPUS_DIR.rglob("*.txt"):

        try:

            conteudo = arquivo.read_text(
                encoding="utf-8"
            )

            docs.append({
                "arquivo": arquivo.name,
                "texto": conteudo
            })

        except Exception:
            pass

    return docs


def recuperar_contexto(pergunta):

    docs = carregar_documentos()

    pergunta = pergunta.lower()

    encontrados = []

    for doc in docs:

        texto = doc["texto"].lower()

        score = 0

        for palavra in pergunta.split():

            if palavra in texto:
                score += 1

        if score > 0:

            encontrados.append({
                "arquivo": doc["arquivo"],
                "texto": doc["texto"],
                "score": score
            })

    encontrados.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return encontrados[:3]


# ============================================================
# AGENTE
# ============================================================

def analisar_solicitacao(pergunta):

    dados_erp = consultar_erp(pergunta)

    documentos = recuperar_contexto(
        pergunta
    )

    contexto_docs = ""

    fontes = []

    for doc in documentos:

        fontes.append(doc["arquivo"])

        contexto_docs += (
            f"\n\nDocumento: "
            f"{doc['arquivo']}\n"
            f"{doc['texto']}"
        )

    prompt = f"""
Solicitação do usuário:

{pergunta}

Dados ERP:

{json.dumps(
    dados_erp,
    indent=2,
    ensure_ascii=False
)}

Documentos recuperados:

{contexto_docs}
"""

    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    conteudo = (
        response.choices[0]
        .message
        .content
    )

    try:

        resultado = json.loads(conteudo)

        if not resultado.get("fonte"):
            resultado["fonte"] = fontes

        return RespostaConciliacao(
            **resultado
        )

    except Exception:

        return RespostaConciliacao(
            resultado="Erro ao interpretar resposta do modelo.",
            fonte=[],
            suficiente=False,
            justificativa="O modelo não retornou um JSON válido."
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n========================")
    print("AGENTE DE CONCILIAÇÃO")
    print("========================\n")

    while True:

        pergunta = input(
            "Pergunta (ou sair): "
        ).strip()

        if pergunta.lower() == "sair":
            break

        resposta = analisar_solicitacao(
            pergunta
        )

        print("\n=== RESULTADO ===")

        print(
            json.dumps(
                resposta.model_dump(),
                indent=2,
                ensure_ascii=False
            )
        )

        print()

if __name__ == "__main__":
    main()