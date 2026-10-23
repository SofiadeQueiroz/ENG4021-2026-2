from django.db import models

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
