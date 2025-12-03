#raspagem.py
import json
from playwright.sync_api import sync_playwright, TimeoutError
import random
import time
import re

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/117 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/116 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; rv:116.0) Gecko/20100101 Firefox/116.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15"
]

# ====================================================================
# REMOVE POPUPS DA AMAZON
# ====================================================================
def fechar_popups(page):
    try:
        popups = page.query_selector_all(
            ".a-popover, .a-modal-scroller, .a-modal-overlay, [role='dialog'], .a-sheet"
        )
        for p in popups:
            try:
                p.evaluate("el => el.remove()")
            except:
                pass
        page.keyboard.press("Escape")
        time.sleep(0.3)
    except:
        pass


# ====================================================================
# FUNÇÃO PRINCIPAL
# ====================================================================
def raspar_dados(playwright, BASE_URL, cepEntrega):

    print("\n============================")
    print("🚀 INICIANDO RASPAGEM AMAZON")
    print("============================\n")

    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(
        user_agent=random.choice(USER_AGENTS),
        viewport={"width": 1280, "height": 800},
        locale="pt-BR"
    )
    page = context.new_page()
    produtos = []
    pagina_atual = 1

    # ---------- Abrir página inicial ----------
    try:
        print("[INFO] Acessando página inicial...")
        page.goto(BASE_URL, timeout=70000)
        page.wait_for_selector('div.s-main-slot', timeout=60000)
        print("[OK] Página carregada!")
    except TimeoutError:
        print("[ERRO] Timeout ao abrir página inicial.")
        browser.close()
        return []
    except Exception as e:
        print(f"[ERRO] Falha ao abrir página inicial: {e}")
        browser.close()
        return []

    # ---------- Atualizar CEP ----------
    try:
        print("[INFO] Atualizando CEP...")
        page.click('#nav-global-location-popover-link', timeout=8000)
        page.wait_for_selector('#GLUXZipUpdateInput_0', timeout=12000)

        cep = re.sub(r"\D", "", cepEntrega)
        page.fill('#GLUXZipUpdateInput_0', cep[:5])
        page.fill('#GLUXZipUpdateInput_1', cep[5:])
        page.click('#GLUXZipUpdate')
        page.wait_for_load_state("networkidle")
        time.sleep(random.uniform(1, 2))
        print("[OK] CEP atualizado!")
    except Exception as e:
        print(f"[AVISO] Não foi possível atualizar o CEP: {e}")

    # ---------- Loop de páginas ----------
    while True:
        print(f"\n==============================")
        print(f"📄 COLETANDO PÁGINA {pagina_atual}")
        print("==============================\n")

        fechar_popups(page)

        # Scroll lento para simular usuário
        try:
            page.evaluate("window.scrollBy(0, document.body.scrollHeight/3);")
            time.sleep(random.uniform(0.5, 1.5))
            page.evaluate("window.scrollBy(0, document.body.scrollHeight);")
            time.sleep(random.uniform(0.5, 1.5))
        except Exception:
            pass

        # ---------- Coleta links de produtos ----------
        try:
            cards = page.query_selector_all('div.s-main-slot div[data-asin]:not([data-asin=""])')
        except Exception as e:
            print(f"[ERRO] Não foi possível coletar cards de produtos: {e}")
            break

        links_produtos = []
        for card in cards:
            name_el = (
                card.query_selector('div[data-cy="title-recipe"] a') or
                card.query_selector('h2.a-size-mini a.a-link-normal') or
                card.query_selector('h2.a-size-base a.a-link-normal')
            )
            if not name_el:
                continue
            href = name_el.get_attribute("href")
            if href and "dp/" in href:
                links_produtos.append("https://www.amazon.com.br" + href)

        print(f"[OK] Links encontrados nesta página: {len(links_produtos)}")

        # ---------- Processa cada produto ----------
        for i, linkProduto in enumerate(links_produtos, start=1):
            print(f"\n📦 Produto {i} da página {pagina_atual}")
            print(f"URL: {linkProduto}")
            produto_info = pegar_dados_produto(context, linkProduto)
            if produto_info:
                produtos.append(produto_info)
                print("[✔] Produto coletado!")
            else:
                print("[X] Produto ignorado.")

            time.sleep(random.uniform(0.5, 1.5))

        # ---------- Próxima página ----------
        try:
            botao_proximo = page.query_selector("a.s-pagination-next:not(.s-pagination-disabled)")
            if botao_proximo:
                href = botao_proximo.get_attribute("href")
                if href:
                    print(f"[➡] Indo para próxima página via href: {href}")
                    page.goto("https://www.amazon.com.br" + href)
                else:
                    print("[INFO] Clicando no botão de próxima página...")
                    botao_proximo.scroll_into_view_if_needed()
                    time.sleep(random.uniform(0.5, 1))
                    botao_proximo.click()
                page.wait_for_load_state("load")
                time.sleep(random.uniform(1, 2))
                pagina_atual += 1
            else:
                print("[✔] Não há mais páginas. Finalizando raspagem.\n")
                break
        except Exception as e:
            print(f"[AVISO] Não foi possível avançar para próxima página: {e}")
            break

    # ---------- Salvamento final ----------
    print(f"\n🎉 COLETA FINALIZADA! Total coletado: {len(produtos)} produtos.")
    with open("amazon_data.json", "w", encoding="utf-8") as f:
        json.dump(produtos, f, ensure_ascii=False, indent=4)

    browser.close()
    return produtos


