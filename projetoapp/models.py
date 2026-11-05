from django.db import models
from django.contrib.auth.models import User

class Produto(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    categoria = models.CharField(max_length=100)
    imagem = models.URLField(blank=True)

    def __str__(self):
        return self.nome# Create your models here.


class Categoria(models.Model):
    nome = models.CharField(max_length=50)

    def __str__(self):
        return self.nome


class Restaurante(models.Model):
    nome = models.CharField(max_length=60)
    descricao = models.TextField(max_length=250)
    cozinha = models.CharField(max_length=40)
    horario = models.CharField(max_length=80)
    endereco = models.CharField(max_length=100, blank=True)
    imagem = models.URLField(blank=True)

    def __str__(self):
        return self.nome


class Perfil(models.Model):
    TIPOS = [
        ('cliente', 'Cliente'),
        ('estabelecimento', 'Estabelecimento'),
    ]
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    cpf = models.CharField(max_length=11, blank=True)
    cnpj = models.CharField(max_length=14, blank=True)
    telefone = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return f'{self.usuario.username} ({self.tipo})'