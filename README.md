# FoodLink · ENG4021-2026-2

Aplicação Django de cardápios digitais. Esta entrega implementa três tarefas de escopo médio:

| Tarefa | Entrega |
| --- | --- |
| Cadastro / Login / Logout | Conta persistida, validação de CPF, telefone, e-mail e senha, confirmação de senha, sessão, saída por POST com CSRF, rotas privadas e dados de gerenciamento separados por usuário. |
| Integração com API | ViaCEP no formulário **Meu restaurante**, com consulta pelo servidor, preenchimento de endereço, cache, timeout, tratamento de erros, descarte de respostas antigas e alternativa manual. |
| Responsividade | Layout compartilhado nas 16 telas, viewport, imagens e formulários fluidos, navegação por teclado e testes reais em Chromium e WebKit. |

## Executar localmente

Requisitos: Python 3.12 e pip. O projeto usa Django 5.2 LTS e SQLite. Na pasta do repositório:

```sh
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Abra <http://127.0.0.1:8000/>, crie uma conta e entre. O menu da conta oferece **Sair** em todas as páginas autenticadas. Em **Meu restaurante**, consulte o CEP, confira o endereço, informe número/complemento e salve.

As configurações incluídas são para desenvolvimento local. O backend de e-mail escreve no console. Configuração de hospedagem/HTTPS e envio de e-mail não fazem parte desta entrega.

## Por que ViaCEP?

O endereço do restaurante já faz parte do FoodLink. A consulta por CEP reduz a digitação e ajuda a preencher rua, bairro, cidade e UF. A [documentação oficial do ViaCEP](https://viacep.com.br/) especifica o formato de oito dígitos e os retornos de erro usados nesta implementação.

- Endpoint interno autenticado: `GET /api/cep/?cep=01001-000`.
- Endpoint externo fixo: `https://viacep.com.br/ws/{cep}/json/`. Apenas o CEP é enviado; não são enviados nome, CPF, telefone ou dados da conta.
- Validação antes da chamada; códigos internos 400 (formato), 404 (não encontrado) e 503 (indisponibilidade/resposta inválida).
- Timeout de conexão/leitura de 2/3 segundos; cache de sucessos por 24 horas, sem cache de falhas. O cache padrão é local ao processo Django.
- O navegador limita a espera a 8 segundos, anuncia o resultado e cancela uma consulta se o CEP mudar. Número/complemento são preservados.
- Campos editáveis e salvamento manual funcionam com a API indisponível ou com JavaScript desativado. A consulta é opcional e não valida a existência física do restaurante.

Esse conjunto de serviço, interface, persistência e tratamento de falhas é o escopo proposto como **médio** para a tarefa de API, cuja classificação final cabe à avaliação da disciplina. A antiga chamada de filmes na página inicial foi removida por não ser usada no FoodLink.

## Testar

```sh
python -m pip install -r requirements-dev.txt
python -m playwright install chromium webkit
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
python manage.py test projetoapp.browser_tests
```

Os testes Django usam banco temporário e simulam respostas da API. Os testes de navegador executam cadastro/login/logout, consulta e salvamento do endereço, erros de rede, resposta obsoleta e preenchimento sem JavaScript. Não dependem de uma API externa disponível.

A matriz de responsividade visita **16 telas × 5 resoluções × 2 navegadores = 160 cenários**: 320×568, 375×812, 768×1024, 1440×900 e 812×375. Verifica rolagem horizontal, controles dentro da tela, tamanho dos campos/botões, imagens locais, recursos HTTP, erros JavaScript e acesso por teclado. Gera capturas e `test-results/responsive-matrix.json`; a pasta é ignorada pelo Git. No CI, as evidências ficam disponíveis como artefato do GitHub Actions.

Veja o [relatório de validação](docs/VALIDACAO.md) para os resultados e capturas selecionadas.

## Banco existente e limites de escopo

A migração `0003` adiciona perfil, dono e campos de endereço sem apagar registros existentes. Produtos, categorias e restaurantes antigos ficam com `dono=NULL`, sem serem atribuídos automaticamente a uma nova conta. Se já houver dados, o mantenedor deve vincular cada registro ao usuário correto pelo Django shell antes de usá-lo no gerenciamento. Cada conta possui no máximo um restaurante.

As telas preexistentes de cardápio público, favoritos, busca/mapa, edição/exclusão, aparência e leitor de QR mantêm seus comportamentos de protótipo; receberam ajustes de layout e navegação. O fluxo preexistente de recuperação de senha apenas envia um aviso, sem redefinição por token. Essas funcionalidades não são apresentadas como parte das três implementações acima.
