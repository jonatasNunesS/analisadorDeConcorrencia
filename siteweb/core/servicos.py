# siteweb/core/servicos.py
from playwright.sync_api import sync_playwright
from siteweb.core.raspagem import raspar_dados
from utils.cache import salvar_cache, ler_cache
from siteweb.core.utils import limpar_preco
from django.db import models
from django.conf import settings
from datetime import datetime
import json
import pandas as pd
import numpy as np
from siteweb.models import Loja, Produto

def executar_raspagem(nomeLoja, urlLoja):
    print("// -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- //")
    print("INICIO RASPAGEM")
    chave_cache = f"loja:{nomeLoja}"
    loja = Loja.objects.filter(url=urlLoja)
    if loja.exists():
        print("Loja já existe no banco de dados.")
        
"""
         with sync_playwright() as playwright:
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
            page.goto(urlLoja, timeout=50000)
            time.sleep(2)
            page.mouse.wheel(0, 1000)
            time.sleep(1)
            if "algo deu errado" in page.content():
                print("[ERRO] Página de erro detectada. Abortando raspagem.")
                browser.close()
                return []

            selected_text = page.evaluate("""
                () => {
                    const selectElement = document.querySelector('select');
                    return selectElement.options[selectElement.selectedIndex].text;
                }
            """)
            print(f"[INFO] Loja selecionada: {selected_text}")
            browser.close()
"""
    produtos_json = ler_cache(chave_cache)
    produtos = json.loads(produtos_json) if produtos_json else []
    produtos = list(produtos)
    if not produtos:
        print("Produtos não encontrados no cache")
        loja = Loja.objects.filter(url=urlLoja).first()
        if loja:
            print("Loja encontrada.")
            produtos = Produto.objects.filter(loja_id = loja.id).all()

            if not produtos.exists():
                print("[INFO] Produtos não encontrados no DB, iniciando raspagem.")
                with sync_playwright() as playwright:
                    produtos = raspar_dados(playwright, urlLoja)
                    produto_list = [
                        {
                        "nome": p["nome"] if isinstance(p, dict) else p.nome,
                            "preco": (
                        float(
                            (p["preco"] if isinstance(p, dict) else p.preco)
                            .replace("R$", "")
                            .replace("\xa0", "")
                            .replace(".", "")
                            .replace(",", ".")
                            .strip()
                        )
                        if (p["preco"] if isinstance(p, dict) else p.preco)
                        else None
                    ),

                        "imagem": p.get("imagem") if isinstance(p, dict) else (p.imagem if p.imagem else None),
                        "loja": p.get("loja") if isinstance(p, dict) else p.loja_id,
                        "url": p.get("url") if isinstance(p, dict) else None
                        }
                        for p in produtos
                    ]   
                    print("Salvando produtos no cache ", produto_list)
                    salvar_cache(chave_cache, json.dumps(produto_list))
                
            else:
                print("Produtos encontrados no DB: " , len(produtos))
                produto_list = [
                    {
                        "nome": p["nome"] if isinstance(p, dict) else p.nome,
                        "preco": float(p.preco),
                        "imagem": p.imagem if p.imagem else None,
                        "loja": p.loja_id,
                        "url": p.get("url") if isinstance(p, dict) else None
                    }
                    for p in produtos
                ]
                salvar_cache(chave_cache, json.dumps(produto_list))
        else:
            produtos = None
            print("Loja não encontrada")
            with sync_playwright() as playwright:
                produtos = raspar_dados(playwright, urlLoja)
            
    else:
        print("Produtos encontrados no cache.")
    print("// -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- //")
    return produtos

def separarLoja(nome):
    partes = nome.split("|",1)
    return partes

def rankeador(resultados_sim):
    if not resultados_sim:
        print("Lista de resultados_sim está vazia.")
        return None 
    lista = []
    resultados_sim = json.loads(resultados_sim)
    nomes = separarLoja(resultados_sim[0]["nome_principal"])
    principal = {
        "nome": nomes[1],
        "preco": resultados_sim[0]["preco_principal"],
        "tipo": "principal",
        "loja": nomes[0],
        "link": "#" 
    }
    precoAntigo = resultados_sim[0]["preco_principal"]
    lista.append(principal)
    for item in resultados_sim:
        nomes = separarLoja(item["nome_concorrente"])
        concorrente = {
            "nome": nomes[1],
            "preco": item["preco_concorrente"],
            "tipo": "concorrente",
            "loja": nomes[0],
            "link": "#"
        }
        lista.append(concorrente)

    lista.sort(key=lambda x: x["preco"])
    lst = np.array(lista)
    indicePrinci = [i for i, item in enumerate(lst) if item["tipo"] == "principal"]
    if(indicePrinci[0] >= 3):
        valorTerceiro = lista[2]["preco"]
        lista.insert(2, lista.pop(indicePrinci[0])) 
        lista[2]["preco"]= valorTerceiro - 1
        texto = f"O produto principal foi movido para a terceira posição com o preço ajustado de {precoAntigo} para {lista[2]['preco']} para melhorar sua competitividade."
    else:
        texto = "O produto principal já está entre os três primeiros, sem necessidade de ajuste de preço."
    print("Principal para rankeamento:", lista)
    lista_df = pd.DataFrame(lista)
    destino = f"{settings.MEDIA_ROOT}/classificacaoPrecoExcel/Rankeamento-{datetime.now().strftime('%d-%m-%Y_%H%M')}.xlsx"
    lista_df.to_excel(destino, index=False)
    return lista, texto

