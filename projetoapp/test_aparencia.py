from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Perfil, Restaurante


class AparenciaTests(TestCase):
    def setUp(self):
        self.dono = User.objects.create_user('dono@example.com', password='Mesa!Azul-73pasta')
        Perfil.objects.create(usuario=self.dono, tipo='estabelecimento')
        self.restaurante = Restaurante.objects.create(
            usuario=self.dono, nome='Casa Teste', descricao='Teste', cozinha='Brasileira', horario='12h-22h'
        )
        self.client.force_login(self.dono)

    def test_cor_padrao_e_terracota(self):
        self.assertEqual(self.restaurante.cor_destaque, '#b84e29')

    def test_salvar_cor_escolhida(self):
        resposta = self.client.post(reverse('aparencia'), {'cor_destaque': '#4f7a4e'})
        self.assertRedirects(resposta, reverse('aparencia'), fetch_redirect_response=False)
        self.restaurante.refresh_from_db()
        self.assertEqual(self.restaurante.cor_destaque, '#4f7a4e')

        # Ao voltar para a tela, a cor salva aparece marcada
        tela = self.client.get(reverse('aparencia'))
        self.assertContains(tela, 'value="#4f7a4e" checked')
        self.assertContains(tela, 'Aparência salva!')

    def test_cor_fora_da_lista_nao_e_salva(self):
        self.client.post(reverse('aparencia'), {'cor_destaque': '#ff0000'})
        self.restaurante.refresh_from_db()
        self.assertEqual(self.restaurante.cor_destaque, '#b84e29')

    def test_cardapio_publico_usa_a_cor_salva(self):
        from unittest.mock import patch
        import requests
        self.client.post(reverse('aparencia'), {'cor_destaque': '#2b2b2b'})
        # O cardápio público consulta APIs externas (feriados); no teste elas ficam desligadas
        with patch('projetoapp.views.requests.get', side_effect=requests.RequestException):
            resposta = self.client.get(reverse('cardapioPublico', args=[self.restaurante.pk]))
        self.assertContains(resposta, '--cor-destaque: #2b2b2b;')
