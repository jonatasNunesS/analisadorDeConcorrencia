
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
                "nome": produto["nome"],
                "preco": produto["preco"],
                "imagem": "https://via.placeholder.com/150",
                "url": "https://www.amazon.com.br/dp/fake",
                    "frete": 4.25,
                    "prazo": "18 de outubro",
            },
            "concorrentes": [
                {
                    "nome": f"{produto['nome']} Concorrente A ",
                    "preco": "R$ 129,99",
                    "imagem": "https://via.placeholder.com/150",
                    "url": "https://www.amazon.com.br/dp/fakeA",
                    "frete": 4.25,
                    "prazo": "18 de outubro",
                },
                {
 "nome": f"Loja | {produto['nome']} Concorrente B",
                    "preco": "R$ 123,99",
                    "imagem": "https://via.placeholder.com/150",
                    "url": "https://www.amazon.com.br/dp/fakeB",
                    "frete": 4.25,
                    "prazo": "18 de outubro",
                },
                 {
 "nome": f"Loja | {produto['nome']} Concorrente c ",
                    "preco": "R$ 110,99",
                    "imagem": "https://via.placeholder.com/150",
                    "url": "https://www.amazon.com.br/dp/fakeB",
                    "frete": 4.25,
                    "prazo": "18 de outubro",
                },
                {
                "nome": f"Loja | {produto['nome']} Concorrente d ",
                    "preco": "R$ 10010,99",
                    "imagem": "https://via.placeholder.com/150",
                    "url": "https://www.amazon.com.br/dp/fakeB",
                    "frete": 4.25,
                    "prazo": "18 de outubro",
                },
                {
                "nome": f"Loja | {produto['nome']} Concorrente e",
                    "preco": "R$ 100,99",
                    "imagem": "https://via.placeholder.com/150",
                    "url": "https://www.amazon.com.br/dp/fakeB",
                    "frete": 4.25,
                    "prazo": "18 de outubro",
                },
                {
                "nome": f"Loja |{produto['nome']} | Concorrente e",
                    "preco": "R$ 98,99",
                    "imagem": "https://via.placeholder.com/150",
                    "url": "https://www.amazon.com.br/dp/fakeB",
                    "frete": 4.25,
                    "prazo": "18 de outubro",
                },
                {
                "nome": f"Loja | {produto['nome']} | Concorrente f",
                    "preco": "R$ 140,99",
                    "imagem": "https://via.placeholder.com/150",
                    "url": "https://www.amazon.com.br/dp/fakeB",
                    "frete": 4.25,
                    "prazo": "18 de outubro",
                },
                {
                "nome": f"Loja | {produto['nome']} | Concorrente g",
                    "preco": "R$ 142,99",
                    "imagem": "https://via.placeholder.com/150",
                    "url": "https://www.amazon.com.br/dp/fakeB",
                    "frete": 4.25,
                    "prazo": "18 de outubro",
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

#codigo ia
import pandas as pd
import os
from datetime import datetime
from playwright.sync_api import sync_playwright
import random
import time
from django.conf import settings
from siteweb.core.servicos import separarLoja
import re

# Função para buscar concorrentes na Amazon
def buscar_concorrentes(produto_nome, max_pages, cep):
    partesName  = separarLoja(produto_nome)
    print("\n---\nBuscando concorrentes para:", partesName[1],"\nLoja:", partesName[0],"\n---\n")
    url_base = f"https://www.amazon.com.br/s?k={partesName[1].replace(' ', '+')}"
    concorrentes = []
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/117 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/116 Safari/537.36"
    ]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            locale="pt-BR")
        page = context.new_page()

        for page_num in range(1, max_pages + 1):
            url = f"{url_base}&page={page_num}"
            page.goto(url, timeout=60000)
            page.wait_for_selector("div.s-main-slot")

            cards = page.query_selector_all("div[data-component-type='s-search-result']")
            
            for card in cards:
                link_el = card.query_selector("a.a-link-normal")
                if not link_el:
                    print("Nenhum link encontrado: ", link_el)
                    continue
                href = link_el.evaluate('node => node.getAttribute("href")') if link_el else None
                 
                url = f"https://www.amazon.com.br{href}" if href else None
                linkLoja = url
                preco_el = card.query_selector("span.a-price span.a-offscreen")
                preco = preco_el.inner_text().strip() if preco_el else None
                try:
                    produto_page = context.new_page()
                    produto_page.goto(url, timeout=60000)
                    time.sleep(2)
                    produto_page.mouse.wheel(0, 1000)

                    produto_page.wait_for_selector("h1#title span#productTitle")
                    nome_el = produto_page.query_selector("h1#title span#productTitle")
                    if not nome_el:
                        raise Exception("Titulo não encontrado")
                    nome = nome_el.inner_text().strip() if nome_el else None
                    if not nome or "hq" in nome.lower():
                        continue
                    nome_loja = produto_page.query_selector("span.offer-display-feature-text-message")
                    nomeLoja = nome_loja.inner_text().strip() if nome_loja else None
                    #Depois criar um controle aqui para verificar se e da loja principal

                    img_el = produto_page.query_selector("#imgTagWrapperId #landingImage")
                    imagem = img_el.get_attribute("src") if img_el else None

                    # Seleciona todas as linhas da tabela de especificações
                    rows = produto_page.query_selector_all("table.a-normal tbody tr")

                    for row in rows:
                        try:
                            label_el = row.query_selector("td.a-span3 span.a-text-bold")
                            value_el = row.query_selector("td.a-span9 span.po-break-word")

                            label = label_el.inner_text().strip() if label_el else None
                            value = value_el.inner_text().strip() if value_el else None

                            if label and value:
                                nome += f"|{label}:{value}"
                        except Exception as e:
                            print(f"Erro ao extrair especificação: {e}")
                            continue
                    # Atualiza o CEP
                    produto_page.wait_for_selector('#glow-ingress-line2', state="visible", timeout=10000)
                    cep_el = produto_page.query_selector('#glow-ingress-line2')
                    cep_atual = cep_el.inner_text().strip() if cep_el else None
                    cep_atual = re.sub(r'\D', '', cep_atual) if cep_atual else None
                    cep_desejado = re.sub(r'\D', '', cep)

                    if cep_atual == cep_desejado:
                        print(f"CEP já está correto: {cep_atual}")
                        # Não tenta clicar de novo, segue direto para capturar frete
                    else:
                        print(f"Atualizando CEP: {cep_atual} -> {cep_desejado}")
                        produto_page.evaluate("window.scrollTo(0, 0)")
                        produto_page.click('#nav-global-location-popover-link', force=True)

                        produto_page.wait_for_selector('#GLUXZipUpdateInput_0', state="visible")
                        produto_page.wait_for_selector('#GLUXZipUpdateInput_1', state="visible")

                        cep_parte1, cep_parte2 = cep_desejado[:5], cep_desejado[5:]
                        produto_page.fill('#GLUXZipUpdateInput_0', cep_parte1)
                        produto_page.fill('#GLUXZipUpdateInput_1', cep_parte2)

                        produto_page.click('#GLUXZipUpdate')
                        produto_page.wait_for_load_state("networkidle")

                        cep_el = produto_page.query_selector('#glow-ingress-line2')
                        cep_atualizado = cep_el.inner_text().strip() if cep_el else None
                        print("CEP atualizado:", cep_atualizado)

                        frete_el = produto_page.query_selector(
                            '#mir-layout-DELIVERY_BLOCK-slot-PRIMARY_DELIVERY_MESSAGE_LARGE'
                        ) or produto_page.query_selector('.shipping-message')

                        if frete_el:
                            # Agora seleciona o span interno que tem os atributos
                            span_el = frete_el.query_selector("span[data-csa-c-delivery-price]")

                            if span_el:
                                frete = span_el.get_attribute("data-csa-c-delivery-price")
                                prazo = span_el.get_attribute("data-csa-c-delivery-time")

                                print("Preço:", frete)
                                print("Prazo:", prazo)
                            else:
                                print("Span com atributos não encontrado")
                        else:
                            print("Elemento de frete não encontrado")
                        print("Frete: ", frete)
                        print("Prazo ", prazo)


                    nome = f"{nomeLoja}|{nome}" if nomeLoja else nome

                    print("Certo", nome)

                    concorrentes.append({
                        "nome": nome,
                        "preco": preco if preco else print(f"O preço de {nome} não foi encontrado na raspagem.\n"),
                        "imagem": imagem if imagem else print(f"A imagem de {nome} não foi encontrada na raspagem.\n"),
                        "url": linkLoja if linkLoja else print(f"O link de {nome} não foi encontrado na raspagem.\n"),
                        "frete": frete if frete else print(f"O frete de {nome} não foi encontrado na raspagem.\n"),
                        "prazo": prazo if prazo else print(f"O prazo de {nome} não foi encontrado na raspagem.\n"),
                    })
                    produto_page.close()  
                except Exception as e:
                    print(f"Erro ao acessar {url}: {e}")
                    continue

                """"""
        browser.close()
    return concorrentes

# Função principal
def raspagem_concorrentes(produtos, numPage, cep):
    raspagem = []  
    num_paginas = int(numPage)
    for produto in produtos:
        concorrentes = buscar_concorrentes(produto["nome"], num_paginas, cep)
        print(f"1° produto {produto["nome"]}")
        bloco = {
            "principal": {
                "nome": produto["nome"],
                "preco": produto["preco"],
                "imagem": "...",  # pode ser preenchido depois
                "url": "..."
            },
            "concorrentes": concorrentes
        }
        raspagem.append(bloco)

    linhas = []
    #Cria um dataframe pra salva em parquet
    
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