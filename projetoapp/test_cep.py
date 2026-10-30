from unittest.mock import Mock, patch

import requests
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Restaurante


class ConsultaCEPTests(TestCase):
    dados = {'nome': 'Meu restaurante', 'descricao': 'Comida caseira', 'cozinha': 'Brasileira', 'horario': '12h às 20h', 'endereco': 'Rua digitada, 10'}
    endereco = {'cep': '01001-000', 'logradouro': 'Praça da Sé', 'bairro': 'Sé', 'localidade': 'São Paulo', 'uf': 'SP'}

    def setUp(self):
        self.client.force_login(User.objects.create_user('teste@example.com'))
        consulta = patch('projetoapp.views.requests.get')
        self.api = consulta.start()
        self.addCleanup(consulta.stop)
        self.api.return_value = Mock(json=Mock(return_value=self.endereco))

    def consultar(self, **dados):
        return self.client.post(reverse('meuRestaurante'), {**self.dados, 'acao': 'consultar_cep', 'cep': '01001-000', **dados})

    def test_consulta_preenche_endereco_e_mantem_campos_digitados(self):
        resposta = self.consultar()
        form = resposta.context['form']
        self.assertEqual(form.initial['endereco'], 'Praça da Sé, Sé, São Paulo/SP')
        self.assertEqual(form.initial['nome'], 'Meu restaurante')
        self.assertEqual(form.initial['horario'], '12h às 20h')
        self.assertContains(resposta, 'Endereço encontrado.')
        self.assertFalse(Restaurante.objects.exists())
        self.api.assert_called_once_with('https://viacep.com.br/ws/01001000/json/', timeout=5, allow_redirects=False)

    def test_consultar_nao_valida_campos_ainda_nao_preenchidos(self):
        resposta = self.consultar(nome='', descricao='')
        self.assertFalse(resposta.context['form'].is_bound)
        self.assertFalse(resposta.context['form'].errors)

    def test_cep_invalido_nao_consulta_api(self):
        for cep in ['', '123', '01001A000', '../admin', '０１００１０００']:
            with self.subTest(cep=cep):
                resposta = self.consultar(cep=cep)
                self.assertIn('cep', resposta.context['cep_form'].errors)
                self.assertEqual(resposta.context['form'].initial['endereco'], 'Rua digitada, 10')
        self.api.assert_not_called()

    def test_cep_inexistente_mostra_erro(self):
        self.api.return_value.json.return_value = {'erro': True}
        self.assertContains(self.consultar(), 'CEP não encontrado.')

    def test_falhas_de_rede_e_timeout_preservam_endereco(self):
        for erro in [requests.Timeout(), requests.ConnectionError()]:
            with self.subTest(erro=type(erro).__name__):
                self.api.side_effect = erro
                resposta = self.consultar()
                self.assertContains(resposta, 'preencha o endereço manualmente')
                self.assertEqual(resposta.context['form'].initial['endereco'], 'Rua digitada, 10')

    def test_erro_http_e_tratado(self):
        self.api.return_value.raise_for_status.side_effect = requests.HTTPError()
        self.assertIn('cep', self.consultar().context['cep_form'].errors)

    def test_json_invalido_e_tratado(self):
        self.api.return_value.json.side_effect = ValueError()
        self.assertIn('cep', self.consultar().context['cep_form'].errors)

    def test_resposta_incompleta_e_tratada(self):
        for dados in [[], {}, {**self.endereco, 'uf': None}, {**self.endereco, 'localidade': ''}]:
            with self.subTest(dados=dados):
                self.api.return_value.json.return_value = dados
                self.assertIn('cep', self.consultar().context['cep_form'].errors)

    def test_endereco_longo_nao_e_cortado_nem_substitui_digitacao(self):
        self.api.return_value.json.return_value = {**self.endereco, 'logradouro': 'Rua ' + 'a' * 100}
        resposta = self.consultar()
        self.assertIn('cep', resposta.context['cep_form'].errors)
        self.assertEqual(resposta.context['form'].initial['endereco'], 'Rua digitada, 10')

    def test_cep_generico_permite_preencher_rua_manualmente(self):
        self.api.return_value.json.return_value = {**self.endereco, 'logradouro': '', 'bairro': ''}
        self.assertEqual(self.consultar().context['form'].initial['endereco'], 'São Paulo/SP')

    def test_consulta_nao_altera_registro_antes_de_salvar(self):
        restaurante = Restaurante.objects.create(**self.dados)
        self.consultar(nome='Nome alterado')
        restaurante.refresh_from_db()
        self.assertEqual(restaurante.nome, 'Meu restaurante')
        self.assertEqual(restaurante.endereco, 'Rua digitada, 10')

    def test_salvar_endereco_manual_funciona_sem_api(self):
        resposta = self.client.post(reverse('meuRestaurante'), self.dados)
        self.assertRedirects(resposta, reverse('meuRestaurante'))
        self.assertEqual(Restaurante.objects.get().endereco, 'Rua digitada, 10')
        self.api.assert_not_called()

    def test_endereco_consultado_pode_ser_completado_e_salvo(self):
        resposta = self.consultar()
        endereco = resposta.context['form'].initial['endereco'] + ', 20'
        self.client.post(reverse('meuRestaurante'), {**self.dados, 'endereco': endereco})
        self.assertEqual(Restaurante.objects.get().endereco, endereco)

    def test_pagina_inicial_nao_depende_de_api_de_filmes(self):
        self.assertEqual(self.client.get(reverse('home')).status_code, 200)
        self.api.assert_not_called()
