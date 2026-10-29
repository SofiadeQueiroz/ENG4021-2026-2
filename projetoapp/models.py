from django.conf import settings
from django.db import models


class Perfil(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    cpf = models.CharField(max_length=11)
    telefone = models.CharField(max_length=11)


class Produto(models.Model):
    dono = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    categoria = models.CharField(max_length=100)
    imagem = models.URLField(blank=True)

    def __str__(self):
        return self.nome  # Create your models here.


class Categoria(models.Model):
    dono = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )
    nome = models.CharField(max_length=50)

    def __str__(self):
        return self.nome


class Restaurante(models.Model):
    dono = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )
    nome = models.CharField(max_length=60)
    descricao = models.TextField(max_length=250)
    cozinha = models.CharField(max_length=40)
    horario = models.CharField(max_length=80)
    endereco = models.CharField(max_length=100, blank=True)
    cep = models.CharField(max_length=8, blank=True)
    numero = models.CharField(max_length=20, blank=True)
    complemento = models.CharField(max_length=80, blank=True)
    bairro = models.CharField(max_length=100, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=2, blank=True)
    imagem = models.URLField(blank=True)

    def __str__(self):
        return self.nome
