from django.shortcuts import render, redirect
import requests
from .models import Produto, Restaurante
from .forms import ProdutoForm, CadastroForm, LoginForm, CategoriaForm, RestauranteForm, EsqueciSenhaForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.core.mail import send_mail



def home(request):
    response = requests.get('https://omdbapi.com/?apikey=38b4b85b&s=Batman&type=movie')
    results_json = response.json()
    movies = results_json['Search']
    context = {
        "movies": movies
    }
    return render(request,'boasVindas.html', context)

@never_cache
def cadastro(request):
    if request.user.is_authenticated:
        return redirect('cardapioDono')
    if request.method == "POST":
        form = CadastroForm(request.POST)
        if form.is_valid():
            dados = form.cleaned_data
            try:
                with transaction.atomic():
                    User.objects.create_user(
                        username=dados['email'],
                        email=dados['email'],
                        password=dados['senha'],
                        first_name=dados['nome'],
                    )
            except IntegrityError:
                form.add_error('email', 'Esse e-mail já está cadastrado.')
            else:
                messages.success(request, 'Conta criada. Entre com seu e-mail e senha.')
                return redirect('entrar')
    else:
        form = CadastroForm()
    return render(request, 'cadastro.html', {'form': form})

def busca(request):
    return render (request,'busca.html')

@never_cache
@login_required(login_url='entrar')
def favoritos(request):
    return render(request,'favoritos.html')

@never_cache
@login_required(login_url='entrar')
def adicionarProduto(request):
    if request.method == "POST":
        form = ProdutoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('cardapioDono')
    else:
        form = ProdutoForm()
    return render(request, 'adicionarProduto.html', {'form': form})

def inicioCliente(request):
    return render(request, 'inicioCliente.html')

@never_cache
@login_required(login_url='entrar')
def novaCategoria(request):
    if request.method == "POST":
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('adicionarProduto')
    else:
        form = CategoriaForm()
    return render(request, 'novaCategoria.html', {'form': form})

def qrcode(request):
    return render(request, 'qrcode.html')

@never_cache
@login_required(login_url='entrar')
def tela1(request):
    produtos = Produto.objects.all()
    context = {
        'produtos': produtos
    }
    return render(request, 'tela1.html', context)

@never_cache
@login_required(login_url='entrar')
def tela2(request):
    return render(request, 'tela2.html')

@never_cache
@login_required(login_url='entrar')
def aparencia(request):
    return render(request, 'aparencia.html')

@never_cache
@login_required(login_url='entrar')
def meuRestaurante(request):
    restaurante = Restaurante.objects.first()
    if request.method == "POST":
        form = RestauranteForm(request.POST, instance=restaurante)
        if form.is_valid():
            form.save()
            return redirect('meuRestaurante')
    else:
        form = RestauranteForm(instance=restaurante)
    return render(request, 'meuRestaurante.html', {'form': form})


def cardapioPublico(request):
    return render(request, 'cardapioPublico.html')

def detalhesProduto(request):
    return render(request, 'detalhesProduto.html')

@never_cache
def entrar(request):
    if request.user.is_authenticated:
        return redirect('cardapioDono')
    destino = request.POST.get('next', request.GET.get('next', ''))
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].lower()
            cadastrado = User.objects.filter(username__iexact=email).first()
            usuario = authenticate(
                request,
                username=cadastrado.username if cadastrado else email,
                password=form.cleaned_data['senha'],
            )
            if usuario is not None:
                login(request, usuario)
                if destino and url_has_allowed_host_and_scheme(
                    destino, allowed_hosts={request.get_host()}, require_https=request.is_secure()
                ):
                    return redirect(destino)
                return redirect('cardapioDono')
            else:
                form.add_error(None, 'Email ou senha incorretos.')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form, 'next': destino})


@login_required(login_url='entrar')
@require_POST
def sair(request):
    logout(request)
    messages.success(request, 'Você saiu da sua conta.')
    return redirect('entrar')

def esqueciSenha(request):
    enviado = False
    if request.method == "POST":
        form = EsqueciSenhaForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            if User.objects.filter(username=email).exists():
                send_mail(
                    subject='Recuperação de senha - FoodLink',
                    message='Recebemos um pedido para recuperar sua senha.',
                    from_email='nao-responda@foodlink.com',
                    recipient_list=[email],
                )
            enviado = True
    else:
        form = EsqueciSenhaForm()
    return render(request, 'esqueciSenha.html', {'form': form, 'enviado': enviado})

