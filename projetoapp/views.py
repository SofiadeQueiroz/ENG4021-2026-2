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
from .forms import ConsultaCEPForm



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
    cep_form = ConsultaCEPForm()
    resultado_cep = ''
    if request.method == "POST":
        if request.POST.get('acao') == 'consultar_cep':
            cep_form = ConsultaCEPForm(request.POST)
            dados_formulario = {campo: request.POST.get(campo, '') for campo in RestauranteForm.Meta.fields}
            if cep_form.is_valid():
                cep = cep_form.cleaned_data['cep'].replace('-', '')
                try:
                    resposta = requests.get(f'https://viacep.com.br/ws/{cep}/json/', timeout=5, allow_redirects=False)
                    resposta.raise_for_status()
                    endereco = resposta.json()
                    if not isinstance(endereco, dict):
                        raise ValueError('Resposta inválida')
                    if endereco.get('erro') in (True, 'true'):
                        cep_form.add_error('cep', 'CEP não encontrado. Confira os números.')
                    elif any(not isinstance(endereco.get(campo), str) for campo in ('logradouro', 'bairro', 'localidade', 'uf')):
                        raise ValueError('Resposta incompleta')
                    elif not endereco['localidade'] or len(endereco['uf']) != 2:
                        raise ValueError('Cidade ou UF inválida')
                    else:
                        partes = [endereco['logradouro'], endereco['bairro'], f"{endereco['localidade']}/{endereco['uf']}"]
                        endereco_completo = ', '.join(parte for parte in partes if parte)
                        if len(endereco_completo) > Restaurante._meta.get_field('endereco').max_length:
                            cep_form.add_error('cep', 'O endereço retornado é longo demais. Preencha o endereço manualmente, com até 100 caracteres.')
                        else:
                            dados_formulario['endereco'] = endereco_completo
                            resultado_cep = 'Endereço encontrado. Confira os dados e acrescente o número e o complemento antes de salvar.'
                except (requests.RequestException, ValueError):
                    cep_form.add_error('cep', 'Não foi possível consultar o CEP. Tente novamente ou preencha o endereço manualmente.')
            # Consultar o CEP mantém os campos digitados e não salva o restaurante.
            form = RestauranteForm(initial=dados_formulario, instance=restaurante)
        else:
            form = RestauranteForm(request.POST, instance=restaurante)
            if form.is_valid():
                form.save()
                return redirect('meuRestaurante')
    else:
        form = RestauranteForm(instance=restaurante)
    return render(request, 'meuRestaurante.html', {'form': form, 'cep_form': cep_form, 'resultado_cep': resultado_cep})


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

def consultarCNPJ(request):
    cnpj = request.GET.get('cnpj', '').replace('.', '').replace('/', '').replace('-', '')

    dados = None
    erro = None

    if cnpj:
        try:
            response = requests.get(
                f'https://brasilapi.com.br/api/cnpj/v1/{cnpj}',
                timeout=10
            )

            if response.status_code == 200:
                dados = response.json()

            elif response.status_code == 429:
                erro = 'Muitas consultas realizadas. Aguarde um pouco e tente novamente.'

            elif response.status_code == 404:
                erro = 'CNPJ não encontrado.'

            elif response.status_code == 400:
                erro = 'CNPJ inválido.'

            else:
                erro = f'Erro ao consultar CNPJ. Código: {response.status_code}'

        except requests.exceptions.RequestException:
            erro = 'Não foi possível conectar à API.'        

    return render(request, 'consultaCNPJ.html', {
        'dados': dados,
        'erro': erro
    })



def consultarNutricao(request):
    alimento = request.GET.get('alimento', '').strip()

    alimentos = []
    erro = None

    if alimento:
        try:
            response = requests.get(
                'https://api.nal.usda.gov/fdc/v1/foods/search',
                params={
                    'query': alimento,
                    'api_key': 'DEMO_KEY',
                    'pageSize': 5
                },
                timeout=10
            )

            if response.status_code == 200:
                resultado = response.json()
                alimentos = resultado.get('foods', [])

            elif response.status_code == 429:
                erro = 'Limite de consultas atingido. Tente novamente mais tarde.'

            else:
                erro = f'Erro na consulta: {response.status_code}'

        except requests.exceptions.RequestException:
            erro = 'Não foi possível conectar à API.'

    return render(request, 'consultaNutricao.html', {
        'alimentos': alimentos,
        'erro': erro,
        'busca': alimento
    })

def consultarAlergenicos(request):
    busca = request.GET.get('produto', '').strip()
    produtos = []
    erro = None

    if busca:
        try:
            response = requests.get(
    'https://world.openfoodfacts.org/cgi/search.pl',
    params={
        'search_terms': busca,
        'json': 1,
        'page_size': 5,
        'fields': 'product_name,brands,allergens,ingredients_text'
    },
    headers={
        'User-Agent': 'FoodLink/1.0 - PUC-Rio student project'
    },
    timeout=10
)

            if response.status_code == 200:
                resultado = response.json()
                produtos = resultado.get('products', [])
            else:
                erro = f'Erro na consulta: {response.status_code}'

        except requests.exceptions.RequestException:
            erro = 'Não foi possível conectar à API.'

    return render(request, 'consultaAlergenicos.html', {
        'produtos': produtos,
        'erro': erro,
        'busca': busca
    })