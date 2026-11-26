# FoodLink

Cardápio digital para restaurantes, feito em **Django** na disciplina ENG4021 (PUC-Rio, 2026.2).

O **restaurante** cadastra o cardápio, e o **cliente** encontra estabelecimentos, vê os pratos, os ingredientes e os alergênicos, e salva os favoritos.

## O que o app faz

**Para o restaurante**
- Cadastro, login (e-mail e senha ou Google) e recuperação de senha por e-mail.
- Cadastro dos dados do restaurante, com consulta de endereço pelo CEP.
- Cardápio: adicionar, editar e apagar produtos e categorias, marcar o prato como indisponível e importar o cardápio de um PDF.
- Escolha da cor de destaque do cardápio público.
- QR Code que leva ao cardápio público.
- Consultas rápidas: CNPJ, informações nutricionais e alergênicos.

**Para o cliente**
- Busca de estabelecimentos no mapa e opção "Perto de mim".
- Cardápio público em português ou inglês, com preços em várias moedas.
- Página do prato com ingredientes e alergênicos.
- Filtro para esconder pratos com os alergênicos que a pessoa quer evitar.
- Favoritos salvos na conta.

## APIs usadas

| API | Para quê |
|---|---|
| ViaCEP | Preencher o endereço pelo CEP |
| BrasilAPI | Dados de CNPJ e feriados |
| USDA FoodData Central | Informações nutricionais |
| Open Food Facts | Alergênicos e ingredientes de produtos |
| Nominatim (OpenStreetMap) | Localização e mapa |
| MyMemory | Tradução do cardápio |
| AwesomeAPI | Cotação de moedas |
| QR Server | Geração do QR Code |
| Resend | E-mail de recuperação de senha |

## Como rodar

Precisa do Python 3.12 ou mais novo.

```bash
git clone https://github.com/SofiadeQueiroz/ENG4021-2026-2.git
cd ENG4021-2026-2
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Depois abra `http://127.0.0.1:8000/`.

### Variáveis de ambiente (opcional)

Crie um arquivo `.env` na pasta do projeto para ligar o e-mail e o login com Google:

```
RESEND_API_KEY=...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

Sem elas o app funciona, mas a recuperação de senha por e-mail e o login com Google ficam desligados.

## Testes

```bash
python manage.py test
```

## Como o código está organizado

```
projeto/              configurações e lista de endereços (urls.py)
projetoapp/
  views.py            a lógica de cada tela
  models.py           as tabelas: Restaurante, Produto, Categoria, Perfil e Favorito
  forms.py            os formulários
  templates/          o HTML de cada tela
  static/css/         o CSS de cada tela
  leitor_cardapio.py  leitura do cardápio em PDF
```

Cada tela segue o mesmo caminho: **endereço** (`urls.py`) → **view** (`views.py`) → **HTML** (`templates/`) + **CSS** (`static/css/`).

## Equipe

Juliana Braunstein Bassan, Rafael De Alessio Meira C Laxe, Lucas Monnerat Aylmer, Joao Paulo Garcia Barroso, Sofia Pereira De Queiroz Ferreira e Diego Rocha Pedrosa.
