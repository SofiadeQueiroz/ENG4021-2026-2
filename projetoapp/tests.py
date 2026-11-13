from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse


class AutenticacaoTests(TestCase):
    senha = 'Mesa!Azul-73pasta'
    cadastro = {
        'nome': 'Pessoa de Teste', 'email': 'Teste@Example.com',
        'cpf': '529.982.247-25', 'telefone': '(21) 99999-1234',
        'senha': senha, 'confirmar_senha': senha, 'aceite': 'on',
    }

    def test_cadastro_cria_usuario_com_senha_protegida(self):
        resposta = self.client.post(reverse('cadastro'), self.cadastro)
        self.assertRedirects(resposta, reverse('entrar'))
        usuario = User.objects.get()
        self.assertEqual(usuario.username, 'teste@example.com')
        self.assertEqual(usuario.email, 'teste@example.com')
        self.assertTrue(usuario.check_password(self.senha))
        self.assertNotEqual(usuario.password, self.senha)

    def test_cadastro_rejeita_senha_fraca_confirmacao_e_email_invalidos(self):
        for campo, valor in [('senha', '12345678'), ('confirmar_senha', 'outra'), ('email', 'invalido'), ('aceite', '')]:
            with self.subTest(campo=campo):
                resposta = self.client.post(reverse('cadastro'), {**self.cadastro, campo: valor})
                self.assertIn(campo, resposta.context['form'].errors)
                self.assertFalse(User.objects.exists())

    def test_cadastro_rejeita_email_repetido_com_caixa_diferente(self):
        User.objects.create_user('TESTE@EXAMPLE.COM')
        resposta = self.client.post(reverse('cadastro'), self.cadastro)
        self.assertIn('email', resposta.context['form'].errors)
        self.assertEqual(User.objects.count(), 1)

    def test_login_aceita_email_sem_distinguir_maiusculas(self):
        usuario = User.objects.create_user('Teste@Example.com', password=self.senha)
        resposta = self.client.post(reverse('entrar'), {'email': 'TESTE@example.com', 'senha': self.senha})
        self.assertRedirects(resposta, reverse('cardapioDono'))
        self.assertEqual(self.client.session['_auth_user_id'], str(usuario.pk))

    def test_login_incorreto_ou_inativo_nao_abre_sessao(self):
        usuario = User.objects.create_user('teste@example.com', password=self.senha)
        for ativo, senha in [(True, 'errada'), (False, self.senha)]:
            usuario.is_active = ativo
            usuario.save()
            resposta = self.client.post(reverse('entrar'), {'email': usuario.username, 'senha': senha})
            self.assertContains(resposta, 'Email ou senha incorretos.')
            self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_volta_a_pagina_pedida(self):
        User.objects.create_user('teste@example.com', password=self.senha)
        resposta = self.client.post(reverse('entrar'), {'email': 'teste@example.com', 'senha': self.senha, 'next': '/meuRestaurante/'})
        self.assertRedirects(resposta, reverse('meuRestaurante'))

    def test_login_nao_redireciona_para_site_externo(self):
        User.objects.create_user('teste@example.com', password=self.senha)
        for destino in ['https://example.org/', '//example.org/', 'javascript:alert(1)']:
            self.client.logout()
            resposta = self.client.post(reverse('entrar'), {'email': 'teste@example.com', 'senha': self.senha, 'next': destino})
            self.assertRedirects(resposta, reverse('cardapioDono'))

    def test_paginas_privadas_exigem_login_em_get_e_post(self):
        for caminho in ['/favoritos/', '/cardapioDono/', '/adicionarProduto/', '/novaCategoria/', '/editarProduto/', '/aparencia/', '/meuRestaurante/']:
            for metodo in ['get', 'post']:
                with self.subTest(caminho=caminho, metodo=metodo):
                    resposta = getattr(self.client, metodo)(caminho)
                    self.assertRedirects(resposta, '/entrar/?next=' + caminho)

    def test_telas_do_cliente_continuam_publicas(self):
        for nome in ['inicioCliente', 'busca', 'qrcode', 'cardapioPublico', 'detalhesProduto']:
            self.assertEqual(self.client.get(reverse(nome)).status_code, 200)

    def test_logout_exige_post_e_invalida_sessao(self):
        self.client.force_login(User.objects.create_user('teste@example.com'))
        sessao_antiga = self.client.cookies['sessionid'].value
        self.assertEqual(self.client.get(reverse('sair')).status_code, 405)
        self.assertIn('_auth_user_id', self.client.session)
        self.assertRedirects(self.client.post(reverse('sair')), reverse('entrar'))
        self.assertNotIn('_auth_user_id', self.client.session)
        self.client.cookies['sessionid'] = sessao_antiga
        self.assertRedirects(self.client.get('/cardapioDono/'), '/entrar/?next=/cardapioDono/')

    def test_formularios_exigem_csrf(self):
        cliente = Client(enforce_csrf_checks=True)
        self.assertEqual(cliente.post(reverse('cadastro'), self.cadastro).status_code, 403)
        self.assertEqual(cliente.post(reverse('entrar'), self.cadastro).status_code, 403)
        cliente.force_login(User.objects.create_user('teste@example.com'))
        self.assertEqual(cliente.post(reverse('sair')).status_code, 403)
        cliente.get(reverse('cardapioDono'))
        token = cliente.cookies['csrftoken'].value
        self.assertRedirects(cliente.post(reverse('sair'), {'csrfmiddlewaretoken': token}), reverse('entrar'))

    def test_usuario_logado_e_paginas_privadas_sem_cache(self):
        self.client.force_login(User.objects.create_user('teste@example.com'))
        for nome in ['cadastro', 'entrar']:
            self.assertRedirects(self.client.get(reverse(nome)), reverse('cardapioDono'))
        resposta = self.client.get(reverse('cardapioDono'))
        self.assertIn('no-store', resposta.headers['Cache-Control'])


