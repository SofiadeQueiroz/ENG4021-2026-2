"""
URL configuration for projeto project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static 
from projetoapp.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('cadastro/', cadastro, name='cadastro'),
    path('busca/', busca, name='busca'),
    path('favoritos/', favoritos, name='favoritos'),
    path('adicionarProduto/', adicionarProduto, name='adicionarProduto'),
    path('inicioCliente/', inicioCliente, name='inicioCliente'),
    path('novaCategoria/', novaCategoria, name='novaCategoria'),
    path('qrcode/', qrcode, name='qrcode'),
    path('cardapioDono/', tela1, name='cardapioDono'),
    path('editarProduto/', tela2),
    path('aparencia/', aparencia, name='aparencia'),
    path('meuRestaurante/', meuRestaurante, name='meuRestaurante'),
    path('cardapioPublico/', cardapioPublico, name='cardapioPublico'),
    path('detalhesProduto/', detalhesProduto, name='detalhesProduto'),
    path('esqueciSenha/', esqueciSenha, name='esqueciSenha'),
    path('entrar/', entrar, name='entrar'),
    path('sair/', sair, name='sair'),
    path('accounts/', include('allauth.urls')),
] 
