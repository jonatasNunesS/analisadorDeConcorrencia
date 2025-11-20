import pandas as pd
from groq import Groq
import re
from django.conf import settings
from datetime import datetime
import requests

modeloIa = "ollama"

if modeloIa == "ollama":
    ollama_url = "http://localhost:11434/api/generate"
    MODELOI = "mistral"
elif modeloIa == "groq":
    API_KEY = "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"
    MODELOI = "openai/gpt-oss-20b"
    client = Groq(api_key=API_KEY)
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
    prompt = f"""
Compare os dois produtos abaixo e diga se são compatíveis ou não.
Leve em consideração nome, marca, cor, unidade, voltagem (se houver) e ano do produto. Só aceite caso os parâmetros indicados combinem e tenham uma compatibilidade de no mínimo {nivelCompat}%.

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
        response = client.chat.completions.create(
            model=MODELOI,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )   
        conteudo = response.choices[0].message.content.strip()


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

def processar_parquet(origem_path, destino_path,nivelCompat):
    df = pd.read_parquet(origem_path)

    df["nome_principal"], df["preco_principal"] = separar_nome_preco(df["principal"])
    df["nome_concorrente"], df["preco_concorrente"] = separar_nome_preco(df["concorrente"])

    resultados = df.apply(
        lambda row: comparar_com_ia(
            row["nome_principal"],
            row["nome_concorrente"],
            row["preco_principal"],
            row["preco_concorrente"],
            nivelCompat
        ),
        axis=1
    )

    df["compatibilidade"] = resultados.apply(lambda x: x["compatibilidade"])
    df["justificativa"] = resultados.apply(lambda x: x["justificativa"])
    df["preco_sugerido"] = resultados.apply(lambda x: x["preco_sugerido"])
    df["justificativa_preco"] = resultados.apply(lambda x: x["justificativa_preco"])

    df.drop(columns=["principal", "concorrente"], inplace=True)

    df_final = df[df["compatibilidade"] == "SIM"]
    df_nao = df[df["compatibilidade"] == "NÃO"]
    
    resultados_sim = df_final.to_json(orient="records")

    df_final.to_parquet(destino_path, index=False)
    print("\n\n✅ Novo parquet salvo em:", destino_path)


    destino_nao = destino_path.replace("concorrentesCompativeis/analiseIa-", "concorrentesNaoCompativeis/analiseIa_naoCompat-")
    df_nao.to_parquet(destino_nao, index=False)
    print("\n⚠️ Parquet com incompatibilidades salvo em:", destino_nao)
    
    return destino_nao, destino_path, resultados_sim

def comparacaoIa(arquivo, nivelCompat):
    origem = f"{settings.MEDIA_ROOT}/concorrentesRaspagem/{arquivo}"
    destino = f"{settings.MEDIA_ROOT}/concorrentesCompativeis/analiseIa-{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
    destinos = processar_parquet(origem, destino, nivelCompat)
    return destinos
    
    
