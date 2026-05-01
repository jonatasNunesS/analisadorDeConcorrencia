from django.http import JsonResponse
from utils.cache import salvar_cache, ler_cache, apagar_cache
from decimal import Decimal, InvalidOperation
from siteweb.models import Loja, Produto
import json
import redis
from tkinter import ttk
import re
r=redis.Redis(host='localhost', port=6379, db=0)

from decimal import Decimal, InvalidOperation

def limpar_preco(valor):
    if valor is None:
        return "0.00"

    # Se já for Decimal, float ou int → converte para string
    if isinstance(valor, (Decimal, float, int)):
        return f"{float(valor)}"
    if isinstance(valor, str):
        valor = valor.strip()
        if not valor or valor.upper() == "GRÁTIS":
            return "0.00"

        # Caso americano: "10.99"
        if re.match(r"^\d+\.\d{2}$", valor):
            return f"{float(valor)}"

        # Caso brasileiro: "1.234,56"
        valor = re.sub(r"[^\d,\.]", "", valor)
        if "," in valor and "." in valor:
            # remove pontos de milhar e troca vírgula por ponto
            valor = valor.replace(".", "").replace(",", ".")
        elif "," in valor:
            valor = valor.replace(",", ".")
        try:
            return f"{float(valor)}"
        except:
            return "0.00"

    return "0.00"



def salvar_loja(request):
    if request.method != 'POST':
        return JsonResponse({'mensagem': 'Método não permitido'}, status=405)

    try:
        dados = json.loads(request.body)
        nome = dados.get('nome')
        url = dados.get('url')
        produtosLoja = dados.get('produtosLoja')

        if not nome or not url or not produtosLoja:
            return JsonResponse({'mensagem': 'Dados incompletos.'}, status=400)

        # Verifica se a loja já existe
        loja = Loja.objects.filter(url=url).first()
        if loja:
            print("Loja já existente.")
            return JsonResponse({'mensagem': 'Loja já existente.'})

        # Criar nova loja
        nova_loja = Loja(nome=nome, url=url)
        nova_loja.save()
        print(f"\nLoja recebida: {nome} - {url}")

        # Verifica se já existe produto vinculado (raro nesse momento)
        produtos_existentes = Produto.objects.filter(loja_id=nova_loja.id).exists()

        if produtos_existentes:
            return JsonResponse({'mensagem': 'Essa loja já tem produtos!'})

        print("\nIniciando salvamento dos produtos...")

        for produto in produtosLoja:
            codigo_prod = produto.get('codigoProduto')
            nome_prod = produto.get('nome')
            precoBruto = produto.get('preco')
            preco_prod = limpar_preco(precoBruto)
            imagem_prod = produto.get('imagem')
            url_prod = produto.get('url')
            frete_prod = produto.get('frete')
            prazo_prod = produto.get('prazo')
            if not nome_prod:
                print("Produto ignorado (nome ausente).")
                continue

            # Evita duplicados
            if Produto.objects.filter(nome=nome_prod, loja_id=nova_loja.id).exists():
                print(f"Produto já existente e ignorado: {nome_prod}")
                continue

            # Criação
            Produto.objects.create(
                codigoProduto=codigo_prod,
                nome=nome_prod,
                preco=preco_prod if preco_prod else 0.0,
                imagem=imagem_prod,
                loja_id=nova_loja.id,
                url=url_prod,
                frete=frete_prod,
                prazo=prazo_prod
            )

            print(f"[OK] {nome_prod} - {preco_prod}")

        print("\nProdutos Recebidos e salvos com sucesso.")
        return JsonResponse({'mensagem': 'Loja salva no DB com sucesso!'})

    except Exception as e:
        print("\n[ERRO AO SALVAR LOJA]:", e)
        return JsonResponse({'mensagem': f'Erro ao salvar loja: {str(e)}'}, status=400)


def ler_todas_lojas():
    lojas=[]

    for loja in Loja.objects.all():
       lojas.append({
            'keyLoja': loja.id,
            'nome': loja.nome,
            'url': loja.url
       })
    return lojas

def recarregar_prod(request):
    if request.method == 'POST':
        try:
            dados = json.loads(request.body)
            nome = dados.get('nome')
            url = dados.get('url')
            chave_cache = f"loja:{nome}" 

            apagar_cache(chave_cache)
            loja = Loja.objects.filter(url=url).first()
            if loja:
                print("Loja encontrada.")
                produtos = Produto.objects.filter(loja_id=loja.id)
                produtos.delete()
                print("Todos os produtos da loja foram apagados.")
            else:
                print("Loja não encontrada.")
            from siteweb.core.servicos import executar_raspagem
            executar_raspagem(nome, url)

            return JsonResponse({'mensagem': 'Loja e Cache apagados com sucesso, iniciando raspagem!'})
        except Exception as e:
            return JsonResponse({'mensagem': f'Erro ao apagar dados antigos: {str(e)}'}, status=400)
    else:
        return JsonResponse({'mensagem': 'Método não permitido'}, status=405)

def abrirPaginaResultados(resultados_sim):
    print(resultados_sim)
    