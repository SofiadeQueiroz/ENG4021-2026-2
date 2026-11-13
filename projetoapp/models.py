
from django.db import models
from django.contrib.auth.models import User


class Restaurante(models.Model):
    CORES = [
        ('#b84e29', 'Terracota'),
        ('#4f7a4e', 'Verde'),
        ('#2b2b2b', 'Grafite'),
    ]
    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='restaurante'
    )
    nome = models.CharField(max_length=60)
    descricao = models.TextField(max_length=250)
    cozinha = models.CharField(max_length=40)
    horario = models.CharField(max_length=80)
    endereco = models.CharField(max_length=100, blank=True)
    imagem = models.URLField(blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    cor_destaque = models.CharField(max_length=7, choices=CORES, default='#b84e29')

    def __str__(self):
        return self.nome


class Produto(models.Model):
    restaurante = models.ForeignKey(
        Restaurante,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='produtos'
    )
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    categoria = models.CharField(max_length=100)
    imagem = models.URLField(blank=True)
    ingredientes = models.TextField(blank=True)
    alergenicos = models.TextField(blank=True)

    def __str__(self):
        return self.nome


class Categoria(models.Model):
    restaurante = models.ForeignKey(
        Restaurante,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='categorias'
    )
    nome = models.CharField(max_length=50)

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


class Favorito(models.Model):
    cliente = models.ForeignKey(User, on_delete=models.CASCADE)
    restaurante = models.ForeignKey(Restaurante, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('cliente', 'restaurante')

    def __str__(self):
        return f'{self.cliente.username} - {self.restaurante.nome}'
