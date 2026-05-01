"""
import pandas as pd
import os
from datetime import datetime
from django.conf import settings
import re

def raspagem_concorrentes(produtos, numPage, cep):
    raspagem = []
    for produto in produtos:
        bloco = {
            "principal": {
                "codigoProduto": f"udjd1",
                "nome": produto["nome"],
                "preco": produto["preco"],
                "imagem": "https://via.placeholder.com/150",
                "url": "https://www.amazon.com.br/dp/fake",
                    "frete": 4.25,
                    "prazo": "18 de outubro",
                    "nomeLoja": "Lojina 1",
            },
            "concorrentes": [
                {
                    "codigoProduto": f"B07DTNB6SY",
                    "nome": f"Loja|{produto['nome']} Concorrente A ",
                    "preco": "R$ 129,99",
                    "imagem": "https://via.placeholder.com/150",
                    "url": "https://www.amazon.com.br/dp/fakeA",
                    "frete": 4.25,
                    "prazo": "18 de outubro",
                    "nomeLoja": "Lojina 2",
                },
                {
 "nome": f"Loja | {produto['nome']} Concorrente B",
                    "codigoProduto": f"udjd7",
                    "preco": "R$ 123,99",
                    "imagem": "https://via.placeholder.com/150",
                    "url": "https://www.amazon.com.br/dp/fakeB",
                    "frete": 4.25,
                    "prazo": "18 de outubro",
                    "nomeLoja": "Lojina 3",
                },
                 {
 "nome": f"Loja | {produto['nome']} Concorrente c ",
                  "codigoProduto": f"udjd6",
                    "preco": "R$ 110,99",
                    "imagem": "https://via.placeholder.com/150",
                    "url": "https://www.amazon.com.br/dp/fakeB",
                    "frete": 4.25,
                    "prazo": "18 de outubro",
                    "nomeLoja": "Lojina 4",
                },
                {
                "nome": f"Loja | {produto['nome']} Concorrente d ",
                                 "codigoProduto": f"udjd1",
                    "preco": "R$ 10010,99",
                    "imagem": "https://via.placeholder.com/150",
                    "url": "https://www.amazon.com.br/dp/fakeB",
                    "frete": 4.25,
                    "prazo": "18 de outubro",
                    "nomeLoja": "Lojina 5",
                },
                {
                "nome": f"Loja | {produto['nome']} Concorrente e",
                                 "codigoProduto": f"udjd5",
                    "preco": "R$ 100,99",
                    "imagem": "https://via.placeholder.com/150",
                    "url": "https://www.amazon.com.br/dp/fakeB",
                    "frete": 4.25,
                    "prazo": "18 de outubro",
                    "nomeLoja": "Lojina 6",
                },
                {
                "nome": f"Loja |{produto['nome']} | Concorrente e",
                                 "codigoProduto": f"udjd4",
                    "preco": "R$ 98,99",
                    "imagem": "https://via.placeholder.com/150",
                    "url": "https://www.amazon.com.br/dp/fakeB",
                    "frete": 4.25,
                    "prazo": "18 de outubro",
                    "nomeLoja": "Lojina 7",
                },
                {
                "nome": f"Loja | {produto['nome']} | Concorrente f",
                                 "codigoProduto": f"udjd3",
                    "preco": "R$ 140,99",
                    "imagem": "https://via.placeholder.com/150",
                    "url": "https://www.amazon.com.br/dp/fakeB",
                    "frete": 4.25,
                    "prazo": "18 de outubro",
                    "nomeLoja": "Lojina 8",
                },
                {
                "nome": f"Loja | {produto['nome']} | Concorrente g",
                                 "codigoProduto": f"udjd2",
                    "preco": "R$ 142,99",
                    "imagem": "https://via.placeholder.com/150",
                    "url": "https://www.amazon.com.br/dp/fakeB",
                    "frete": 4.25,
                    "prazo": "18 de outubro",
                    "nomeLoja": "Lojina",
                }
            ]
        }
        raspagem.append(bloco)

    linhas = []
    for bloco in raspagem:
        principal = bloco["principal"]
        principal_txt = f"{principal['nome']}|{principal['preco']}"
        for concorrente in bloco["concorrentes"]:
            concorrente_txt = f"{concorrente['nome']}|{concorrente['preco']}"
            linhas.append({
                "principal": principal_txt,
                "concorrente": concorrente_txt
            })

    df = pd.DataFrame(linhas)
    df = df.astype(str)
    os.makedirs("media", exist_ok=True)
    nome_arquivo = f"comparacao-{datetime.now().strftime('%d-%m-%Y_%H%M')}.parquet"
    #caminho = os.path.join("media/concorrentesRaspagem", nome_arquivo)
    caminho = f"{settings.MEDIA_ROOT}/concorrentesRaspagem/{nome_arquivo}"
    df.to_parquet(caminho, index=False, engine="pyarrow")
    return raspagem, nome_arquivo
"""

