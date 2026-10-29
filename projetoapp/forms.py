import re

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import (
    validate_password,
    password_validators_help_text_html,
)
from django.db import transaction
from django.db.models import Q

from .models import Produto, Categoria, Restaurante, Perfil
from .services import normalizar_cep


class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ["nome", "descricao", "preco", "categoria", "imagem"]


class CadastroForm(forms.Form):
    nome = forms.CharField(
        label="Nome completo",
        max_length=100,
        widget=forms.TextInput(attrs={"autocomplete": "name"}),
    )
    email = forms.EmailField(
        label="E-mail",
        max_length=150,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )
    cpf = forms.CharField(
        label="CPF",
        max_length=14,
        widget=forms.TextInput(
            attrs={"inputmode": "numeric", "placeholder": "000.000.000-00"}
        ),
    )
    telefone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={"type": "tel", "autocomplete": "tel"}),
    )
    senha = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text=password_validators_help_text_html(),
    )
    confirmar_senha = forms.CharField(
        label="Confirmar senha",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    aceite = forms.BooleanField(
        label="Concordo com o uso destes dados para criar minha conta no FoodLink."
    )

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if (
            get_user_model()
            .objects.filter(Q(username__iexact=email) | Q(email__iexact=email))
            .exists()
        ):
            raise forms.ValidationError("Esse e-mail já está cadastrado.")
        return email

    def clean_cpf(self):
        raw = self.cleaned_data["cpf"]
        if not re.fullmatch(
            r"(?:[0-9]{11}|[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2})", raw
        ):
            raise forms.ValidationError("Informe um CPF válido.")
        cpf = re.sub(r"[^0-9]", "", raw)
        if len(set(cpf)) == 1:
            raise forms.ValidationError("Informe um CPF válido.")
        for length in (9, 10):
            digit = (
                sum(int(cpf[i]) * (length + 1 - i) for i in range(length)) * 10 % 11
            ) % 10
            if digit != int(cpf[length]):
                raise forms.ValidationError("Informe um CPF válido.")
        return cpf

    def clean_telefone(self):
        telefone = re.sub(r"[()\s-]", "", self.cleaned_data["telefone"])
        if not re.fullmatch(r"[1-9][0-9]{9,10}", telefone):
            raise forms.ValidationError("Informe DDD e telefone com 10 ou 11 dígitos.")
        return telefone

    def clean(self):
        dados = super().clean()
        senha = dados.get("senha")
        if senha:
            usuario = get_user_model()(
                username=dados.get("email", ""),
                email=dados.get("email", ""),
                first_name=dados.get("nome", ""),
            )
            try:
                validate_password(senha, usuario)
            except forms.ValidationError as error:
                self.add_error("senha", error)
        if senha and dados.get("confirmar_senha") and senha != dados["confirmar_senha"]:
            self.add_error("confirmar_senha", "As senhas não coincidem.")
        return dados

    @transaction.atomic
    def save(self):
        dados = self.cleaned_data
        usuario = get_user_model().objects.create_user(
            username=dados["email"],
            email=dados["email"],
            password=dados["senha"],
            first_name=dados["nome"],
        )
        Perfil.objects.create(
            usuario=usuario, cpf=dados["cpf"], telefone=dados["telefone"]
        )
        return usuario


class LoginForm(forms.Form):
    email = forms.EmailField(
        label="E-mail",
        max_length=150,
        widget=forms.EmailInput(attrs={"autocomplete": "username"}),
    )
    senha = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nome"]


class RestauranteForm(forms.ModelForm):
    cep = forms.CharField(
        label="CEP",
        max_length=9,
        required=False,
        widget=forms.TextInput(
            attrs={
                "inputmode": "numeric",
                "autocomplete": "postal-code",
                "placeholder": "00000-000",
                "aria-describedby": "cep-status",
            }
        ),
    )

    class Meta:
        model = Restaurante
        fields = [
            "nome",
            "descricao",
            "cozinha",
            "horario",
            "cep",
            "endereco",
            "numero",
            "complemento",
            "bairro",
            "cidade",
            "estado",
            "imagem",
        ]
        labels = {
            "endereco": "Rua / logradouro",
            "numero": "Número",
            "estado": "UF",
            "horario": "Funcionamento",
        }

    def clean_cep(self):
        cep = self.cleaned_data["cep"]
        if not cep:
            return ""
        try:
            return normalizar_cep(cep)
        except ValueError as error:
            raise forms.ValidationError(str(error)) from error

    def clean_estado(self):
        estado = self.cleaned_data["estado"].upper()
        if (
            estado
            and estado
            not in "AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split()
        ):
            raise forms.ValidationError("Informe uma UF válida, como RJ ou SP.")
        return estado


class EsqueciSenhaForm(forms.Form):
    email = forms.EmailField()
