from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import Produto, Categoria, Restaurante, Perfil



class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ['nome', 'descricao', 'preco', 'categoria', 'imagem','ingredientes',
            'alergenicos']


class CadastroForm(forms.Form):
    tipo = forms.ChoiceField(choices=Perfil.TIPOS, widget=forms.HiddenInput)
    nome = forms.CharField(max_length=100)
    email = forms.EmailField(max_length=150)
    cpf = forms.CharField(max_length=14, required=False)
    cnpj = forms.CharField(max_length=18, required=False)
    telefone = forms.CharField(max_length=15)
    senha = forms.CharField(widget=forms.PasswordInput, min_length=8)
    confirmar_senha = forms.CharField(widget=forms.PasswordInput)
    aceite = forms.BooleanField()

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(username__iexact=email).exists():
            raise forms.ValidationError('Esse e-mail já está cadastrado.')
        return email

    def clean(self):
        dados = super().clean()
        senha = dados.get('senha')
        if senha:
            usuario = User(username=dados.get('email', ''), first_name=dados.get('nome', ''))
            try:
                validate_password(senha, usuario)
            except forms.ValidationError as erro:
                self.add_error('senha', erro)
        if senha and dados.get('confirmar_senha') and senha != dados['confirmar_senha']:
            self.add_error('confirmar_senha', 'As senhas não coincidem.')
        tipo = dados.get('tipo')
        cpf = ''.join(c for c in dados.get('cpf', '') if c.isdigit())
        cnpj = ''.join(c for c in dados.get('cnpj', '') if c.isdigit())
        if tipo == 'cliente' and len(cpf) != 11:
            self.add_error('cpf', 'Digite um CPF com 11 números.')
        if tipo == 'estabelecimento' and len(cnpj) != 14:
            self.add_error('cnpj', 'Digite um CNPJ com 14 números.')
        dados['cpf'] = cpf if tipo == 'cliente' else ''
        dados['cnpj'] = cnpj if tipo == 'estabelecimento' else ''
        return dados

class LoginForm(forms.Form):
    email = forms.EmailField(max_length=150)
    senha = forms.CharField(widget=forms.PasswordInput)

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nome']

class ItemImportadoForm(forms.Form):
    incluir = forms.BooleanField(required=False, initial=True)
    categoria = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'list': 'lista-categorias'}))
    nome = forms.CharField(max_length=100, required=False)
    descricao = forms.CharField(required=False)
    preco = forms.DecimalField(max_digits=8, decimal_places=2, min_value=0, required=False)

    def clean(self):
        dados = super().clean()
        # Só exige os campos dos itens que vão ser importados
        if dados.get('incluir'):
            for campo in ['categoria', 'nome', 'preco']:
                if dados.get(campo) in (None, ''):
                    self.add_error(campo, 'Preencha este campo ou desmarque o item.')
        return dados

ItensImportadosFormSet = forms.formset_factory(ItemImportadoForm, extra=0)

class RestauranteForm(forms.ModelForm):
    class Meta:
        model = Restaurante
        fields = ['nome', 'descricao', 'cozinha', 'horario', 'endereco', 'imagem']

class ConsultaCEPForm(forms.Form):
    cep = forms.RegexField(
        regex=r'^[0-9]{5}-?[0-9]{3}$',
        max_length=9,
        required=False,
        error_messages={'invalid': 'Informe um CEP com 8 números, como 01001-000.'},
        widget=forms.TextInput(attrs={'inputmode': 'numeric', 'placeholder': '00000-000'}),
    )

    def clean_cep(self):
        cep = self.cleaned_data['cep']
        if not cep:
            raise forms.ValidationError('Informe o CEP para fazer a consulta.')
        return cep

class EsqueciSenhaForm(forms.Form):
    email = forms.EmailField()

class NovaSenhaForm(forms.Form):
    senha = forms.CharField(widget=forms.PasswordInput, min_length=8)
    confirmar_senha = forms.CharField(widget=forms.PasswordInput, min_length=8)

    def clean(self):
        dados = super().clean()
        if dados.get('senha') and dados.get('confirmar_senha'):
            if dados['senha'] != dados['confirmar_senha']:
                self.add_error('confirmar_senha', 'As senhas não são iguais.')
        return dados