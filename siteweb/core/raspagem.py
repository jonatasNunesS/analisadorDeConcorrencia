"""import json
from playwright.sync_api import sync_playwright
import random
import time
import re

def raspar_dados(playwright, BASE_URL, cepEntrega):
    status_produtos = {}
    browser = playwright.chromium.launch(headless=False)
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/117 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/116 Safari/537.36"
    ]
    viewport={"width": 1280, "height": 800}
    context = browser.new_context(
        user_agent=random.choice(USER_AGENTS),
        viewport={"width":1280,"height":800}
    )
    page = context.new_page()
    print("[INFO] Acessando página...")
    try:
        page.goto(BASE_URL, timeout=50000)
    except Exception as e:
        print(f"[ERRO] Falha ao acessar {linkProduto}: {e}")
    time.sleep(2)
    page.mouse.wheel(0, 1000)
    time.sleep(1)
    if "algo deu errado" in page.content():
        print("[ERRO] Página de erro detectada. Abortando raspagem.")
        browser.close()
        return []

    page.wait_for_selector('div.s-main-slot', timeout=15000)
    print("[INFO] Página carregada, buscando produtos...")

    product_cards = page.query_selector_all('div.s-main-slot div[data-asin]:not([data-asin=""])')
    print(f"[INFO] Total de blocos com data-asin: {len(product_cards)}")

    produtos = []
    for i, card in enumerate(product_cards, 1):
        name_el = card.query_selector('div[data-cy="title-recipe"] a') \
          or card.query_selector('h2.a-size-mini a.a-link-normal') \
          or card.query_selector('h2.a-size-base a.a-link-normal')
        if not name_el:
            print("Nome do produto não encontrado")
            continue
        nome = name_el.inner_text().strip() if name_el else None
        if not nome or "hq" in nome.lower():
            continue
        linkProduto = "https://www.amazon.com.br" + name_el.get_attribute('href') if name_el else None
        if not linkProduto:
                print(f"[SKIP] Produto {i} ignorado (link não encontrado).")
                continue
        print("Link recebido:", {linkProduto})
    
        def pegarDados(browser, linkProduto, cepEntrega, tentativas=1):
            for tentativa in range(tentativas):
                try:
                    context = browser.new_context(
                        user_agent=random.choice(USER_AGENTS),
                        locale="pt-BR")
                    produto_page = context.new_page()
                    produto_page.goto(linkProduto, timeout=50000)
                    time.sleep(2)
                    produto_page.mouse.wheel(0, 1000)
                    time.sleep(1)
                    produto_page.wait_for_selector("h1#title span#productTitle", timeout=60000)
                    nome_el = produto_page.query_selector("h1#title span#productTitle")
                    if not nome_el:
                        print("Nome do produto não encontrado")
                        status_produtos[nome] = {"url": linkProduto, "status": "Nome não escontrado"}
                    nome = nome_el.inner_text().strip() if nome_el else None
                    if not nome or "hq" in nome.lower():
                        status_produtos[nome] = {"url": linkProduto, "status": "Nome não escontrado"}
                        continue
                    print("Nome:", nome)

                    match = re.search(r"/dp/([A-Z0-9]+)/", linkProduto)
                    codigoProduto = match.group(1)
                    if not codigoProduto:
                        status_produtos[nome] = {"url": linkProduto, "status": "Codigo não escontrado"}
                        print("Codigo do produto não encontrado")
                        continue
                    print("Codigo produto:",codigoProduto)

                    price_el = produto_page.query_selector("span.a-price span.a-offscreen")
                    price = price_el.inner_text().strip() if price_el else None
                    if not price:
                        status_produtos[nome] = {"url": linkProduto, "status": "Preço não escontrado"}
                        print(f"[SKIP] Produto {i} ignorado (preço não encontrado {price}).")
                        continue
                    status_produtos[nome] = {"url": linkProduto, "status": "ok", "preco": price}

                    print("Preço:", {price})

                    nome_loja = produto_page.query_selector("span.offer-display-feature-text-message")
                    nomeLoja = nome_loja.inner_text().strip() if nome_loja else None
                    print("Nome loja: ", nome)

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
                    print("Nome completo: ",nome)
                    # Atualiza o CEP
                    produto_page.wait_for_selector('#glow-ingress-line2', state="visible", timeout=10000)
                    cep_el = produto_page.query_selector('#glow-ingress-line2')
                    cep_atual = cep_el.inner_text().strip() if cep_el else None
                    cep_atual = re.sub(r'\D', '', cep_atual) if cep_atual else None
                    cep_desejado = re.sub(r'\D', '', cepEntrega)

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
                    produto_page.close() 
                    print("Certo", nome)
                    
                    produtos.append({
                        "codigoProduto": codigoProduto if codigoProduto else print(f"O codigoProduto de {nome} não foi encontrado no pincipal.\n"),
                        "nome": nome if nome else print(f"O nome de {linkProduto} não foi encontrado na raspagem.\n"),
                        "preco": price if price else 0.0,
                        "imagem": imagem if imagem else print(f"A imagem de {nome} não foi encontrada na raspagem.\n"),
                        "url": linkProduto if linkProduto else print(f"O link de {nome} não foi encontrado na raspagem.\n"),
                        "frete": frete if frete else print(f"O frete de {nome} não foi encontrado na raspagem.\n"),
                        "prazo": prazo if prazo else print(f"O prazo de {nome} não foi encontrado na raspagem.\n"),
                    })
                except Exception as e:
                    print(f"[ERRO] Tentativa {tentativa+1} falhou para {linkProduto}: {e}")
                    if tentativa == tentativas - 1:
                        print("[ERRO] Todas as tentativas falharam, pulando produto.")
                        status_produtos[nome] = {"url": linkProduto, "status": "Preço não escontrado"}
                        return None

        pegarDados(browser ,linkProduto, cepEntrega)
    print(f"[INFO] Total de produtos válidos encontrados: {len(produtos)}")
    print(status_produtos)
    with open("amazon_data.json", "w", encoding="utf-8") as f:
        json.dump(produtos, f, indent=4, ensure_ascii=False)

    browser.close()
    if(produtos == 1 or produtos == None or produtos == "" or produtos == 0 ):
        print(f"Numero de Produtos passados {produtos}")
        print("A raspagem houve um erro, sera refeita!")
        raspar_dados()
    return produtos
"""

