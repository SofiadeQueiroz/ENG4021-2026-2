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

    

