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

Você possui uma ferramenta chamada `consultar_erp_e_documentos`.
Sempre que o usuário perguntar sobre uma Nota Fiscal ou pedir uma análise de divergência, chame essa ferramenta passando o número da Nota Fiscal.
Se o usuário apenas cumprimentar ou fizer uma pergunta geral sem citar notas fiscais, responda educadamente sem chamar ferramentas.

Regras importantes:
1. Nunca invente contratos, valores, fornecedores ou justificativas.
2. Utilize apenas as evidências retornadas pela ferramenta.
3. Cite sempre os arquivos e registros utilizados no campo "fonte".
4. Se não houver documentos de justificativa ou se a NF não existir, marque "suficiente": false.

Responda APENAS em JSON válido seguindo exatamente este formato:
{
    "resultado": "Resumo objetivo da conclusão (ex: Divergência Justificada, Divergência Não Autorizada, Dados Insuficientes)",
    "fonte": ["ERP NF 00000", "nome_do_arquivo.txt"],
    "suficiente": true,
    "justificativa": "Explicação detalhada cruzando os valores do ERP com os documentos encontrados."
}
"""

# ============================================================
# BASE DE DADOS E FERRAMENTA UNIFICADA (ERP + RAG)
# ============================================================

ERP_DADOS = {
    # Caso 1: Divergência de Valor (Reajuste / Frete)
    "45887": {
        "pedido": "450019283",
        "fornecedor": "Fornecedor XYZ",
        "valor_nf": 104000.00,
        "valor_pedido": 100000.00,
        "status_erp": "Bloqueada - Divergência de Preço (+4%)"
    },
    # Caso 2: Divergência de Quantidade / Escopo
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

# CORPUS_DIR = Path("corpus")
CORPUS_DIR = Path(__file__).resolve().parent / "corpus"



def consultar_erp_e_documentos(numero_nf: str) -> str:
    """Consulta os dados da NF no ERP e busca automaticamente contratos e e-mails relacionados."""
    nf_limpa = str(numero_nf).strip()
    
    if nf_limpa not in ERP_DADOS:
        return json.dumps({
            "erro": f"Nota Fiscal {nf_limpa} não encontrada no ERP."
        }, ensure_ascii=False)

    dados_nf = {"nf": nf_limpa, **ERP_DADOS[nf_limpa]}
    
    # Busca automática nos documentos usando NF, Pedido e Fornecedor juntos
    termos = f"{nf_limpa} {dados_nf.get('pedido', '')} {dados_nf.get('fornecedor', '')}".lower()
    palavras = [p for p in termos.split() if len(p) >= 3]
    
    encontrados = []
    if CORPUS_DIR.exists():
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
    docs_relevantes = [
        {"arquivo": d["arquivo"], "texto": d["texto"]} 
        for d in encontrados[:3]
    ]

    return json.dumps({
        "dados_erp": dados_nf,
        "documentos_encontrados": docs_relevantes if docs_relevantes else "Nenhum documento de justificativa encontrado."
    }, ensure_ascii=False)


TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "consultar_erp_e_documentos",
            "description": "Busca os dados da Nota Fiscal no ERP e recupera automaticamente os contratos, aditivos e e-mails relacionados.",
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
    }
]

MAPA_FERRAMENTAS = {
    "consultar_erp_e_documentos": consultar_erp_e_documentos
}


# ============================================================
# LOOP DO AGENTE (TOOL CALLING RESILIENTE)
# ============================================================

def analisar_solicitacao(pergunta: str) -> RespostaConciliacao:
    inicio = time.time()
    tokens_totais = 0
    max_passos = 4

    mensagens = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": pergunta}
    ]

    for passo in range(max_passos):
        response = client.chat.completions.create(
            model=MODEL,
            temperature=0,
            messages=mensagens,
            tools=TOOLS_SCHEMA,
            tool_choice="auto"
        )

        if response.usage:
            tokens_totais += response.usage.total_tokens

        mensagem_assistente = response.choices[0].message
        mensagens.append(mensagem_assistente)

        # Se o modelo decidiu chamar a ferramenta
        if getattr(mensagem_assistente, "tool_calls", None):
            for tool_call in mensagem_assistente.tool_calls:
                nome_funcao = tool_call.function.name
                argumentos = json.loads(tool_call.function.arguments)

                print(f"  [Agente -> Ferramenta] {nome_funcao}({argumentos})")

                funcao_python = MAPA_FERRAMENTAS.get(nome_funcao)
                retorno = funcao_python(**argumentos) if funcao_python else "Ferramenta desconhecida."

                mensagens.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": retorno
                })
        else:
            # Resposta final gerada pelo modelo
            latencia = round(time.time() - inicio, 2)
            print(f"\n[Observabilidade] Passos: {passo + 1} | Latência: {latencia}s | Tokens: {tokens_totais}")

            conteudo = (mensagem_assistente.content or "").strip()
            
            # Remove blocos markdown caso o modelo retorne ```json
            if conteudo.startswith("```"):
                conteudo = conteudo.strip("`").removeprefix("json").strip()

            # Extrai o JSON mesmo que haja texto antes ou depois das chaves
            inicio_json = conteudo.find("{")
            fim_json = conteudo.rfind("}")
            
            if inicio_json != -1 and fim_json != -1:
                try:
                    resultado = json.loads(conteudo[inicio_json:fim_json + 1])
                    return RespostaConciliacao(**resultado)
                except Exception:
                    pass

            # Fallback elegante para respostas em texto livre (ex: saudações)
            return RespostaConciliacao(
                resultado="Conversa Geral / Resposta Direta",
                fonte=[],
                suficiente=True,
                justificativa=conteudo
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
    print("AGENTE SMART CONTAS A PAGAR")
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
