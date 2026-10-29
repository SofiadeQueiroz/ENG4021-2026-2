from unittest.mock import Mock, patch

import requests
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import IntegrityError
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import Categoria, Perfil, Produto, Restaurante
from .services import CEPIndisponivel, CEPNaoEncontrado, consultar_cep


PASSWORD = "Mesa!Azul-73pasta"
CADASTRO = {
    "nome": "Pessoa de Teste",
    "email": "Teste@Example.com",
    "cpf": "529.982.247-25",
    "telefone": "(21) 99999-1234",
    "senha": PASSWORD,
    "confirmar_senha": PASSWORD,
    "aceite": "on",
}
RESTAURANTE = {
    "nome": "Restaurante de teste",
    "descricao": "Comida caseira",
    "cozinha": "Brasileira",
    "horario": "12h às 22h",
    "cep": "01001-000",
    "endereco": "Praça da Sé",
    "numero": "10",
    "complemento": "Loja A",
    "bairro": "Sé",
    "cidade": "São Paulo",
    "estado": "sp",
}
VIACEP = {
    "cep": "01001-000",
    "logradouro": "Praça da Sé",
    "bairro": "Sé",
    "localidade": "São Paulo",
    "uf": "SP",
}
PRIVATE_ROUTES = [
    "favoritos",
    "cardapioDono",
    "adicionarProduto",
    "novaCategoria",
    "editarProduto",
    "aparencia",
    "meuRestaurante",
    "endereco_cep",
]
PUBLIC_ROUTES = [
    "home",
    "cadastro",
    "entrar",
    "inicioCliente",
    "busca",
    "qrcode",
    "cardapioPublico",
    "detalhesProduto",
    "esqueciSenha",
]


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class CadastroTests(TestCase):
    def test_cadastro_persiste_perfil_e_senha_com_hash(self):
        response = self.client.post(reverse("cadastro"), CADASTRO)
        self.assertRedirects(response, reverse("entrar"))
        user = User.objects.get()
        self.assertEqual(user.username, "teste@example.com")
        self.assertEqual(user.email, "teste@example.com")
        self.assertTrue(user.check_password(PASSWORD))
        self.assertNotEqual(user.password, PASSWORD)
        self.assertEqual(user.perfil.cpf, "52998224725")
        self.assertEqual(user.perfil.telefone, "21999991234")

    def test_dados_invalidos_nao_criam_conta(self):
        for field, value in [
            ("email", "invalido"),
            ("senha", "12345678"),
            ("confirmar_senha", "diferente"),
            ("aceite", ""),
            ("cpf", "11111111111"),
            ("cpf", "52998224726"),
            ("cpf", "abc52998224725"),
            ("telefone", "123"),
            ("telefone", "2199999abcd"),
            ("nome", ""),
        ]:
            with self.subTest(field=field, value=value):
                response = self.client.post(
                    reverse("cadastro"), {**CADASTRO, field: value}
                )
                self.assertEqual(response.status_code, 200)
                self.assertIn(field, response.context["form"].errors)
                self.assertFalse(User.objects.exists())

    def test_email_duplicado_ignora_maiusculas(self):
        User.objects.create_user(
            username="TESTE@EXAMPLE.COM", email="Teste@Example.com"
        )
        response = self.client.post(reverse("cadastro"), CADASTRO)
        self.assertIn("email", response.context["form"].errors)
        self.assertEqual(User.objects.count(), 1)

    def test_falha_de_persistencia_nao_deixa_cadastro_parcial(self):
        with patch(
            "projetoapp.forms.Perfil.objects.create", side_effect=IntegrityError
        ):
            response = self.client.post(reverse("cadastro"), CADASTRO)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.exists())
        self.assertFalse(Perfil.objects.exists())


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class AuthenticationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="Legado@Example.com", email="Legado@Example.com", password=PASSWORD
        )

    def login(self, **extra):
        return self.client.post(
            reverse("entrar"),
            {"email": "LEGADO@example.com", "senha": PASSWORD, **extra},
        )

    def test_login_case_insensitive_e_sessao(self):
        self.assertRedirects(self.login(), reverse("cardapioDono"))
        self.assertEqual(self.client.session["_auth_user_id"], str(self.user.pk))

    def test_senha_incorreta_e_usuario_inativo(self):
        for inactive in [False, True]:
            with self.subTest(inactive=inactive):
                self.user.is_active = not inactive
                self.user.save()
                response = self.client.post(
                    reverse("entrar"),
                    {
                        "email": self.user.email,
                        "senha": PASSWORD if inactive else "errada",
                    },
                )
                self.assertContains(response, "Email ou senha incorretos.")
                self.assertNotIn("_auth_user_id", self.client.session)

    def test_next_local_e_preservado(self):
        self.assertRedirects(
            self.login(next="/meuRestaurante/"), reverse("meuRestaurante")
        )

    def test_next_externo_nao_redireciona(self):
        for destination in [
            "https://example.org/",
            "//example.org/",
            "javascript:alert(1)",
            "///example.org/",
        ]:
            with self.subTest(destination=destination):
                self.client.logout()
                self.assertRedirects(
                    self.login(next=destination), reverse("cardapioDono")
                )

    def test_telas_privadas_exigem_sessao_inclusive_post(self):
        for route in PRIVATE_ROUTES:
            for method in ["get", "post"]:
                with self.subTest(route=route, method=method):
                    path = reverse(route)
                    self.assertRedirects(
                        getattr(self.client, method)(path), f"/entrar/?next={path}"
                    )
        self.assertFalse(Restaurante.objects.exists())
        self.assertFalse(Produto.objects.exists())

    def test_telas_publicas_continuam_acessiveis(self):
        for route in PUBLIC_ROUTES:
            with self.subTest(route=route):
                self.assertEqual(self.client.get(reverse(route)).status_code, 200)

    def test_logout_so_aceita_post_e_revoga_sessao(self):
        self.client.force_login(self.user)
        old_session = self.client.cookies["sessionid"].value
        self.assertEqual(self.client.get(reverse("sair")).status_code, 405)
        self.assertIn("_auth_user_id", self.client.session)
        self.assertRedirects(self.client.post(reverse("sair")), reverse("home"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.client.cookies["sessionid"] = old_session
        self.assertEqual(self.client.get(reverse("cardapioDono")).status_code, 302)

    def test_csrf_no_login_cadastro_logout_e_salvamento(self):
        client = Client(enforce_csrf_checks=True)
        for route in ["cadastro", "entrar"]:
            self.assertEqual(client.post(reverse(route), CADASTRO).status_code, 403)
        client.force_login(self.user)
        for route in ["sair", "meuRestaurante", "adicionarProduto", "novaCategoria"]:
            self.assertEqual(client.post(reverse(route), RESTAURANTE).status_code, 403)
        client.get(reverse("cardapioDono"))
        token = client.cookies["csrftoken"].value
        self.assertRedirects(
            client.post(reverse("sair"), {"csrfmiddlewaretoken": token}),
            reverse("home"),
        )

    def test_paginas_privadas_nao_sao_cacheadas(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("cardapioDono"))
        self.assertIn("no-store", response.headers["Cache-Control"])

    def test_autenticado_nao_recebe_formulario_de_login_ou_cadastro(self):
        self.client.force_login(self.user)
        for route in ["entrar", "cadastro"]:
            self.assertRedirects(
                self.client.get(reverse(route)), reverse("cardapioDono")
            )


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class OwnershipTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user("owner@example.com")
        self.other = User.objects.create_user("other@example.com")
        self.client.force_login(self.owner)

    def test_restaurante_salva_endereco_e_pertence_ao_usuario(self):
        self.assertRedirects(
            self.client.post(
                reverse("meuRestaurante"), {**RESTAURANTE, "dono": self.other.pk}
            ),
            reverse("meuRestaurante"),
        )
        restaurante = Restaurante.objects.get()
        self.assertEqual(restaurante.dono, self.owner)
        self.assertEqual(restaurante.cep, "01001000")
        self.assertEqual(restaurante.estado, "SP")
        self.assertEqual(restaurante.complemento, "Loja A")
        self.client.post(
            reverse("meuRestaurante"), {**RESTAURANTE, "nome": "Nome atualizado"}
        )
        self.assertEqual(Restaurante.objects.count(), 1)

    def test_conta_nao_le_nem_sobrescreve_restaurante_alheio(self):
        self.client.post(reverse("meuRestaurante"), RESTAURANTE)
        self.client.force_login(self.other)
        self.assertEqual(
            self.client.get(reverse("meuRestaurante")).context["form"].instance.pk, None
        )
        self.client.post(
            reverse("meuRestaurante"), {**RESTAURANTE, "nome": "Outro restaurante"}
        )
        self.assertEqual(
            Restaurante.objects.get(dono=self.owner).nome, RESTAURANTE["nome"]
        )
        self.assertEqual(Restaurante.objects.count(), 2)

    def test_registros_legados_sem_dono_nao_sao_apropriados(self):
        legacy = Restaurante.objects.create(nome="Legado")
        self.client.post(reverse("meuRestaurante"), RESTAURANTE)
        legacy.refresh_from_db()
        self.assertIsNone(legacy.dono)
        self.assertEqual(legacy.nome, "Legado")

    def test_produtos_e_categorias_recebem_dono_e_menu_isola_contas(self):
        self.client.post(
            reverse("novaCategoria"), {"nome": "Entradas", "dono": self.other.pk}
        )
        self.client.post(
            reverse("adicionarProduto"),
            {
                "nome": "Produto exclusivo",
                "descricao": "Teste",
                "preco": "10.00",
                "categoria": "Entradas",
                "dono": self.other.pk,
            },
        )
        self.assertEqual(Categoria.objects.get().dono, self.owner)
        self.assertEqual(Produto.objects.get().dono, self.owner)
        self.assertContains(
            self.client.get(reverse("cardapioDono")), "Produto exclusivo"
        )
        self.client.force_login(self.other)
        self.assertNotContains(
            self.client.get(reverse("cardapioDono")), "Produto exclusivo"
        )

    def test_endereco_manual_sem_cep_funciona_sem_api(self):
        with patch("projetoapp.services.requests.get") as api:
            self.client.post(reverse("meuRestaurante"), {**RESTAURANTE, "cep": ""})
            api.assert_not_called()
        self.assertEqual(Restaurante.objects.get().endereco, "Praça da Sé")

    def test_cep_ou_uf_invalidos_impedem_salvamento(self):
        for field, value in [("cep", "123"), ("cep", "01001A000"), ("estado", "XX")]:
            with self.subTest(field=field):
                response = self.client.post(
                    reverse("meuRestaurante"), {**RESTAURANTE, field: value}
                )
                self.assertIn(field, response.context["form"].errors)
                self.assertFalse(Restaurante.objects.exists())


class ViaCEPTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client.force_login(User.objects.create_user("cep@example.com"))
        self.patcher = patch("projetoapp.services.requests.get")
        self.api = self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.api.return_value = Mock(json=Mock(return_value=VIACEP))

    def test_sucesso_normalizacao_e_timeout(self):
        response = self.client.get(reverse("endereco_cep"), {"cep": "01001-000"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["cidade"], "São Paulo")
        self.api.assert_called_once_with(
            "https://viacep.com.br/ws/01001000/json/",
            timeout=(2, 3),
            allow_redirects=False,
        )

    def test_resultado_e_cacheado_sem_repetir_consulta(self):
        consultar_cep("01001-000")
        consultar_cep("01001000")
        self.api.assert_called_once()

    def test_formato_invalido_nao_chama_servico(self):
        for cep in ["", "123", "01001A00", "../admin", "０１００１０００", "01001 000"]:
            with self.subTest(cep=cep):
                self.assertEqual(
                    self.client.get(reverse("endereco_cep"), {"cep": cep}).status_code,
                    400,
                )
        self.api.assert_not_called()

    def test_cep_inexistente_retorna_404(self):
        self.api.return_value.json.return_value = {"erro": True}
        response = self.client.get(reverse("endereco_cep"), {"cep": "99999999"})
        self.assertEqual(response.status_code, 404)
        self.assertIn("não encontrado", response.json()["erro"])

    def test_timeout_ou_erro_http_retorna_503_sem_detalhes_internos(self):
        for error in [
            requests.Timeout("internal"),
            requests.ConnectionError("internal"),
            requests.HTTPError("internal"),
        ]:
            with self.subTest(error=type(error).__name__):
                self.api.side_effect = error
                response = self.client.get(reverse("endereco_cep"), {"cep": "01001000"})
                self.assertEqual(response.status_code, 503)
                self.assertNotIn("internal", response.content.decode())

    def test_http_falha_ao_validar_status(self):
        self.api.return_value.raise_for_status.side_effect = requests.HTTPError()
        self.assertEqual(
            self.client.get(reverse("endereco_cep"), {"cep": "01001000"}).status_code,
            503,
        )

    def test_json_invalido(self):
        self.api.return_value.json.side_effect = ValueError()
        with self.assertRaises(CEPIndisponivel):
            consultar_cep("01001000")

    def test_resposta_incompleta_ou_cep_divergente(self):
        for data in [
            [],
            {},
            {**VIACEP, "uf": None},
            {**VIACEP, "cep": None},
            {**VIACEP, "cep": "99999-999"},
            {**VIACEP, "logradouro": "a" * 101},
        ]:
            with self.subTest(data=data):
                self.api.return_value.json.return_value = data
                with self.assertRaises(CEPIndisponivel):
                    consultar_cep("01001000")

    def test_cep_generico_sem_rua_e_bairro_e_valido(self):
        self.api.return_value.json.return_value = {
            **VIACEP,
            "logradouro": "",
            "bairro": "",
        }
        self.assertEqual(consultar_cep("01001000")["cidade"], "São Paulo")

    def test_falha_nao_e_cacheada(self):
        self.api.return_value.json.return_value = {"erro": True}
        with self.assertRaises(CEPNaoEncontrado):
            consultar_cep("01001000")
        self.api.return_value.json.return_value = VIACEP
        self.assertEqual(consultar_cep("01001000")["estado"], "SP")
        self.assertEqual(self.api.call_count, 2)

    def test_endpoint_so_aceita_get(self):
        self.assertEqual(
            self.client.post(reverse("endereco_cep"), {"cep": "01001000"}).status_code,
            405,
        )
        self.api.assert_not_called()

    def test_home_nao_depende_de_api_externa(self):
        self.assertEqual(self.client.get(reverse("home")).status_code, 200)
        self.api.assert_not_called()
