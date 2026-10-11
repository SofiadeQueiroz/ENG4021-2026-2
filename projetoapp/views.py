from django.shortcuts import render

def home(request):
    return render(request,'boasVindas.html')

def cadastro(request):
    return render (request,'cadastro.html')

def busca(request):
    return render (request,'busca.html')

def favoritos(request):
    return render(request,'favoritos.html')