import json
from playwright.sync_api import sync_playwright
import random
import time
import re

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/117 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/116 Safari/537.36"
]

# ====================================================================
# FUNÇÃO PRINCIPAL
# ====================================================================
def raspar_dados(playwright, BASE_URL, cepEntrega):

    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(
        user_agent=random.choice(USER_AGENTS),
        viewport={"width": 1280, "height": 800},
        locale="pt-BR"
    )

    page = context.new_page()
    produtos = []
    status_produtos = {}

    print("[INFO] Acessando página inicial...")

    try:
        page.goto(BASE_URL, timeout=70000)
        page.wait_for_selector('div.s-main-slot', timeout=60000)
    except Exception as e:
        print(f"[ERRO] Falha ao abrir página inicial: {e}")
        browser.close()
        return []

    time.sleep(2)

    product_cards = page.query_selector_all('div.s-main-slot div[data-asin]:not([data-asin=""])')

    print(f"[INFO] Produtos encontrados: {len(product_cards)}")

    # ====================================================================
    # LOOP PRINCIPAL DE LISTAGEM
    # ====================================================================
    for i, card in enumerate(product_cards, start=1):

        name_el = (
            card.query_selector('div[data-cy="title-recipe"] a') or
            card.query_selector('h2.a-size-mini a.a-link-normal') or
            card.query_selector('h2.a-size-base a.a-link-normal')
        )

        if not name_el:
            print("[AVISO] Produto sem nome, ignorado.")
            continue

        nome = name_el.inner_text().strip()
        linkProduto = "https://www.amazon.com.br" + name_el.get_attribute('href')

        print(f"\n=========== PRODUTO {i} ===========")
        print("Link:", linkProduto)

        # ====================================================================
        # COLETA DOS DADOS INDIVIDUAIS
        # ====================================================================
        produto_info = pegar_dados_produto(browser, linkProduto, cepEntrega)

        if produto_info:
            produtos.append(produto_info)
            print("[OK] Produto coletado com sucesso.\n")
        else:
            print("[ERRO] Produto ignorado.\n")

    # ====================================================================
    # SALVAMENTO FINAL
    # ====================================================================
    print(f"[INFO] Total coletado: {len(produtos)}")

    with open("amazon_data.json", "w", encoding="utf-8") as f:
        json.dump(produtos, f, ensure_ascii=False, indent=4)

    browser.close()
    return produtos


