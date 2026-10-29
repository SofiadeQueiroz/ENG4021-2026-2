from django.shortcuts import render, redirect
from .models import Produto, Restaurante
from .forms import (
    ProdutoForm,
    CadastroForm,
    LoginForm,
    CategoriaForm,
    RestauranteForm,
    EsqueciSenhaForm,
)
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.db import IntegrityError
from django.http import JsonResponse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST
from .services import consultar_cep, CEPNaoEncontrado, CEPIndisponivel


def home(request):
    return render(request, "boasVindas.html")


@never_cache
def cadastro(request):
    if request.user.is_authenticated:
        return redirect("cardapioDono")
    if request.method == "POST":
        form = CadastroForm(request.POST)
        if form.is_valid():
            try:
                form.save()
            except IntegrityError:
                form.add_error("email", "Esse e-mail já está cadastrado.")
            else:
                messages.success(request, "Conta criada! Entre com seu e-mail e senha.")
                return redirect("entrar")
    else:
        form = CadastroForm()
    return render(request, "cadastro.html", {"form": form})


def busca(request):
    return render(request, "busca.html")


@never_cache
@login_required
def favoritos(request):
    return render(request, "favoritos.html")


@never_cache
@login_required
def adicionarProduto(request):
    if request.method == "POST":
        form = ProdutoForm(request.POST)
        if form.is_valid():
            produto = form.save(commit=False)
            produto.dono = request.user
            produto.save()
            return redirect("cardapioDono")
    else:
        form = ProdutoForm()
    return render(request, "adicionarProduto.html", {"form": form})


def inicioCliente(request):
    return render(request, "inicioCliente.html")


@never_cache
@login_required
def novaCategoria(request):
    if request.method == "POST":
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = form.save(commit=False)
            categoria.dono = request.user
            categoria.save()
            return redirect("adicionarProduto")
    else:
        form = CategoriaForm()
    return render(request, "novaCategoria.html", {"form": form})


def qrcode(request):
    return render(request, "qrcode.html")


@never_cache
@login_required
def tela1(request):
    produtos = Produto.objects.filter(dono=request.user)
    context = {"produtos": produtos}
    return render(request, "tela1.html", context)


@never_cache
@login_required
def tela2(request):
    return render(request, "tela2.html")


@never_cache
@login_required
def aparencia(request):
    return render(request, "aparencia.html")


@never_cache
@login_required
def meuRestaurante(request):
    restaurante = Restaurante.objects.filter(dono=request.user).first()
    if request.method == "POST":
        form = RestauranteForm(request.POST, instance=restaurante)
        if form.is_valid():
            restaurante = form.save(commit=False)
            restaurante.dono = request.user
            restaurante.save()
            messages.success(request, "Restaurante atualizado com sucesso.")
            return redirect("meuRestaurante")
    else:
        form = RestauranteForm(instance=restaurante)
    return render(request, "meuRestaurante.html", {"form": form})


def cardapioPublico(request):
    return render(request, "cardapioPublico.html")


def detalhesProduto(request):
    return render(request, "detalhesProduto.html")


@never_cache
def entrar(request):
    if request.user.is_authenticated:
        return redirect("cardapioDono")
    destino = request.POST.get("next", request.GET.get("next", ""))
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"].lower()
            existente = User.objects.filter(username__iexact=email).first()
            usuario = authenticate(
                request,
                username=existente.username if existente else email,
                password=form.cleaned_data["senha"],
            )
            if usuario is not None:
                login(request, usuario)
                if destino and url_has_allowed_host_and_scheme(
                    destino,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
                ):
                    return redirect(destino)
                return redirect("cardapioDono")
            else:
                form.add_error(None, "Email ou senha incorretos.")
    else:
        form = LoginForm()
    return render(request, "login.html", {"form": form, "next": destino})


@require_POST
def sair(request):
    logout(request)
    messages.success(request, "Você saiu da sua conta.")
    return redirect("home")


@login_required
@require_GET
def endereco_cep(request):
    try:
        return JsonResponse(consultar_cep(request.GET.get("cep", "")))
    except ValueError as error:
        return JsonResponse({"erro": str(error)}, status=400)
    except CEPNaoEncontrado as error:
        return JsonResponse({"erro": str(error)}, status=404)
    except CEPIndisponivel as error:
        return JsonResponse({"erro": str(error)}, status=503)


def esqueciSenha(request):
    enviado = False
    if request.method == "POST":
        form = EsqueciSenhaForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            if User.objects.filter(username=email).exists():
                send_mail(
                    subject="Recuperação de senha - FoodLink",
                    message="Recebemos um pedido para recuperar sua senha.",
                    from_email="nao-responda@foodlink.com",
                    recipient_list=[email],
                )
            enviado = True
    else:
        form = EsqueciSenhaForm()
    return render(request, "esqueciSenha.html", {"form": form, "enviado": enviado})
