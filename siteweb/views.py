from django.shortcuts import render, redirect
from siteweb.core.raspagem import raspar_dados
from siteweb.core.rasparConc import raspagem_concorrentes
from siteweb.core.inteligencio import comparacaoIa
from siteweb.core.utils import ler_todas_lojas
#from utils.cache import salvar_cache, ler_cache
from siteweb.core.servicos import executar_raspagem
from siteweb.core.servicos import rankeador
import json
from django.conf import settings
from siteweb.models import Usuario
from django.http import JsonResponse

def usuario_autenticado(request):
    if 'usuario_id' in request.session:
        usuario_id = request.session['usuario_id']
        usuario = Usuario.objects.get(id=usuario_id)
        print("Usuário já autenticado:", usuario.nome)
        return True
    else:   
        return False

def login(request):
    return render(request, 'siteweb/loginPage.html')

def home(request):
    if usuario_autenticado(request):
        return render(request, 'siteweb/index.html')
    else:
        login(request)

def verificar_usuario(request):
    if request.method == 'POST':
        nome = request.POST.get('username')
        senha = request.POST.get('password')
        usuario = Usuario.objects.filter(nome=nome, senha=senha).first()
        if usuario:
            request.session['usuario_id'] = usuario.id
            print("Usuário autenticado com sucesso.")   
            return redirect('/')
        else:
            print("Falha na autenticação do usuário.")
            return render(request, 'siteweb/loginPage.html', {'erro': 'Credenciais inválidas'})

def raspar_loja(request):
    if usuario_autenticado(request):
        if request.method == 'POST':
            urlLoja = request.POST.get("urlLoja")
            cepEntrega = request.POST.get("cepEntrega")
            produto, nomeLoja, chave_cache = executar_raspagem(urlLoja, cepEntrega) #ler_cache(chave_cache)  

            return render(request, 'siteweb/detalhesLoja.html', {
                'loja': {'nome': nomeLoja, 'url':urlLoja, 'chave-cache':chave_cache},
                'produtos': produto
            })
    else:
        return login(request)
def comparador(request):
    if usuario_autenticado(request):
        if request.method == 'POST':
            try:
                dados = json.loads(request.body)
                produto = dados["produtos"]
                numPages = dados["numPages"]
                nivelCompat = dados["nivelCompat"]
                cep = dados["cep"]
                raspagem, arquivo = raspagem_concorrentes(produto,numPages, cep)
                print(f"ARQUIVO: {arquivo}")
                print("Foram encontrados:", len(raspagem[0]), "produtos concorrentes.\n")
                resultados_sim = comparacaoIa(raspagem, nivelCompat)
                """destino_nao = destinos[0]
                destino_sim = destinos[1]
                resultados_sim = destinos[2]"""
                if resultados_sim == "[]":
                    print("Nenhum concorrente compatível encontrado.")  
                    return render(request, "siteweb/comparador.html", {"erro": "Nenhum concorrente compatível foi encontrado, verifique se seus o limite da Ia foi atingido."})
                  
                resultadoRanking, texto = rankeador(resultados_sim)
                
                return render(request, "siteweb/comparador.html", 
                              {"comparacoes": raspagem, 
                               "resultados_ranking":resultadoRanking, 
                               "texto":texto, 
                               "dadosComparacao":resultados_sim}
                )
            except json.JSONDecodeError:
                    return render(request, "siteweb/comparador.html", {"erro": "Erro ao decodificar JSON"})
        else:
                return render(request, "siteweb/comparador.html", {"erro": "Método inválido"})
    else:
        return login(request)
def lojas_salvas(request):
    if usuario_autenticado(request):
        lojas= ler_todas_lojas()
        return render(request, "siteweb/index.html", {"lojas":lojas})
    else:
        return login(request)