#rasparConc.py
import pandas as pd
import os
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError
from siteweb.core.utils import limpar_preco
import random
import time
from django.conf import settings

import re


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/117 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/116 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; rv:116.0) Gecko/20100101 Firefox/116.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15"
]

# Função para buscar concorrentes na Amazon
def buscar_concorrentes(produto_nome, max_pages, cep):
    # força limite de 5 páginas
    max_pages = min(max_pages, 5)
    print("\n==============================")
    print(f"🔎 Buscando concorrentes para: {produto_nome}")
    print(f"🏬 Loja principal: {produto_nome}")
    print("==============================\n")
    contador = 0
    url_base = f"https://www.amazon.com.br/s?k={produto_nome.replace(' ', '+')}"
    concorrentes = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            locale="pt-BR")
        page = context.new_page()

        # Atualiza CEP apenas uma vez na primeira página
        try:
            page.goto(url_base, timeout=60000)
            page.wait_for_selector("div.s-main-slot", timeout=30000)
            print("✅ Página inicial carregada com sucesso")

            print(f"📍 Atualizando CEP para {cep}")
            page.click('#nav-global-location-popover-link', force=True)
            page.wait_for_selector('#GLUXZipUpdateInput_0', state="visible")
            page.wait_for_selector('#GLUXZipUpdateInput_1', state="visible")
            cep_desejado = re.sub(r'\D', '', cep)
            page.fill('#GLUXZipUpdateInput_0', cep_desejado[:5])
            page.fill('#GLUXZipUpdateInput_1', cep_desejado[5:])
            page.click('#GLUXZipUpdate')
            page.wait_for_load_state("networkidle")
            print("✅ CEP atualizado com sucesso")
        except Exception as e:
            print(f"[AVISO] Não foi possível atualizar o CEP na página inicial: {e}")

        # Loop de páginas
        for page_num in range(1, max_pages + 1):
            if page_num > 1:
                url = f"{url_base}&page={page_num}"
                try:
                    page.goto(url, timeout=60000)
                    page.wait_for_selector("div.s-main-slot", timeout=30000)
                    print(f"\n--- Página {page_num} carregada ---")
                except TimeoutError:
                    print(f"[ERRO] Timeout ao carregar página {page_num}")
                    continue

            cards = page.query_selector_all("div[data-component-type='s-search-result']")
            print(f"📦 Produtos encontrados nesta página: {len(cards)}")

            for idx, card in enumerate(cards, start=1):
                print(f"\n➡️ Processando produto {idx}...")
                link_el = card.query_selector("a.a-link-normal")
                if not link_el:
                    print("⚠️ Nenhum link encontrado neste card")
                    continue

                href = link_el.get_attribute("href")
                url = f"https://www.amazon.com.br{href}" if href else None
                linkLoja = url

                preco_el = card.query_selector("span.a-price span.a-offscreen")
                preco = preco_el.inner_text().strip() if preco_el else None
                preco = limpar_preco(preco)
                try:
                    # pega o span que contém "Mais de X mil compras"
                    proof_el = page.query_selector("div[data-cy='reviews-block'] span.a-size-base.a-color-secondary")
                    quantidadeCompras = None
                    if proof_el:
                        texto = proof_el.inner_text().strip()
                        texto = texto.replace("\xa0", " ")  # normaliza espaço não quebrável
                        print("[DEBUG] Texto capturado:", texto)

                        # caso especial: "mil"
                        if "mil" in texto.lower():
                            match = re.search(r"(\d+)", texto)
                            if match:
                                quantidadeCompras = int(match.group()) * 1000
                        else:
                            match = re.search(r"(\d+)", texto)
                            quantidadeCompras = int(match.group()) if match else None

                except Exception as e:
                    print("[ERRO] Não foi possível capturar quantidade de compras:", e)
                    quantidadeCompras = None


                produto_page = None
                try:
                    produto_page = context.new_page()
                    produto_page.goto(url, timeout=60000)
                    time.sleep(random.uniform(0.5, 1.5))
                    produto_page.mouse.wheel(0, 1000)

                    produto_page.wait_for_selector("h1#title span#productTitle", timeout=30000)
                    nome_el = produto_page.query_selector("h1#title span#productTitle")
                    nome = nome_el.inner_text().strip() if nome_el else None
                    if not nome or "hq" in nome.lower():
                        print("⚠️ Produto ignorado (sem título válido)")
                        continue

                    nome_loja = produto_page.query_selector("span.offer-display-feature-text-message")
                    nomeLoja = nome_loja.inner_text().strip() if nome_loja else None

                    # Código ASIN
                    match = re.search(r"/dp/([A-Z0-9]+)/", linkLoja)
                    codigoProduto = match.group(1) if match else None

                    img_el = produto_page.query_selector("#imgTagWrapperId #landingImage")
                    imagem = img_el.get_attribute("src") if img_el else None

                    
                    # Especificações
                    rows = produto_page.query_selector_all("table.a-normal tbody tr")
                    for row in rows:
                        try:
                            label_el = row.query_selector("td.a-span3 span.a-text-bold")
                            value_el = row.query_selector("td.a-span9 span.po-break-word")
                            if label_el and value_el:
                                nome += f"|{label_el.inner_text().strip()}:{value_el.inner_text().strip()}"
                        except:
                            continue

                    # Frete e prazo
                    try:
                        frete_el = produto_page.query_selector(
                            '#mir-layout-DELIVERY_BLOCK-slot-PRIMARY_DELIVERY_MESSAGE_LARGE'
                        ) or produto_page.query_selector('.shipping-message')

                        if frete_el:
                            span_el = frete_el.query_selector("span[data-csa-c-delivery-price]")
                            if span_el:
                                frete = span_el.get_attribute("data-csa-c-delivery-price")
                                prazo = span_el.get_attribute("data-csa-c-delivery-time")
                                print(f"🚚 Frete capturado: {frete} | Prazo: {prazo}")
                            else:
                                frete, prazo = None, None
                                print("⚠️ Não foi possível capturar frete/prazo")
                        else:
                            frete, prazo = None, None
                            print("⚠️ Elemento de frete não encontrado")
                    except Exception as e:
                        print(f"[AVISO] Erro ao capturar frete/prazo: {e}")
                        frete, prazo = None, None
                    
                    concorrentes.append({
                        "codigoProduto": codigoProduto,
                        "nome": nome,
                        "preco": preco,
                        "imagem": imagem,
                        "url": linkLoja,
                        "frete": frete,
                        "prazo": prazo,
                        "nomeLoja": nomeLoja,
                        "quantidadeCompras": quantidadeCompras,
                    })
                    print(f"✅ Concorrente coletado: {nome} |QUantia:De Compras: {quantidadeCompras}")
                    contador+=1
                    if contador > 5:
                        break
                except Exception as e:
                    print(f"[ERRO] Falha ao acessar produto: {e}")
                finally:
                    if produto_page:
                        try:
                            produto_page.close()
                        except:
                            pass

        browser.close()
    return concorrentes

