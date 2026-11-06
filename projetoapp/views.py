from django.shortcuts import render, redirect, get_object_or_404
import requests
from datetime import date
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
from django.utils.text import slugify
from .forms import ConsultaCEPForm
from django.shortcuts import render, redirect, get_object_or_404



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
    q = request.GET.get('q', '')
    restaurantes = Restaurante.objects.all()
    if q:
        restaurantes = restaurantes.filter(nome__icontains=q)
    restaurante = restaurantes.first()

    endereco = 'Rua Marquês de São Vicente, 225, Rio de Janeiro'
    if restaurante and restaurante.endereco:
        endereco = restaurante.endereco

    resposta = requests.get('https://nominatim.openstreetmap.org/search', params={'q': endereco, 'format': 'json'}, headers={'User-Agent': 'FoodLink-PUC'})
    resultados = resposta.json()

    lat = -22.979
    lon = -43.233
    if resultados:
        lat = float(resultados[0]['lat'])
        lon = float(resultados[0]['lon'])

    return render(request, 'busca.html', {'endereco': endereco, 'restaurantes': restaurantes, 'q': q, 'lat': lat, 'lon': lon})

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
    q = request.GET.get('q', '')
    categoria = request.GET.get('categoria', '')
    categorias = ['Entradas', 'Pratos principais', 'Bebidas', 'Sobremesas']
    produtos = Produto.objects.all()
    if q:
        produtos = produtos.filter(nome__icontains=q)
    if categoria:
        produtos = produtos.filter(categoria=categoria)
    context = {
        'produtos': produtos,
        'q': q,
        'categoria': categoria,
        'categorias': categorias
    }
    return render(request, 'tela1.html', context)

@never_cache
@login_required(login_url='entrar')
def editarProduto(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    categorias = ['Entradas', 'Pratos principais', 'Bebidas', 'Sobremesas']
    if request.method == "POST":
        form = ProdutoForm(request.POST, instance=produto)
        if form.is_valid():
            form.save()
            return redirect('cardapioDono')
    else:
        form = ProdutoForm(instance=produto)
    return render(request, 'tela2.html', {'form': form, 'produto': produto, 'categorias': categorias})

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
        'detalhes': 'Ver detalhes',
        'sem_produtos': 'Nenhum produto cadastrado ainda.',
    }

    idioma = request.GET.get('idioma', 'pt')

    # Traduz um texto para inglês; se a API falhar, mantém o texto original
    traducoes = {}
    def traduzir(texto):
        if idioma != 'en' or not texto:
            return texto
        if texto not in traducoes:
            try:
                resposta = requests.get('https://api.mymemory.translated.net/get', params={'q': texto, 'langpair': 'pt|en'}, timeout=5)
                traducoes[texto] = resposta.json()['responseData']['translatedText']
            except (requests.RequestException, ValueError, KeyError, TypeError):
                traducoes[texto] = texto
        return traducoes[texto]

    # Nomes de categoria comuns já traduzidos (a API traduz "Entradas" como "Inflows")
    traducoes.update({'Entradas': 'Starters', 'Pratos principais': 'Main courses', 'Bebidas': 'Drinks', 'Sobremesas': 'Desserts'})

    textos['descricao'] = traduzir(textos['descricao'])
    if idioma == 'en':
        textos['detalhes'] = 'See details'
        textos['sem_produtos'] = 'No products yet.'

    simbolos = {'BRL': 'R$', 'USD': 'US$', 'EUR': '€', 'GBP': '£'}

    moeda = request.GET.get('moeda', 'BRL')
    if moeda not in simbolos:
        moeda = 'BRL'

    cotacao = 1
    if moeda != 'BRL':
        try:
            resposta = requests.get(f'https://economia.awesomeapi.com.br/json/last/{moeda}-BRL', timeout=5)
            cotacao = float(resposta.json()[f'{moeda}BRL']['bid'])
        except (requests.RequestException, ValueError, KeyError):
            moeda = 'BRL'

    # Produtos cadastrados pelo dono, agrupados por categoria
    categorias = {}
    for produto in Produto.objects.order_by('categoria', 'nome'):
        convertido = f'{float(produto.preco) / cotacao:.2f}'
        if moeda == 'BRL':
            convertido = convertido.replace('.', ',')

        if produto.categoria not in categorias:
            categorias[produto.categoria] = {
                'nome': traduzir(produto.categoria),
                'ancora': slugify(produto.categoria),
                'produtos': [],
            }
        categorias[produto.categoria]['produtos'].append({
            'produto': produto,
            'descricao': traduzir(produto.descricao),
            'preco': f'{simbolos[moeda]} {convertido}',
        })

    feriado = None
    hoje = date.today()
    try:
        for ano in [hoje.year, hoje.year + 1]:
            resposta = requests.get(f'https://brasilapi.com.br/api/feriados/v1/{ano}', timeout=5)
            for item in resposta.json():
                dia = date.fromisoformat(item['date'])
                if dia >= hoje:
                    feriado = {'nome': item['name'], 'data': dia.strftime('%d/%m'), 'hoje': dia == hoje}
                    break
            if feriado:
                break
    except (requests.RequestException, ValueError, KeyError, TypeError):
        feriado = None

    if idioma == 'en':
        textos['feriado_hoje'] = 'Today is a holiday'
        textos['proximo_feriado'] = 'Next holiday'
        textos['aviso_feriado'] = 'opening hours may change.'
    else:
        textos['feriado_hoje'] = 'Hoje é feriado'
        textos['proximo_feriado'] = 'Próximo feriado'
        textos['aviso_feriado'] = 'o horário de funcionamento pode mudar.'

    return render(request, 'cardapioPublico.html', {
        'feriado': feriado,
        'textos': textos,
        'idioma': idioma,
        'categorias': categorias.values(),
        'moeda': moeda,
        'moedas': simbolos,
    })

def detalhesProduto(request, id):
    # Busca o produto pelo id que veio na URL; se não existir, mostra a página de erro 404
    produto = get_object_or_404(Produto, id=id)
    preco = f'R$ {produto.preco:.2f}'.replace('.', ',')
    return render(request, 'detalhesProduto.html', {'produto': produto, 'preco': preco})

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
