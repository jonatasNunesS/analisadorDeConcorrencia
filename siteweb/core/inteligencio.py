#inteligencio.py

import pandas as pd
from groq import Groq
import re
from django.conf import settings
from datetime import datetime
import requests

#Escolha entre "ollama" ou "groq"   
modeloIa = "groq"

if modeloIa == "ollama":
    ollama_url = "http://localhost:11434/api/generate"
    MODELOI = "mistral"
elif modeloIa == "groq":
    try:
        API_KEY = "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"#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
        MODELOI = "openai/gpt-oss-20b"
        client = Groq(api_key=API_KEY)
    except Exception as e:
        print("Erro ao configurar o cliente Groq:", e)
else:
    print("Modelo não detectado de ia")


# ------------------ Funções auxiliares ------------------
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

def comparar_com_ia(principal, concorrente, preco_principal, preco_concorrente,nivelCompat):
    systemPrompt = (
        "You are a product analysis assistant; your task is to analyze various products."
    )
    prompt = f"""

Compare os dois produtos abaixo e diga se são compatíveis ou não.
Leve em consideração nome, marca, cor, unidade, voltagem (se houver) e ano do produto. Só aceite caso os parâmetros indicados combinem e tenham uma compatibilidade de no mínimo 95%.

Se os valores forem muito diferentes, não considere isso na compatibilidade.

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
    
    if modeloIa == "ollama":
        payload = {
            "model": MODELOI,
            "prompt": prompt,
            "stream": False
        }
        response = requests.post(ollama_url, json=payload)
        if response.status_code == 200:
            conteudo = response.json()
            if 'response' in conteudo:
                conteudo = conteudo['response']
                print(conteudo)
            else:
                conteudo = str(conteudo)
        else:
            print(f"Error: {response.status_code}")
    elif modeloIa == "groq":
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
        except Exception as e:
            print("Erro ao chamar o modelo Groq:", e)
            conteudo = ""

    compatibilidadeNao = extrair_naoCompatibilidade(conteudo)

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

    return {
        "compatibilidade": compatibilidade,
        "justificativa": justificativa,
        "preco_sugerido": preco_sugerido,
        "justificativa_preco": justificativa_preco
    }

# ------------------ Pipeline de processamento ------------------

def processarDados(raspagem, nivelCompat):
    print("\n\nDados recebidinhos:\n", raspagem)

    resultados_sim = {}
    resultados_nao = {}
    todas_analises = []

    for item in raspagem:
        principal = item.get("principal", {})
        concorrentes = item.get("concorrentes", [])

        nome_p = principal.get("nome")
        preco_p = principal.get("preco")

        # Mantém o formato ANTIGO (corretíssimo)
        info_principal = {
            "nome": nome_p,
            "preco": preco_p,
            "loja": principal.get("loja"),
            "imagem": principal.get("imagem"),
            "url": principal.get("url"),
            "frete": principal.get("frete"),
            "link": principal.get("link"),   # caso exista
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
            nome_c = c.get("nome")
            preco_c = c.get("preco")

            resultado_ia = comparar_com_ia(
                principal=nome_p,
                concorrente=nome_c,
                preco_principal=preco_p,
                preco_concorrente=preco_c,
                nivelCompat=nivelCompat
            )

            linha = {
                # DADOS DO CONCORRENTE (com todos os campos preservados)
                "nome": nome_c,
                "preco": preco_c,
                "loja": c.get("loja"),
                "imagem": c.get("imagem"),
                "url": c.get("url"),
                "frete": c.get("frete"),
                "link": c.get("link"),

                # RESULTADO DA IA
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
            if resultado_ia["compatibilidade"] == "SIM":
                resultados_sim[nome_p]["concorrentes"].append(linha)
            else:
                resultados_nao[nome_p]["concorrentes"].append(linha)

    return resultados_sim, resultados_nao, todas_analises

def comparacaoIa(raspagem, nivelCompat):
    destino = f"{settings.MEDIA_ROOT}/concorrentesCompativeis/analiseIa-{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
    #destinos = processar_parquet(raspa, destino, nivelCompat)
    resultados_sim, resultados_nao, todas_analises = processarDados(raspagem, nivelCompat)
    return resultados_sim
"""
def comparacaoIa(arquivo, nivelCompat):
    # dados fictícios para teste
    resultados_sim = {
        "Impressora Epson L1250": {
            "principal": {
                "nome": "Impressora Epson L1250",
                "preco": 899.90,
                "loja": "Loja Oficial Epson",
                "imagem": "https://exemplo.com/impressora.jpg",
                "url": "https://exemplo.com/produto/impressora-l1250",
                "tipo": "principal"
            },
            "concorrentes": [
                {
                    "nome": "Impressora Epson L1250 Concorrente A",
                    "preco": 879.90,
                    "loja": "Loja Concorrente A",
                    "imagem": "https://exemplo.com/impressoraA.jpg",
                    "url": "https://exemplo.com/produto/impressora-concorrenteA",
                    "tipo": "concorrente"
                },
                {
                    "nome": "Impressora Epson L1250 Concorrente B",
                    "preco": 920.00,
                    "loja": "Loja Concorrente B",
                    "imagem": "https://exemplo.com/impressoraB.jpg",
                    "url": "https://exemplo.com/produto/impressora-concorrenteB",
                    "tipo": "concorrente"
                }
            ]
        },
        "Caixa de Som JBL Boombox 4": {
            "principal": {
                "nome": "Caixa de Som JBL Boombox 4",
                "preco": 3802.90,
                "loja": "Loja Oficial JBL",
                "imagem": "https://exemplo.com/jbl.jpg",
                "url": "https://exemplo.com/produto/jbl-boombox4",
                "tipo": "principal"
            },
            "concorrentes": [
                {
                    "nome": "Caixa de Som JBL Boombox 4 Concorrente X",
                    "preco": 3700.00,
                    "loja": "Loja Concorrente X",
                    "imagem": "https://exemplo.com/jblX.jpg",
                    "url": "https://exemplo.com/produto/jbl-concorrenteX",
                    "tipo": "concorrente"
                },
                {
                    "nome": "Caixa de Som JBL Boombox 4 Concorrente Y",
                    "preco": 3999.00,
                    "loja": "Loja Concorrente Y",
                    "imagem": "https://exemplo.com/jblY.jpg",
                    "url": "https://exemplo.com/produto/jbl-concorrenteY",
                    "tipo": "concorrente"
                }
            ]
        }
    }

    destino_nao = "media/concorrentesNaoCompativeis/analiseIa_naoCompat-teste.parquet"
    destino_sim = "media/concorrentesCompativeis/analiseIa-teste.parquet"

    return destino_nao, destino_sim, resultados_sim
"""