# Função principal
def raspagem_concorrentes(produtos, numPage, cep):
    raspagem = []  
    # força limite de 5 páginas
    num_paginas = min(int(numPage), 5)
    print(f"\n\n\n Recebido por raspagem concorrentes:\n {produtos}\n\n\n")
    for produto in produtos:
        print("\n==============================")
        print(f"📌 Iniciando coleta para produto principal: {produto['nome']}")
        print("==============================\n")
        
        concorrentes = buscar_concorrentes(produto["nome"], num_paginas, cep)
        print(f"\n🎉 COLETA FINALIZADA! Total coletado: {len(concorrentes)} concorrentes.")
        print(f"📊 Produto principal: {produto['nome']}")

        bloco = {
            "principal": {
                "nome": produto["nome"],
                "preco": limpar_preco(produto["preco"]),
                "imagem": produto.get("imagem", "..."),
                "url": produto["url"],
                "codigoProduto":produto["codigoProduto"],
                "frete": produto["frete"],
                "prazo": produto["prazo"],
            },
            "concorrentes": concorrentes
        }
        raspagem.append(bloco)

    linhas = []
    for bloco in raspagem:
        principal = bloco["principal"]
        principal_txt = f"{principal['nome']}|{principal['preco']}" 
        for concorrente in bloco["concorrentes"]:
            concorrente_txt = f"{concorrente['nome']}|{concorrente['preco']}"
            linhas.append({
                "principal": principal_txt,
                "concorrente": concorrente_txt
            })

    df = pd.DataFrame(linhas).astype(str)
    os.makedirs(f"{settings.MEDIA_ROOT}/concorrentesRaspagem", exist_ok=True)
    nome_arquivo = f"comparacao-{datetime.now().strftime('%d-%m-%Y_%H%M')}.parquet"
    caminho = f"{settings.MEDIA_ROOT}/concorrentesRaspagem/{nome_arquivo}"
    df.to_parquet(caminho, index=False, engine="pyarrow")

    return raspagem, nome_arquivo
