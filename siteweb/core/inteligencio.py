#inteligencio.py

import pandas as pd
from groq import Groq
import re
from django.conf import settings
from datetime import datetime
import requests, time, os, json

# Escolha entre "ollama" ou "groq"
modeloIa = "groq"

# Lista de API Keys para fallback
API_KEYS = [
    "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",
    "#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"
]

MODELOI = "openai/gpt-oss-20b"
client = None

def configurar_cliente():
    global client
    for key in API_KEYS:
        try:
            client = Groq(api_key=key)
            print(f"✅ Cliente Groq configurado com chave {key[:10]}...")
            return True
        except Exception as e:
            print(f"[ERRO] Falha ao configurar cliente com chave {key[:10]}: {e}")
    return False

configurar_cliente()

# ------------------ Funções auxiliares ------------------
def salvar_json(dados, nome="analiseIa.json"):
    caminho = os.path.join(settings.MEDIA_ROOT, "concorrentesCompativeis", nome)
    try:
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
        print(f"✅ Resultados salvos em {caminho}")
    except Exception as e:
        print(f"[AVISO] Não foi possível salvar JSON: {e}")

def extrair_naoCompatibilidade(conteudo):
    return "NAO" if re.search(r'\bNAO\b', conteudo.upper()) else "SIM"

def extrair_compatibilidade(conteudo):
    return "SIM" if re.search(r'\bSIM\b', conteudo.upper()) else "NÃO"

def extrair_justificativa(conteudo):
    match = re.search(r'Justificativa\s*:\s*(.*)', conteudo, re.IGNORECASE)
    return match.group(1).strip() if match else "Sem justificativa"

def extrair_preco_sugerido(conteudo, preco_atual):
    match = re.search(r'Preco\s*sugerido\s*[:\-]?\s*[\$Rr\s]*([\d.,]+)', conteudo, re.IGNORECASE)
    if match:
        preco_str = match.group(1).replace(",", ".")
        try:
            return float(preco_str)
        except:
            return preco_atual
    return preco_atual

def extrair_justificativa_preco(conteudo):
    match = re.search(r'Justificativa\s*do\s*preco\s*[:\-]?\s*(.*)', conteudo, re.IGNORECASE)
    justificativa = match.group(1).strip() if match else ""
    return justificativa if justificativa else "Preço ajustado com base no concorrente"

def separar_nome_preco(coluna):
    nomes = []
    precos = []
    for valor in coluna:
        if isinstance(valor, str):
            partes = valor.split("|")
            preco_str = partes[-1].replace("R$", "").replace("\u00a0", "").replace(" ", "").replace(",", ".")
            nome = "|".join(partes[:-1]).strip()
            try:
                preco = float(preco_str)
            except:
                preco = 0.0
        else:
            nome = str(valor).strip()
            preco = 0.0
        nomes.append(nome)
        precos.append(preco)
    return nomes, precos

# ------------------ Função principal de comparação ------------------

