from unittest.mock import patch

import requests
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .models import Produto, Restaurante
from .views import alergenicos_do_produto


class AlergenicosDoProdutoTests(SimpleTestCase):
    def test_descobre_alergenicos_pelos_ingredientes(self):
        produto = Produto(ingredientes='farinha de trigo, ovos, leite', alergenicos='')
        self.assertEqual(alergenicos_do_produto(produto), ['Leite', 'Ovo', 'Glúten'])

    def test_usa_tambem_o_que_o_dono_escreveu_em_alergenicos(self):
        produto = Produto(ingredientes='', alergenicos='Glúten, Amendoim')
        self.assertEqual(alergenicos_do_produto(produto), ['Glúten', 'Amendoim'])

    def test_prato_sem_alergenicos(self):
        produto = Produto(ingredientes='alface, tomate e azeite', alergenicos='')
        self.assertEqual(alergenicos_do_produto(produto), [])


class CardapioEDetalhesTests(TestCase):
    def setUp(self):
        self.restaurante = Restaurante.objects.create(
            nome='Cantina Teste', descricao='Massas', cozinha='Italiana', horario='12h às 22h')
        self.bolo = Produto.objects.create(
            restaurante=self.restaurante, nome='Bolo de laranja', descricao='Bolo caseiro', preco='20.00',
            categoria='Sobremesas', ingredientes='farinha de trigo, ovos, leite')
        self.salada = Produto.objects.create(
            restaurante=self.restaurante, nome='Salada verde', descricao='Folhas frescas', preco='18.00',
            categoria='Entradas', ingredientes='alface, tomate e azeite')
        # O cardápio consulta a API de feriados; aqui ela "cai" para o teste não depender da internet.
        consulta = patch('projetoapp.views.requests.get', side_effect=requests.ConnectionError())
        consulta.start()
        self.addCleanup(consulta.stop)

    def cardapio(self, **parametros):
        return self.client.get(reverse('cardapioPublico', args=[self.restaurante.pk]), parametros)

    def test_sem_filtro_mostra_todos_os_pratos(self):
        resposta = self.cardapio()
        self.assertContains(resposta, 'Bolo de laranja')
        self.assertContains(resposta, 'Salada verde')

    def test_filtro_esconde_pratos_com_o_alergenico(self):
        resposta = self.cardapio(evitar='Leite')
        self.assertNotContains(resposta, 'Bolo de laranja')
        self.assertContains(resposta, 'Salada verde')
        self.assertEqual(resposta.context['escondidos'], 1)

    def test_filtro_com_dois_alergenicos(self):
        resposta = self.cardapio(evitar=['Soja', 'Glúten'])
        self.assertNotContains(resposta, 'Bolo de laranja')
        self.assertContains(resposta, 'Salada verde')

    def test_nome_que_nao_esta_na_lista_e_ignorado(self):
        resposta = self.cardapio(evitar='Banana')
        self.assertContains(resposta, 'Bolo de laranja')
        self.assertEqual(resposta.context['evitar'], [])

    def test_detalhes_mostram_ingredientes_e_alergenicos(self):
        resposta = self.client.get(reverse('detalhesProduto', args=[self.bolo.pk]))
        self.assertContains(resposta, 'farinha de trigo, ovos, leite')
        for nome in ['Leite', 'Ovo', 'Glúten']:
            with self.subTest(nome=nome):
                self.assertContains(resposta, f'<li>{nome}</li>', html=True)

    def test_detalhes_de_prato_sem_alergenicos(self):
        resposta = self.client.get(reverse('detalhesProduto', args=[self.salada.pk]))
        self.assertContains(resposta, 'Nenhum alergênico informado.')


class PaginaNaoEncontradaTests(TestCase):
    def test_endereco_inexistente_mostra_pagina_404_do_foodlink(self):
        resposta = self.client.get('/esse-endereco-nao-existe/')
        self.assertEqual(resposta.status_code, 404)
        self.assertContains(resposta, 'Página não encontrada', status_code=404)
        self.assertContains(resposta, 'Voltar ao início', status_code=404)
