from django.contrib import admin

from .models import Produto, Categoria, Restaurante, Perfil

admin.site.register(Produto)
admin.site.register(Categoria)
admin.site.register(Restaurante)
admin.site.register(Perfil)