def comparar_com_ia(principal, concorrente, preco_principal, preco_concorrente, nivelCompat):
    systemPrompt = "You are a product analysis assistant; your task is to analyze various products."

    prompt = f"""
Compare os dois produtos abaixo e diga se são compatíveis ou não.
Leve em consideração nome, marca, cor, unidade, voltagem (se houver) e ano do produto. Só aceite caso os parâmetros indicados combinem e tenham uma compatibilidade de no mínimo 95%.

Produto principal: {principal}, Preco: {preco_principal}
Produto concorrente: {concorrente}, Preco: {preco_concorrente}

⚠️ Instruções importantes para o preço:
- Sempre sugira um ajuste de preço para o produto principal.
- Se o preço do principal for maior que o concorrente, sugira uma redução para ficar um pouco abaixo.
- Se o preço do principal for menor que o concorrente, sugira um aumento leve, mas ainda abaixo do concorrente.
- Nunca deixe o campo de preço sugerido vazio.

Formato da resposta:
Compatibilidade: SIM ou NÃO
Justificativa: breve explicação.
Preco sugerido: valor sugerido para o produto principal
Justificativa do preco: breve explicação do ajuste de preco
"""

    conteudo = ""
    tentativas = 3
    for i in range(tentativas):
        try:
            response = client.chat.completions.create(
                model=MODELOI,
                messages=[
                    {"role": "system","content": systemPrompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            conteudo = response.choices[0].message.content.strip()
            if conteudo:
                break
        except Exception as e:
            print(f"[ERRO] Tentativa {i+1} falhou: {e}")
            configurar_cliente()
            time.sleep(1)

    if not conteudo:
        print("⚠️ IA não retornou resposta após várias tentativas.")
        return {
            "compatibilidade": None,
            "justificativa": "Falha na análise automática",
            "preco_sugerido": None,
            "justificativa_preco": None
        }

    compatibilidade = extrair_compatibilidade(conteudo)
    justificativa = extrair_justificativa(conteudo)

    if compatibilidade == "SIM":
        preco_sugerido = extrair_preco_sugerido(conteudo, preco_principal)
        justificativa_preco = extrair_justificativa_preco(conteudo)
    else:
        preco_sugerido = None
        justificativa_preco = None

    print("\n🔎 Comparação")
    print("Principal   :", principal)
    print("Concorrente :", concorrente)
    print("Preço Principal:", preco_principal)
    print("Preço Concorrente:", preco_concorrente)
    print("👉 Compatibilidade:", compatibilidade)
    print("👉 Justificativa:", justificativa)
    if compatibilidade == "SIM":
        print("👉 Preço sugerido:", preco_sugerido)
        print("👉 Justificativa do preço:", justificativa_preco)
        print("-" * 50)

    resultado = {
        "compatibilidade": compatibilidade,
        "justificativa": justificativa,
        "preco_sugerido": preco_sugerido,
        "justificativa_preco": justificativa_preco
    }

    salvar_json(resultado, nome="ultimaAnalise.json")

    return resultado

# ------------------ Pipeline de processamento ------------------

def processarDados(raspagem, nivelCompat):
    resultados_sim = {}
    resultados_nao = {}
    todas_analises = []

    for item in raspagem:
        principal = item.get("principal", {})
        concorrentes = item.get("concorrentes", [])

        nome_p = principal.get("nome")
        codigo_p = principal.get("codigoProduto")
        preco_p = principal.get("preco")

        info_principal = {
            "codigoProduto": codigo_p,
            "nome": nome_p,
            "preco": preco_p,
            "loja": principal.get("nomeLoja"),
            "imagem": principal.get("imagem"),
            "url": principal.get("url"),
            "frete": principal.get("frete"),
            "prazo": principal.get("prazo"),
        }

        resultados_sim[nome_p] = {
            "principal": info_principal,
            "concorrentes": []
        }

        resultados_nao[nome_p] = {
            "principal": info_principal,
            "concorrentes": []
        }

        for c in concorrentes:
            codigo_c = c.get("codigoProduto")
            nome_c = c.get("nome")
            preco_c = c.get("preco")

            if 1 == 1:
                linha = {
                    "nome": nome_c,
                    "preco": preco_c,
                    "imagem": c.get("imagem"),
                    "url": c.get("url"),
                    "frete": c.get("frete"),
                    "prazo": c.get("prazo"),
                    "loja": c.get("nomeLoja"),
                    "quantidadeCompras": c.get("quantidadeCompras"),
                    "compatibilidade": "SIM",
                    "justificativa": "Os dois códigos de produto são iguais, não precisou passar pela IA",
                    "preco_sugerido": "Sem preço sugerido",
                    "justificativa_preco": "Sem Justificativa",
                }
                print("\n🔎 Códigos de produtos iguais")
                print("Principal   :", nome_p)
                print("Concorrente :", nome_c)
                print("Preço Principal:", preco_p)
                print("Preço Concorrente:", preco_c)
            else:
                resultado_ia = comparar_com_ia(
                    principal=nome_p,
                    concorrente=nome_c,
                    preco_principal=preco_p,
                    preco_concorrente=preco_c,
                    nivelCompat=nivelCompat
                )

                linha = {
                    "nome": nome_c,
                    "preco": preco_c,
                    "loja": c.get("nomeLoja"),
                    "imagem": c.get("imagem"),
                    "url": c.get("url"),
                    "frete": c.get("frete"),
                    "prazo": c.get("prazo"),
                    "quantidadeCompras": c.get("quantidadeCompras"),
                    "compatibilidade": resultado_ia["compatibilidade"],
                    "justificativa": resultado_ia["justificativa"],
                    "preco_sugerido": resultado_ia["preco_sugerido"],
                    "justificativa_preco": resultado_ia["justificativa_preco"],
                }

            # Adiciona ao histórico geral
            todas_analises.append({
                "principal": nome_p,
                "nome_concorrente": nome_c,
                "preco_principal": preco_p,
                "preco_concorrente": preco_c,
                **linha
            })

            # Organiza nos grupos
            if linha["compatibilidade"] == "SIM":
                resultados_sim[nome_p]["concorrentes"].append(linha)
            else:
                resultados_nao[nome_p]["concorrentes"].append(linha)

    # Salva todas as análises em JSON para auditoria
    salvar_json(todas_analises, nome="analises_completas.json")

    return resultados_sim, resultados_nao, todas_analises


def comparacaoIa(raspagem, nivelCompat):
    destino = f"{settings.MEDIA_ROOT}/concorrentesCompativeis/analiseIa-{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
    resultados_sim, resultados_nao, todas_analises = processarDados(raspagem, nivelCompat)

    # Também salva os resultados compatíveis em JSON
    salvar_json(resultados_sim, nome="resultados_sim.json")
    salvar_json(resultados_nao, nome="resultados_nao.json")

    return resultados_sim