from django.contrib import admin
from django.urls import path
from siteweb import views
from siteweb.core import utils
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    #path('', views.home, name='home'),
    path('login/', views.login, name='login'),
    path('', views.lojas_salvas, name='home'),
    path('verifier', views.verificar_usuario, name='verificar_usuario'),
    path("proxy-webhook/", views.proxy_webhook, name="proxy_webhook"),
    path('Loja/', views.raspar_loja, name='raspar_loja'),
    path('Loja/salvar/', utils.salvar_loja, name='salvar_loja'),
    path('Loja/recarga/', utils.recarregar_prod, name='recarregar_prod'),
    path('Loja/produto/', views.comparador, name='comparador'),
    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
