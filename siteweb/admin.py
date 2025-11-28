from django.contrib import admin
from .models import Usuario, Loja, Produto

admin.site.register(Usuario)
admin.site.register(Loja)
admin.site.register(Produto)