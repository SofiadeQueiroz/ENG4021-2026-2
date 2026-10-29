from django import forms
from .models import Produto, Categoria, Restaurante



class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ['nome', 'descricao', 'preco', 'categoria', 'imagem']


class CadastroForm(forms.Form):
    nome = forms.CharField(max_length=100)
    email = forms.EmailField()
    cpf = forms.CharField(max_length=14)
    telefone = forms.CharField(max_length=15)
    senha = forms.CharField(widget=forms.PasswordInput, min_length=8)
    aceite = forms.BooleanField()

class LoginForm(forms.Form):
    email = forms.EmailField()
    senha = forms.CharField(widget=forms.PasswordInput)

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nome']

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

    

