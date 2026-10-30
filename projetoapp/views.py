from django.shortcuts import render, redirect
import requests
from .models import Produto, Restaurante
from .forms import ProdutoForm, CadastroForm, LoginForm, CategoriaForm, RestauranteForm, EsqueciSenhaForm, NovaSenhaForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.conf import settings



def home(request):
    response = requests.get('https://omdbapi.com/?apikey=38b4b85b&s=Batman&type=movie')
    results_json = response.json()
    movies = results_json['Search']
    context = {
        "movies": movies
    }
    return render(request,'boasVindas.html', context)

def cadastro(request):
    if request.method == "POST":
        form = CadastroForm(request.POST)
        if form.is_valid():
            dados = form.cleaned_data
            if User.objects.filter(username=dados['email']).exists():
                form.add_error('email', 'Esse email já está cadastrado.')
            else:
                User.objects.create_user(
                    username=dados['email'],
                    email=dados['email'],
                    password=dados['senha'],
                    first_name=dados['nome'],
                )
                return redirect('entrar')
    else:
        form = CadastroForm()
    return render(request, 'cadastro.html', {'form': form})

def busca(request):
    return render (request,'busca.html')

def favoritos(request):
    return render(request,'favoritos.html')

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

def tela1(request):
    produtos = Produto.objects.all()
    context = {
        'produtos': produtos
    }
    return render(request, 'tela1.html', context)

def tela2(request):
    return render(request, 'tela2.html')

def aparencia(request):
    return render(request, 'aparencia.html')

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

def entrar(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            usuario = authenticate(
                request,
                username=form.cleaned_data['email'],
                password=form.cleaned_data['senha'],
            )
            if usuario is not None:
                login(request, usuario)
                return redirect('cardapioDono')
            else:
                form.add_error(None, 'Email ou senha incorretos.')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def esqueciSenha(request):
    enviado = False
    if request.method == "POST":
        form = EsqueciSenhaForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            usuario = User.objects.filter(username=email).first()
            if usuario is not None:
                uid = urlsafe_base64_encode(force_bytes(usuario.pk))
                token = default_token_generator.make_token(usuario)
                link = request.build_absolute_uri(reverse('redefinirSenha', args=[uid, token]))
                enviar_email_resend(
                    email,
                    'Recuperação de senha - FoodLink',
                    'Recebemos um pedido para recuperar sua senha.\n\nClique no link abaixo para criar uma nova senha:\n' + link + '\n\nSe você não fez esse pedido, ignore este e-mail.',
                )
            enviado = True
    else:
        form = EsqueciSenhaForm()
    return render(request, 'esqueciSenha.html', {'form': form, 'enviado': enviado})

def redefinirSenha(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        usuario = User.objects.get(pk=uid)
    except (ValueError, TypeError, OverflowError, User.DoesNotExist):
        usuario = None

    link_valido = usuario is not None and default_token_generator.check_token(usuario, token)

    if not link_valido:
        return render(request, 'redefinirSenha.html', {'link_valido': False})

    if request.method == "POST":
        form = NovaSenhaForm(request.POST)
        if form.is_valid():
            usuario.set_password(form.cleaned_data['senha'])
            usuario.save()
            return redirect('entrar')
    else:
        form = NovaSenhaForm()
    return render(request, 'redefinirSenha.html', {'form': form, 'link_valido': True})

def enviar_email_resend(destinatario, assunto, texto):
    resposta = requests.post(
        'https://api.resend.com/emails',
        headers={
            'Authorization': 'Bearer ' + str(settings.RESEND_API_KEY),
            'Content-Type': 'application/json',
        },
        json={
            'from': 'FoodLink <onboarding@resend.dev>',
            'to': [destinatario],
            'subject': assunto,
            'text': texto,
        },
        timeout=10,
    )
    if resposta.status_code != 200:
        print('Erro Resend:', resposta.status_code, resposta.text)
    return resposta.status_code == 200