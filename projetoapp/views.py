from django.shortcuts import render, redirect
import requests
from .models import Produto, Restaurante
from .forms import ProdutoForm, CadastroForm, LoginForm, CategoriaForm, RestauranteForm, EsqueciSenhaForm, NovaSenhaForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.conf import settings
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
    endereco = 'Rua Marquês de São Vicente, 225, Rio de Janeiro'
    restaurante = Restaurante.objects.first()
    if restaurante and restaurante.endereco:
        endereco = restaurante.endereco

    resposta = requests.get('https://nominatim.openstreetmap.org/search', params={'q': endereco, 'format': 'json'}, headers={'User-Agent': 'FoodLink-PUC'})
    resultados = resposta.json()

    lat = -22.979
    lon = -43.233
    if resultados:
        lat = float(resultados[0]['lat'])
        lon = float(resultados[0]['lon'])

    mapa_url = f'https://www.openstreetmap.org/export/embed.html?bbox={lon-0.01},{lat-0.01},{lon+0.01},{lat+0.01}&marker={lat},{lon}'
    return render(request, 'busca.html', {'mapa_url': mapa_url, 'endereco': endereco})

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
    textos = {
        'descricao': 'Massas artesanais e receitas de família.',
        'entradas': 'Entradas',
        'pratos': 'Pratos principais',
        'bruschetta': 'Pão tostado com tomate e manjericão.',
        'arancini': 'Bolinhos de risoto recheados com queijo.',
        'carbonara': 'Massa com guanciale, queijo e gemas.',
        'lasanha': 'Massa fresca, molho de carne e queijo gratinado.',
        'detalhes': 'Ver detalhes',
        'indisponivel': 'Indisponível no momento',
    }

    idioma = request.GET.get('idioma', 'pt')
    if idioma == 'en':
        descricoes = ['descricao', 'bruschetta', 'arancini', 'carbonara', 'lasanha']
        for chave in descricoes:
            resposta = requests.get('https://api.mymemory.translated.net/get', params={'q': textos[chave], 'langpair': 'pt|en'})
            textos[chave] = resposta.json()['responseData']['translatedText']

        textos['entradas'] = 'Starters'
        textos['pratos'] = 'Main courses'
        textos['detalhes'] = 'See details'
        textos['indisponivel'] = 'Unavailable right now'
    return render(request, 'cardapioPublico.html', {'textos': textos, 'idioma': idioma})

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

def qrcodeRestaurante(request):
    link_cardapio = request.build_absolute_uri('/cardapioPublico/')
    qr_url = 'https://api.qrserver.com/v1/create-qr-code/?size=300x300&color=B84E29&data=' + link_cardapio
    return render(request, 'qrcodeRestaurante.html', {'qr_url': qr_url, 'link_cardapio': link_cardapio})
  
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