# ====================================================================
# FUNÇÃO: RASPA UM PRODUTO INDIVIDUAL
# ====================================================================
def pegar_dados_produto(context, linkProduto, tentativas=3):
    for tentativa in range(1, tentativas + 1):
        print(f"[INFO] Acessando produto (tentativa {tentativa})")
        try:
            page = context.new_page()
            page.goto(linkProduto, timeout=90000)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(random.uniform(1, 2))

            fechar_popups(page)

            # Título
            try:
                nome = page.query_selector("h1#title span#productTitle").inner_text().strip()
            except:
                nome = "Produto sem título"

            # Código ASIN
            match = re.search(r"/dp/([A-Z0-9]+)/", linkProduto)
            codigoProduto = match.group(1) if match else None

            # Preço
            try:
                price_el = page.query_selector("span.a-price span.a-offscreen")
                price = price_el.inner_text().strip() if price_el else None
            except:
                price = None

            # Imagem
            try:
                img_el = page.query_selector("#landingImage")
                imagem = img_el.get_attribute("src") if img_el else None
            except:
                imagem = None

            # Especificações
            try:
                rows = page.query_selector_all("table.a-normal tbody tr")
                for row in rows:
                    label = row.query_selector("td.a-span3 span.a-text-bold")
                    value = row.query_selector("td.a-span9 span.po-break-word")
                    if label and value:
                        nome += f"|{label.inner_text().strip()}:{value.inner_text().strip()}"
            except:
                pass

            # Frete e prazo (usando bloco fornecido)
            try:
                delivery_block = page.query_selector(
                    "#mir-layout-DELIVERY_BLOCK-slot-PRIMARY_DELIVERY_MESSAGE_LARGE span[data-csa-c-type='element']"
                )
                if delivery_block:
                    frete = delivery_block.get_attribute("data-csa-c-delivery-price")
                    prazo = delivery_block.get_attribute("data-csa-c-delivery-time")
                else:
                    frete, prazo = None, None
            except:
                frete, prazo = None, None
            print(f"\n Nome:{nome}\n Codigo:{codigoProduto}\nPreço:{price}\nFrete:{frete}\nPrazo:{prazo}\n\n -------------------------------\n")
            page.close()
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
            time.sleep(random.uniform(1, 2))
            continue

    print(f"[ERRO] Todas as tentativas falharam para: {linkProduto}")
    return None



"""import json
import time
import random

# Mantemos o mesmo nome para compatibilidade
def fechar_popups(page):
    # Não faz nada na versão mock
    return


def raspar_dados(playwright, BASE_URL, cepEntrega):
    print("\n============================")
    print("🚀 MODO TESTE / MOCK")
    print("============================\n")

    print("[INFO] Acessando página inicial (fake)...")
    time.sleep(0.2)

    produtos = []
    pagina_atual = 1

    # Simulando 3 páginas com 5 produtos cada
    for pagina in range(1, 4):
        print(f"\n==============================")
        print(f"📄 COLETANDO PÁGINA {pagina} (FAKE)")
        print("==============================\n")

        # Simula links de produtos
        links = [
            f"https://www.amazon.com.br/dp/FAKEASIN{pagina}{i}"
            for i in range(1, 6)
        ]
        print(f"[OK] Links encontrados nesta página: {len(links)}")

        for link in links:
            print(f"\n📦 Produto FAKE - {link}")
            produto = pegar_dados_produto(None, link)
            produtos.append(produto)
            print("[✔] Produto simulado coletado!")
            time.sleep(0.1)

    # Salvamento fake
    print(f"\n🎉 COLETA MOCKADA FINALIZADA! Total coletado: {len(produtos)} produtos.")
    with open("amazon_data_mock.json", "w", encoding="utf-8") as f:
        json.dump(produtos, f, ensure_ascii=False, indent=4)

    return produtos


def pegar_dados_produto(context, linkProduto, tentativas=3):
    print(f"[INFO] Acessando produto (mock)...")

    # Gerando valores fictícios mas realistas
    codigo = linkProduto.split("/")[-1].replace("dp/", "")
    preco = f"R$ {random.randint(50, 500)}"
    nome = f"Produto Fictício {codigo}"
    imagem = "https://fakeimg.pl/300x300/?text=Produto+Fake"
    frete = random.choice(["Grátis", "R$ 12,90", "R$ 19,90"])
    prazo = random.choice(["2 dias úteis", "Até 7 dias", "Entrega amanhã"])

    print(f"""'''
 Nome: {nome}
 Código: {codigo}
 Preço: {preco}
 Frete: {frete}
 Prazo: {prazo}
 -------------------------------
   ''' """)

    return {
        "codigoProduto": codigo,
        "nome": nome,
        "preco": preco,
        "imagem": imagem,
        "url": linkProduto,
        "frete": frete,
        "prazo": prazo
    }"""