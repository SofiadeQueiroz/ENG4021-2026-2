# Validação das três tarefas médias

Execução local em **29/10/2026**, Windows, Python 3.12.12, Django 5.2.18 e Playwright 1.64.1. Base do trabalho: `5b1d0d5`.

## Resultado

| Verificação | Resultado observado |
| --- | --- |
| `python manage.py check` | Sem problemas |
| `python manage.py makemigrations --check --dry-run` | Nenhuma migração pendente |
| `python manage.py test` | **32 testes aprovados** |
| `python manage.py test projetoapp.browser_tests` | **6 testes aprovados**, em 142,300 s |
| Matriz de layout incluída no teste de navegador | **160 de 160 cenários aprovados** |
| Consulta real ao ViaCEP, fora dos testes simulados | CEP `01001-000` retornou Praça da Sé, Sé, São Paulo/SP |

Os seis testes de navegador compreendem a matriz de layout e cinco fluxos: cadastro/login/logout; consulta e salvamento do endereço; erros de CEP/rede preservando a edição manual; alteração de CEP durante uma consulta; salvamento com JavaScript desativado.

## 1. Cadastro, login e logout

- Cadastro persiste usuário e perfil na mesma transação. Senha é armazenada com hash; CPF e telefone são normalizados.
- CPF inválido, telefone inválido, senha fraca, confirmação divergente, falta de aceite e e-mail repetido são rejeitados. Duplicidade de e-mail ignora maiúsculas/minúsculas.
- Login aceita e-mail com variação de caixa, preserva destinos internos e rejeita redirecionamentos para domínios externos. Senha errada e conta inativa não criam sessão.
- Logout exige POST/CSRF e invalida a sessão anterior. Rotas privadas redirecionam visitantes ao login, tanto em GET como em POST; páginas públicas permanecem abertas.
- Uma conta não lê nem sobrescreve o restaurante/produtos de outra pelo gerenciamento. Dados antigos sem dono não são apropriados automaticamente.

## 2. Integração com ViaCEP

A API foi escolhida porque o restaurante já possui endereço no domínio do projeto. O preenchimento por CEP reduz digitação. O escopo médio proposto combina serviço Django, endpoint autenticado, interface assíncrona, persistência, cache e tratamento de falhas.

Testes cobrem sucesso, normalização, cache, CEP inexistente, formato inválido, timeout, falha HTTP/conexão, JSON inválido, resposta incompleta, CEP divergente e retorno de CEP genérico sem rua/bairro. O navegador também confirma que número/complemento são preservados e que os campos continuam editáveis após falhas.

As respostas dos testes automatizados são simuladas para permitir repetição sem depender de internet. A consulta real adicional confirmou a comunicação HTTPS com o serviço. Referência: [documentação oficial do ViaCEP](https://viacep.com.br/).

## 3. Responsividade testada

| Resolução CSS | Chromium 156.0.8078.4 | WebKit 27.2 |
| --- | --- | --- |
| 320 × 568 | 16/16 | 16/16 |
| 375 × 812 | 16/16 | 16/16 |
| 768 × 1024 | 16/16 | 16/16 |
| 1440 × 900 | 16/16 | 16/16 |
| 812 × 375, horizontal | 16/16 | 16/16 |
| **Total** | **80/80** | **80/80** |

Telas: boas-vindas, cadastro, login, recuperação de senha, início do cliente, busca, QR Code, cardápio público, detalhes do produto, favoritos, cardápio do dono, edição de produto, adição de produto, categoria, aparência e restaurante. As telas privadas são acessadas com uma sessão real. O cardápio de teste contém nome/descrição longos e uma imagem para exercitar quebra de linhas.

Em cada cenário, o navegador verifica ausência de rolagem horizontal; campos, botões, imagens e links do menu dentro da largura da tela; controles de formulário com pelo menos 44 px de altura (tolerância de 1 px); imagens locais carregadas; ausência de erros HTTP/JavaScript; viewport configurado e foco visível no atalho de teclado para o conteúdo. Os fluxos de cadastro e salvamento também exercitam os botões em telas estreitas.

Resultados individuais: [matriz JSON com 160 registros](evidencias/responsive-matrix.json).

Capturas reais selecionadas, também inspecionadas visualmente:

| Evidência | Arquivo |
| --- | --- |
| Cadastro, celular de 320 px | [Abrir captura](evidencias/cadastro-320.png) |
| Meu restaurante, celular de 375 px | [Abrir captura](evidencias/restaurante-375.png) |
| Aparência, tablet de 768 px | [Abrir captura](evidencias/aparencia-768.png) |
| Cardápio do dono, desktop de 1440 px | [Abrir captura](evidencias/cardapio-1440.png) |
| Login no WebKit, celular de 320 px | [Abrir captura](evidencias/login-webkit-320.png) |

A primeira execução identificou seletores de rótulos que precisavam de ajuste e uma diferença de foco de links no WebKit. Os rótulos foram padronizados e o atalho recebeu `tabindex="0"`; depois a matriz completa foi executada novamente com sucesso. O Firefox baixado não iniciou neste Windows devido a uma dependência de ativação do executável, portanto **não é contado como navegador validado**.

São testes de navegador com viewport emulado, não testes em aparelhos físicos. As telas que já eram protótipos continuam com seu escopo anterior, conforme o README; a validação de layout não equivale à implementação dessas outras funcionalidades. A migração preserva dados antigos sem atribuir dono automaticamente.

## Reproduzir

Os comandos completos estão no [README](../README.md). O workflow [Testes FoodLink](../.github/workflows/tests.yml) executa verificações Django e a matriz no GitHub Actions, guardando as capturas em um artefato. Os resultados acima descrevem a execução local; o estado do CI deve ser consultado nos checks do PR.