# ====================================================================
# FUNÇÃO QUE RASPA CADA PRODUTO INDIVIDUAL
# ====================================================================
def pegar_dados_produto(browser, linkProduto, cepEntrega, tentativas=3):

    for tentativa in range(1, tentativas + 1):
        try:
            print(f"[INFO] Acessando produto (tentativa {tentativa})")

            context = browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={"width": 1280, "height": 800},
                locale="pt-BR"
            )

            page = context.new_page()
            page.goto(linkProduto, timeout=90000)

            # Wait for title
            page.wait_for_selector("h1#title span#productTitle", timeout=60000)

            # ============================
            # TÍTULO
            # ============================
            nome = page.query_selector("h1#title span#productTitle").inner_text().strip()

            # ============================
            # CÓDIGO ASIN
            # ============================
            match = re.search(r"/dp/([A-Z0-9]+)/", linkProduto)
            codigoProduto = match.group(1) if match else None

            # ============================
            # PREÇO
            # ============================
            price_el = page.query_selector("span.a-price span.a-offscreen")
            price = price_el.inner_text().strip() if price_el else None

            # ============================
            # IMAGEM DO PRODUTO
            # ============================
            img_el = page.query_selector("#landingImage")
            imagem = img_el.get_attribute("src") if img_el else None

            # ============================
            # ESPECIFICAÇÕES
            # ============================
            rows = page.query_selector_all("table.a-normal tbody tr")

            for row in rows:
                try:
                    label = row.query_selector("td.a-span3 span.a-text-bold")
                    value = row.query_selector("td.a-span9 span.po-break-word")

                    if label and value:
                        nome += f"|{label.inner_text().strip()}:{value.inner_text().strip()}"
                except:
                    pass

            # ============================
            # ATUALIZAÇÃO DO CEP
            # ============================
            frete = None
            prazo = None

            try:
                time.sleep(1)
                page.click('#nav-global-location-popover-link', timeout=8000)

                page.wait_for_selector('#GLUXZipUpdateInput_0', timeout=12000)

                cep = re.sub(r"\D", "", cepEntrega)
                page.fill('#GLUXZipUpdateInput_0', cep[:5])
                page.fill('#GLUXZipUpdateInput_1', cep[5:])

                page.click('#GLUXZipUpdate')
                page.wait_for_load_state("networkidle")

                span_el = page.query_selector("span[data-csa-c-delivery-price]")

                if span_el:
                    frete = span_el.get_attribute("data-csa-c-delivery-price")
                    prazo = span_el.get_attribute("data-csa-c-delivery-time")

            except Exception as e:
                print("[AVISO] Não foi possível atualizar o CEP:", e)

            page.close()

            # ============================
            # MONTA OBJETO FINAL
            # ============================
            return {
                "codigoProduto": codigoProduto,
                "nome": nome,
                "preco": price,
                "imagem": imagem,
                "url": linkProduto,
                "frete": frete,
                "prazo": prazo
            }

        except Exception as e:
            print(f"[ERRO] Tentativa {tentativa} falhou: {e}")
            time.sleep(2)

    print("[ERRO] Todas as tentativas falharam:", linkProduto)
    return None

