import os
import json
import time
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
Você é um agente especializado em Conciliação Contábil Procure-to-Pay (P2P).

Sua função é investigar divergências entre Notas Fiscais, Pedidos de Compra, Contratos, Aditivos e E-mails.

Você possui ferramentas para consultar o ERP e buscar documentos no repositório (corpus).
Use as ferramentas sempre que o usuário mencionar uma Nota Fiscal, Pedido, Fornecedor ou dúvida contábil.

Regras importantes:
1. Nunca invente contratos, valores, fornecedores ou justificativas.
2. Utilize apenas as evidências retornadas pelas ferramentas.
3. Cite sempre os arquivos ou registros utilizados no campo "fonte".
4. Se não houver evidências suficientes após consultar as ferramentas, marque "suficiente": false.

Quando tiver todas as evidências, responda APENAS em JSON válido no formato:
{
    "resultado": "Resumo objetivo da conclusão (ex: Divergência Justificada, Divergência Não Autorizada, Dados Insuficientes)",
    "fonte": ["ERP NF 00000", "nome_do_arquivo.txt"],
    "suficiente": true,
    "justificativa": "Explicação detalhada cruzando os valores do ERP com os documentos encontrados."
}
"""

# ============================================================
# BASE DE DADOS E FERRAMENTAS (TOOLS)
# ============================================================

ERP_DADOS = {
    # Caso 1 (Seu original): Divergência de Valor (Reajuste / Frete)
    "45887": {
        "pedido": "450019283",
        "fornecedor": "Fornecedor XYZ",
        "valor_nf": 104000.00,
        "valor_pedido": 100000.00,
        "status_erp": "Bloqueada - Divergência de Preço (+4%)"
    },
    # Caso 2 (Novo para apresentação): Divergência de Quantidade / Escopo
    "88910": {
        "pedido": "450019950",
        "fornecedor": "TechCorp Soluções",
        "item": "Licenças de Software Cloud",
        "qtd_nf": 120,
        "qtd_pedido": 100,
        "valor_nf": 60000.00,
        "valor_pedido": 50000.00,
        "status_erp": "Bloqueada - Divergência de Quantidade (+20 un.)"
    }
}

CORPUS_DIR = Path("corpus")


def consultar_erp(numero_nf: str) -> str:
    """Consulta os dados financeiros e de status de uma Nota Fiscal no ERP."""
    nf_limpa = str(numero_nf).strip()
    if nf_limpa in ERP_DADOS:
        return json.dumps({"nf": nf_limpa, **ERP_DADOS[nf_limpa]}, ensure_ascii=False)
    return json.dumps({"erro": f"Nota Fiscal {nf_limpa} não encontrada no ERP."})


def consultar_documentos(termos_busca: str) -> str:
    """Busca contratos, aditivos e e-mails na pasta corpus usando palavras-chave."""
    if not CORPUS_DIR.exists():
        return json.dumps({"aviso": "Pasta corpus não encontrada."})

    palavras = [p.lower() for p in termos_busca.split() if len(p) >= 3]
    encontrados = []

    for arquivo in CORPUS_DIR.rglob("*.txt"):
        try:
            conteudo = arquivo.read_text(encoding="utf-8")
            texto_lower = conteudo.lower()
            score = sum(1 for p in palavras if p in texto_lower)

            if score > 0:
                encontrados.append({
                    "arquivo": arquivo.name,
                    "texto": conteudo,
                    "score": score
                })
        except Exception:
            pass

    encontrados.sort(key=lambda x: x["score"], reverse=True)
    top_docs = [{"arquivo": d["arquivo"], "texto": d["texto"]} for d in encontrados[:3]]

    if not top_docs:
        return json.dumps({"aviso": "Nenhum documento relevante encontrado para esses termos."})

    return json.dumps(top_docs, ensure_ascii=False)


# Definição das ferramentas no padrão OpenAI
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "consultar_erp",
            "description": "Busca dados de Nota Fiscal, Pedido, Fornecedor e valores no sistema ERP.",
            "parameters": {
                "type": "object",
                "properties": {
                    "numero_nf": {
                        "type": "string",
                        "description": "O número da Nota Fiscal (ex: 45887 ou 88910)."
                    }
                },
                "required": ["numero_nf"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_documentos",
            "description": "Pesquisa contratos, aditivos e e-mails de aprovação no repositório de documentos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "termos_busca": {
                        "type": "string",
                        "description": "Palavras-chave como nome do fornecedor, número do pedido ou número da NF."
                    }
                },
                "required": ["termos_busca"]
            }
        }
    }
]

MAPA_FERRAMENTAS = {
    "consultar_erp": consultar_erp,
    "consultar_documentos": consultar_documentos
}


# ============================================================
# LOOP DO AGENTE (TOOL CALLING COM TRAVA ANTI-LOOP)
# ============================================================

def analisar_solicitacao(pergunta: str) -> RespostaConciliacao:
    inicio = time.time()
    tokens_totais = 0
    max_passos = 5  # Teto de segurança contra loops
    ja_consultou_docs = False

    mensagens = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": pergunta}
    ]

    for passo in range(max_passos):
        # Monta os argumentos da chamada de API
        kwargs_api = {
            "model": MODEL,
            "temperature": 0,
            "messages": mensagens
        }

        # Se já buscou documentos, não envia mais ferramentas para obrigar o modelo a concluir
        if not ja_consultou_docs:
            kwargs_api["tools"] = TOOLS_SCHEMA
            kwargs_api["tool_choice"] = "auto"

        response = client.chat.completions.create(**kwargs_api)

        if response.usage:
            tokens_totais += response.usage.total_tokens

        mensagem_assistente = response.choices[0].message
        mensagens.append(mensagem_assistente)

        # Se o modelo decidiu chamar ferramentas (e ainda tem permissão)
        if getattr(mensagem_assistente, "tool_calls", None):
            for tool_call in mensagem_assistente.tool_calls:
                nome_funcao = tool_call.function.name
                argumentos = json.loads(tool_call.function.arguments)

                # Print visual excelente para a sua apresentação!
                print(f"  [Agente -> Ferramenta] {nome_funcao}({argumentos})")

                funcao_python = MAPA_FERRAMENTAS.get(nome_funcao)
                retorno_ferramenta = funcao_python(**argumentos) if funcao_python else "Ferramenta desconhecida."

                # Ativa a trava assim que a busca nos documentos for realizada
                if nome_funcao == "consultar_documentos":
                    ja_consultou_docs = True

                mensagens.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": retorno_ferramenta
                })
        else:
            # O modelo terminou de investigar e gerou a resposta final
            latencia = round(time.time() - inicio, 2)
            print(f"\n[Observabilidade] Passos: {passo + 1} | Latência: {latencia}s | Tokens: {tokens_totais}")

            conteudo = mensagem_assistente.content or ""
            conteudo_limpo = conteudo.strip()
            if conteudo_limpo.startswith("```"):
                conteudo_limpo = conteudo_limpo.strip("`").removeprefix("json").strip()

            try:
                resultado = json.loads(conteudo_limpo)
                return RespostaConciliacao(**resultado)
            except Exception:
                return RespostaConciliacao(
                    resultado="Erro ao interpretar resposta do modelo.",
                    fonte=[],
                    suficiente=False,
                    justificativa=f"Saída bruta recebida: {conteudo}"
                )

    return RespostaConciliacao(
        resultado="Orçamento de passos esgotado.",
        fonte=[],
        suficiente=False,
        justificativa="O agente atingiu o limite máximo de consultas sem concluir."
    )



# ============================================================
# MAIN
# ============================================================

def main():
    print("\n==========================================")
    print("AGENTE DE CONCILIAÇÃO P2P (COM TOOL CALLING)")
    print("==========================================\n")

    while True:
        pergunta = input("Pergunta (ou sair): ").strip()
        if not pergunta:
            continue
        if pergunta.lower() == "sair":
            break

        resposta = analisar_solicitacao(pergunta)

        print("\n=== RESULTADO ===")
        print(json.dumps(resposta.model_dump(), indent=2, ensure_ascii=False))
        print()


if __name__ == "__main__":
    main()