class DisponibilidadeProdutoTests(TestCase):
    def setUp(self):
        from unittest.mock import patch
        from .models import Perfil, Restaurante, Produto
        self.dono = User.objects.create_user('dono@example.com', password='Mesa!Azul-73pasta')
        Perfil.objects.create(usuario=self.dono, tipo='estabelecimento')
        self.restaurante = Restaurante.objects.create(
            usuario=self.dono, nome='Casa Teste', descricao='Teste', cozinha='Brasileira', horario='12h-22h'
        )
        self.produto = Produto.objects.create(
            restaurante=self.restaurante, nome='Feijoada', descricao='Completa', preco='45.00', categoria='Pratos'
        )
        self.client.force_login(self.dono)
        # O cardápio público consulta APIs externas (feriados); nos testes elas ficam desligadas
        bloqueio = patch('projetoapp.views.requests.get', side_effect=__import__('requests').RequestException)
        bloqueio.start()
        self.addCleanup(bloqueio.stop)

    def dados(self, **extra):
        return {'nome': 'Feijoada', 'descricao': 'Completa', 'preco': '45.00', 'categoria': 'Pratos', **extra}

    def test_produto_novo_comeca_disponivel(self):
        self.assertTrue(self.produto.disponivel)

    def test_editar_salva_produto_como_indisponivel(self):
        # Checkbox desmarcado não é enviado no POST
        resposta = self.client.post(reverse('editarProduto', args=[self.produto.pk]), self.dados())
        self.assertRedirects(resposta, reverse('cardapioDono'))
        self.produto.refresh_from_db()
        self.assertFalse(self.produto.disponivel)

        self.client.post(reverse('editarProduto', args=[self.produto.pk]), self.dados(disponivel='on'))
        self.produto.refresh_from_db()
        self.assertTrue(self.produto.disponivel)

    def test_adicionar_salva_disponibilidade_escolhida(self):
        from .models import Produto
        self.client.post(reverse('adicionarProduto'), self.dados(nome='Pudim'))
        self.assertFalse(Produto.objects.get(nome='Pudim').disponivel)

    def test_indisponivel_some_do_cardapio_publico_mas_aparece_para_o_dono(self):
        self.produto.disponivel = False
        self.produto.save()

        publico = self.client.get(reverse('cardapioPublico', args=[self.restaurante.pk]))
        self.assertNotContains(publico, 'Feijoada')

        dono = self.client.get(reverse('cardapioDono'))
        self.assertContains(dono, 'Feijoada')
        self.assertContains(dono, 'Indisponível')
