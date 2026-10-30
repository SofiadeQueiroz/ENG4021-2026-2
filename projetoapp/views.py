from django.shortcuts import render
import requests
from .models import Produto

def home(request):
    response = requests.get('https://omdbapi.com/?apikey=38b4b85b&s=Batman&type=movie')
    results_json = response.json()
    movies = results_json['Search']
    context = {
        "movies": movies
    }
    return render(request,'boasVindas.html', context)

def cadastro(request):
    return render (request,'cadastro.html')

def busca(request):
    return render (request,'busca.html')

def favoritos(request):
    return render(request,'favoritos.html')

def adicionarProduto(request):
    return render(request, 'adicionarProduto.html')

def inicioCliente(request):
    return render(request, 'inicioCliente.html')

def novaCategoria(request):
    return render(request, 'novaCategoria.html')

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