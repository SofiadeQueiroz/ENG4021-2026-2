from django.contrib import admin

from .models import Produto, Categoria, Restaurante

admin.site.register(Produto)
admin.site.register(Categoria)
admin.site.register(Restaurante)