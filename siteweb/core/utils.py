from django.http import JsonResponse
from utils.cache import salvar_cache, ler_cache, apagar_cache
from decimal import Decimal, InvalidOperation
from siteweb.models import Loja, Produto
import json
import redis
from tkinter import ttk

r=redis.Redis(host='localhost', port=6379, db=0)

from decimal import Decimal, InvalidOperation

def limpar_preco(valor_str):
    if not valor_str:
        return Decimal("0.00")
    # Remove símbolo de moeda, espaços invisíveis e separador de milhar
    valor_str = valor_str.replace("R$", "").replace("\xa0", "").replace(".", "").strip()
    # Substitui vírgula por ponto
    valor_str = valor_str.replace(",", ".")
    try:
        return Decimal(valor_str)
    except InvalidOperation:
        raise ValueError(f"Preço inválido: {valor_str}")

def salvar_loja(request):
    if request.method == 'POST':
        try:
            dados = json.loads(request.body)
            nome = dados.get('nome')
            url = dados.get('url')
            produtosLoja = dados.get('produtosLoja')
            lojas = Loja.objects.filter(url=url)
            loja = lojas.first()
            quantProduto = Produto.objects.filter(loja_id=loja.id).count() if loja else 0
            if loja is None:
                nova_loja = Loja(nome=nome, url=url)
                nova_loja.save() 
                print(f"Loja recebida: {nome} - {url}")
                produtos = Produto.objects.filter(loja_id = nova_loja.id).all()
                if not produtos.exists():
                    for produto in produtosLoja:
                        nome_prod = produto.get('nome')
                        print(nome_prod)
                        precoBruto = produto.get('preco')
                        preco_prod = limpar_preco(precoBruto)
                        imagem_prod = produto.get('imagem') 
                        url_prod = produto.get('url')
                        if not Produto.objects.filter(nome=nome_prod, loja_id=nova_loja.id).exists():
                            Produto.objects.create(
                                nome=nome_prod,
                                preco=preco_prod,   
                                imagem=imagem_prod,
                                loja_id=nova_loja.id,
                                url=url_prod
                            )
                            print(f"{nome_prod} - {preco_prod} - {imagem_prod}\n")
                    print(f"\nProdutos Recebidos:\n")
                    return JsonResponse({'mensagem': 'Loja salva no DB com sucesso!'})
                else:
                    return JsonResponse({'mensagem': 'Essa loja ja tem produtos!'})          
            else:
                print("Loja ja existente.")
                return JsonResponse({'mensagem': 'Loja já existente.'})
        except Exception as e:
            return JsonResponse({'mensagem': f'Erro ao salvar loja: {str(e)}'}, status=400)
    else:
        return JsonResponse({'mensagem': 'Método não permitido'}, status=405)
    


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
    