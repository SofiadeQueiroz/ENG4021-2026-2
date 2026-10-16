from django.shortcuts import render
import requests

def home(request):
    results = request.get('https://omdbapi.com/?apikey=38b4b85b&s=Batman&type=movie')
    print(results)
    return render(request,'boasVindas.html')

def cadastro(request):
    return render (request,'cadastro.html')

def busca(request):
    return render (request,'busca.html')

def favoritos(request):
    return render(request,'favoritos.html')