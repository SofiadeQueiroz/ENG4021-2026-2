from unittest.mock import Mock, patch

import requests
from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .models import Perfil
from .views import cnpj_valido, nutrientes_principais


class ValidarCNPJTests(SimpleTestCase):
    def test_cnpjs_validos(self):
        for cnpj in ['00000000000191', '11222333000181']:
            with self.subTest(cnpj=cnpj):
                self.assertTrue(cnpj_valido(cnpj))

    def test_cnpjs_invalidos(self):
        # dígito errado, tudo igual, curto, com letras e vazio
        for cnpj in ['00000000000192', '11111111111111', '123', '1122233300018A', '']:
            with self.subTest(cnpj=cnpj):
                self.assertFalse(cnpj_valido(cnpj))


class NutrientesPrincipaisTests(SimpleTestCase):
    def test_traduz_nomes_e_ignora_o_que_nao_e_principal(self):
        alimento = {'foodNutrients': [
            {'nutrientName': 'Energy', 'value': 52, 'unitName': 'KCAL'},
            {'nutrientName': 'Energy', 'value': 218, 'unitName': 'KJ'},
            {'nutrientName': 'Protein', 'value': 0.3, 'unitName': 'G'},
            {'nutrientName': 'Sodium, Na', 'value': 1, 'unitName': 'MG'},
            {'nutrientName': 'Vitamin C, total ascorbic acid', 'value': 4.6, 'unitName': 'MG'},
        ]}
        self.assertEqual(nutrientes_principais(alimento), [
            {'nome': 'Calorias', 'valor': 52, 'unidade': 'kcal'},
            {'nome': 'Proteínas', 'valor': 0.3, 'unidade': 'g'},
            {'nome': 'Sódio', 'valor': 1, 'unidade': 'mg'},
        ])

    def test_alimento_sem_nutrientes(self):
        self.assertEqual(nutrientes_principais({}), [])


class TelasDeConsultaTests(TestCase):
    def setUp(self):
        usuario = User.objects.create_user('dono@example.com')
        Perfil.objects.create(usuario=usuario, tipo='estabelecimento')
        self.client.force_login(usuario)
        consulta = patch('projetoapp.views.requests.get')
        self.api = consulta.start()
        self.addCleanup(consulta.stop)

    def test_cardapio_do_dono_tem_links_para_as_consultas(self):
        resposta = self.client.get(reverse('cardapioDono'))
        for nome in ['consultarCNPJ', 'consultarNutricao', 'consultarAlergenicos']:
            with self.subTest(nome=nome):
                self.assertContains(resposta, reverse(nome))

    def test_cnpj_invalido_nao_chama_a_api(self):
        resposta = self.client.get(reverse('consultarCNPJ'), {'cnpj': '12.345.678/0001-00'})
        self.assertContains(resposta, 'CNPJ inválido')
        self.api.assert_not_called()

    def test_cnpj_valido_com_mascara_chama_a_api_so_com_numeros(self):
        self.api.return_value = Mock(status_code=200, json=Mock(return_value={'razao_social': 'EMPRESA TESTE LTDA'}))
        resposta = self.client.get(reverse('consultarCNPJ'), {'cnpj': '00.000.000/0001-91'})
        self.assertContains(resposta, 'EMPRESA TESTE LTDA')
        self.api.assert_called_once_with('https://brasilapi.com.br/api/cnpj/v1/00000000000191', timeout=10)

    def test_cnpj_vazio_so_mostra_o_formulario(self):
        resposta = self.client.get(reverse('consultarCNPJ'))
        self.assertEqual(resposta.status_code, 200)
        self.api.assert_not_called()

    def test_falha_de_rede_mostra_mensagem_em_vez_de_quebrar(self):
        self.api.side_effect = requests.ConnectionError()
        resposta = self.client.get(reverse('consultarCNPJ'), {'cnpj': '00000000000191'})
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Não foi possível conectar à API.')

    def test_nutricao_mostra_principais_em_portugues(self):
        alimento = {'description': 'APPLE', 'foodNutrients': [
            {'nutrientName': 'Protein', 'value': 0.3, 'unitName': 'G'},
        ]}
        self.api.return_value = Mock(status_code=200, json=Mock(return_value={'foods': [alimento]}))
        resposta = self.client.get(reverse('consultarNutricao'), {'alimento': 'apple'})
        self.assertContains(resposta, 'Principais nutrientes')
        self.assertContains(resposta, 'Proteínas')
