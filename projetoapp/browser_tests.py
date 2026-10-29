"""Testes reais de layout e fluxos. Executar: python manage.py test projetoapp.browser_tests."""

import json
import os
from pathlib import Path
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.cache import cache
from django.test import override_settings
from playwright.sync_api import sync_playwright, expect

from .models import Produto, Restaurante
from .tests import PASSWORD, VIACEP


VIEWPORTS = [(320, 568), (375, 812), (768, 1024), (1440, 900), (812, 375)]
PAGES = {
    "boasVindas": "/",
    "cadastro": "/cadastro/",
    "login": "/entrar/",
    "esqueciSenha": "/esqueciSenha/",
    "inicioCliente": "/inicioCliente/",
    "busca": "/busca/",
    "qrcode": "/qrcode/",
    "cardapioPublico": "/cardapioPublico/",
    "detalhesProduto": "/detalhesProduto/",
    "favoritos": "/favoritos/",
    "tela1": "/cardapioDono/",
    "tela2": "/editarProduto/",
    "adicionarProduto": "/adicionarProduto/",
    "novaCategoria": "/novaCategoria/",
    "aparencia": "/aparencia/",
    "meuRestaurante": "/meuRestaurante/",
}
PRIVATE = {
    "favoritos",
    "tela1",
    "tela2",
    "adicionarProduto",
    "novaCategoria",
    "aparencia",
    "meuRestaurante",
}
RESULTS = Path(os.environ.get("FOODLINK_TEST_RESULTS", "test-results"))


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class BrowserTests(StaticLiveServerTestCase):
    def setUp(self):
        # ORM fixtures are prepared before Playwright starts its event loop.
        cache.clear()
        self.user = User.objects.create_user(
            "browser@example.com", password=PASSWORD, first_name="Pessoa de teste"
        )
        Produto.objects.create(
            dono=self.user,
            nome="Produto com nome bem longo para testar a quebra de linhas",
            descricao="Descrição extensa do prato, ingredientes e acompanhamentos. "
            * 4,
            preco="1234.56",
            categoria="Entradas",
            imagem="/static/img/bruschetta.jpg",
        )
        self.client.force_login(self.user)
        self.session = self.client.cookies["sessionid"].value
        RESULTS.mkdir(parents=True, exist_ok=True)

    def authenticated_context(self, browser, width, height):
        context = browser.new_context(viewport={"width": width, "height": height})
        context.add_cookies(
            [{"name": "sessionid", "value": self.session, "url": self.live_server_url}]
        )
        return context

    def assert_layout(self, page):
        errors = page.evaluate("""() => {
            const failures = [];
            const width = document.documentElement.clientWidth;
            if (document.documentElement.scrollWidth > width + 1) failures.push('Rolagem horizontal');
            for (const el of document.querySelectorAll('input:not([type="hidden"]), textarea, select, button, img, .menu-inferior a')) {
                const r = el.getBoundingClientRect();
                if (!r.width || !r.height) continue;
                if (r.left < -1 || r.right > width + 1) failures.push('Fora da tela: ' + el.outerHTML.slice(0, 100));
                if (['INPUT', 'TEXTAREA', 'SELECT', 'BUTTON'].includes(el.tagName) && !['checkbox', 'radio'].includes(el.type) && r.height < 43) failures.push('Controle pequeno: ' + el.outerHTML.slice(0, 100));
            }
            for (const img of document.images) {
                if (img.src.startsWith(location.origin) && (!img.complete || !img.naturalWidth)) failures.push('Imagem quebrada: ' + img.src);
            }
            return failures;
        }""")
        self.assertEqual(errors, [])
        self.assertEqual(
            page.locator('meta[name="viewport"]').get_attribute("content"),
            "width=device-width, initial-scale=1",
        )

    def test_responsividade_16_telas_5_resolucoes_2_navegadores(self):
        matrix = []
        engines = os.environ.get('FOODLINK_BROWSERS', 'chromium,webkit').split(',')
        selected_pages = os.environ.get('FOODLINK_LAYOUT_PAGES', ','.join(PAGES)).split(',')
        with sync_playwright() as playwright:
            for engine in engines:
                browser = getattr(playwright, engine).launch()
                try:
                    for width, height in VIEWPORTS:
                        public = browser.new_context(
                            viewport={"width": width, "height": height}
                        )
                        private = self.authenticated_context(browser, width, height)
                        try:
                            for name in selected_pages:
                                path = PAGES[name]
                                with self.subTest(
                                    browser=engine,
                                    viewport=f"{width}x{height}",
                                    page=name,
                                ):
                                    page = (
                                        private if name in PRIVATE else public
                                    ).new_page()
                                    failed_resources, js_errors = [], []
                                    page.on(
                                        "response",
                                        lambda response: (
                                            failed_resources.append(response.url)
                                            if response.status >= 400
                                            else None
                                        ),
                                    )
                                    page.on(
                                        "pageerror",
                                        lambda error: js_errors.append(str(error)),
                                    )
                                    try:
                                        response = page.goto(
                                            self.live_server_url + path,
                                            wait_until="networkidle",
                                        )
                                        self.assertEqual(response.status, 200)
                                        self.assertEqual(
                                            page.url, self.live_server_url + path
                                        )
                                        self.assert_layout(page)
                                        self.assertEqual(failed_resources, [])
                                        self.assertEqual(js_errors, [])
                                        # Keyboard navigation must bring the skip link into view.
                                        page.keyboard.press("Tab")
                                        expect(
                                            page.locator(".skip-link")
                                        ).to_be_focused()
                                        expect(
                                            page.locator(".skip-link")
                                        ).to_be_in_viewport()
                                        page.keyboard.press("Tab")
                                        screenshot = (
                                            RESULTS
                                            / f"{engine}-{width}x{height}-{name}.png"
                                        )
                                        page.screenshot(
                                            path=str(screenshot), full_page=True
                                        )
                                        matrix.append(
                                            {
                                                "browser": engine,
                                                "viewport": f"{width}x{height}",
                                                "page": name,
                                                "status": "passed",
                                            }
                                        )
                                    finally:
                                        page.close()
                        finally:
                            public.close()
                            private.close()
                finally:
                    browser.close()
        self.assertEqual(len(matrix), len(engines) * len(VIEWPORTS) * len(selected_pages))
        (RESULTS / "responsive-matrix.json").write_text(
            json.dumps(matrix, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def test_cadastro_login_logout_no_celular(self):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 320, "height": 568})
            page.goto(self.live_server_url + "/cadastro/")
            for label, value in [
                ("Nome completo", "Cliente Teste"),
                ("E-mail", "cliente@example.com"),
                ("CPF", "529.982.247-25"),
                ("Telefone", "(21) 99999-1234"),
                ("Senha", PASSWORD),
                ("Confirmar senha", PASSWORD),
            ]:
                page.get_by_label(label, exact=True).fill(value)
            page.get_by_label("Concordo com o uso").check()
            page.get_by_role("button", name="Criar conta", exact=True).click()
            expect(page).to_have_url(self.live_server_url + "/entrar/")
            expect(page.get_by_role("status")).to_contain_text("Conta criada")
            page.get_by_label("E-mail", exact=True).fill("CLIENTE@example.com")
            page.get_by_label("Senha", exact=True).fill("incorreta")
            page.get_by_role("button", name="Entrar", exact=True).click()
            expect(page.locator(".errorlist")).to_contain_text(
                "Email ou senha incorretos"
            )
            self.assert_layout(page)
            page.get_by_label("Senha", exact=True).fill(PASSWORD)
            page.get_by_role("button", name="Entrar", exact=True).click()
            expect(page).to_have_url(self.live_server_url + "/cardapioDono/")
            expect(page.locator(".session-name")).to_contain_text("Cliente Teste")
            page.get_by_role("button", name="Sair", exact=True).click()
            expect(page).to_have_url(self.live_server_url + "/")
            page.goto(self.live_server_url + "/meuRestaurante/")
            expect(page).to_have_url(
                self.live_server_url + "/entrar/?next=/meuRestaurante/"
            )
            browser.close()

    def test_viacep_preenche_e_salva_endereco_no_celular(self):
        response = Mock(json=Mock(return_value=VIACEP))
        with (
            patch("projetoapp.services.requests.get", return_value=response),
            sync_playwright() as playwright,
        ):
            browser = playwright.chromium.launch()
            context = self.authenticated_context(browser, 375, 812)
            page = context.new_page()
            page.goto(self.live_server_url + "/meuRestaurante/")
            page.get_by_label("Nome do restaurante").fill("Restaurante navegador")
            page.get_by_label("Descrição", exact=True).fill("Comida brasileira")
            page.get_by_label("Tipo de cozinha").fill("Brasileira")
            page.get_by_label("Funcionamento").fill("12h às 22h")
            page.get_by_label("CEP", exact=True).fill("01001-000")
            page.get_by_label("Número", exact=True).fill("20")
            page.get_by_label("Complemento", exact=True).fill("Loja B")
            page.get_by_role("button", name="Buscar endereço").click()
            expect(page.locator("#cep-status")).to_contain_text("Endereço encontrado")
            expect(page.locator("#id_endereco")).to_have_value("Praça da Sé")
            expect(page.locator("#id_cidade")).to_have_value("São Paulo")
            expect(page.locator("#id_numero")).to_have_value("20")
            expect(page.locator("#id_complemento")).to_have_value("Loja B")
            self.assert_layout(page)
            page.get_by_role("button", name="Salvar alterações").click()
            expect(page.get_by_role("status").first).to_contain_text(
                "Restaurante atualizado"
            )
            page.reload()
            expect(page.locator("#id_endereco")).to_have_value("Praça da Sé")
            expect(page.locator("#id_cep")).to_have_value("01001000")
            browser.close()
        self.assertEqual(Restaurante.objects.get().cidade, "São Paulo")

    def test_cep_erro_e_rede_preservam_endereco_manual(self):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            context = self.authenticated_context(browser, 320, 568)
            page = context.new_page()
            page.goto(self.live_server_url + "/meuRestaurante/")
            page.locator("#id_endereco").fill("Endereço manual")
            page.locator("#id_cep").fill("123")
            page.get_by_role("button", name="Buscar endereço").click()
            expect(page.locator("#cep-status")).to_contain_text("8 dígitos")
            for status, message in [
                (404, "CEP não encontrado."),
                (503, "Serviço indisponível. Preencha manualmente."),
            ]:
                page.route(
                    "**/api/cep/**",
                    lambda route: route.fulfill(status=status, json={"erro": message}),
                )
                page.locator("#id_cep").fill("99999-999")
                page.get_by_role("button", name="Buscar endereço").click()
                expect(page.locator("#cep-status")).to_have_text(message)
                expect(page.locator("#id_endereco")).to_have_value("Endereço manual")
                expect(
                    page.get_by_role("button", name="Buscar endereço")
                ).to_be_enabled()
                self.assert_layout(page)
                page.unroute("**/api/cep/**")
            page.route("**/api/cep/**", lambda route: route.abort())
            page.get_by_role("button", name="Buscar endereço").click()
            expect(page.locator("#cep-status")).to_contain_text("indisponível")
            expect(page.locator("#id_endereco")).to_have_value("Endereço manual")
            browser.close()

    def test_mudar_cep_durante_consulta_descarta_resposta_antiga(self):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            context = self.authenticated_context(browser, 375, 812)
            page = context.new_page()
            page.goto(self.live_server_url + "/meuRestaurante/")
            page.evaluate("""() => { window.fetch = () => new Promise(resolve => {
                window.finishCEP = () => resolve({ ok: true, json: async () => ({cep: '01001000', endereco: 'Rua antiga', bairro: 'Sé', cidade: 'São Paulo', estado: 'SP'}) });
            }); }""")
            page.locator("#id_cep").fill("01001-000")
            page.get_by_role("button", name="Buscar endereço").click()
            expect(page.get_by_role("button", name="Buscando…")).to_be_disabled()
            page.locator("#id_cep").fill("20040-020")
            page.locator("#id_endereco").fill("Rua nova")
            page.evaluate("window.finishCEP()")
            expect(page.locator("#id_endereco")).to_have_value("Rua nova")
            expect(page.get_by_role("button", name="Buscar endereço")).to_be_enabled()
            browser.close()

    def test_endereco_manual_funciona_sem_javascript(self):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            context = browser.new_context(
                java_script_enabled=False, viewport={"width": 320, "height": 568}
            )
            context.add_cookies(
                [
                    {
                        "name": "sessionid",
                        "value": self.session,
                        "url": self.live_server_url,
                    }
                ]
            )
            page = context.new_page()
            page.goto(self.live_server_url + "/meuRestaurante/")
            expect(page.locator("noscript")).to_be_visible()
            for selector, value in [
                ("#id_nome", "Sem JavaScript"),
                ("#id_descricao", "Teste"),
                ("#id_cozinha", "Brasileira"),
                ("#id_horario", "12h às 20h"),
                ("#id_endereco", "Rua manual"),
            ]:
                page.locator(selector).fill(value)
            page.get_by_role("button", name="Salvar alterações").click()
            expect(page.get_by_role("status").first).to_contain_text(
                "Restaurante atualizado"
            )
            browser.close()
        self.assertEqual(Restaurante.objects.get().endereco, "Rua manual")
