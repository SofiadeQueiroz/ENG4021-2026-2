from django.shortcuts import render

def home(request):
    return render(request,'boasVindas.html')

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
    return render(request, 'tela1.html')

def tela2(request):
    return render(request, 'tela2.html')