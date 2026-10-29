"""Consulta ao ViaCEP: somente CEP é enviado; nenhuma chave ou dado de conta."""

import re

import requests
from django.core.cache import cache


class CEPNaoEncontrado(Exception):
    pass


class CEPIndisponivel(Exception):
    pass


def normalizar_cep(cep):
    cep = cep.strip()
    if not re.fullmatch(r"[0-9]{5}-?[0-9]{3}", cep):
        raise ValueError("Informe um CEP com 8 dígitos, como 01001-000.")
    return cep.replace("-", "")


def consultar_cep(cep):
    cep = normalizar_cep(cep)
    key = f"viacep:{cep}"
    cached = cache.get(key)
    if cached is not None:
        return cached
    try:
        response = requests.get(
            f"https://viacep.com.br/ws/{cep}/json/",
            timeout=(2, 3),
            allow_redirects=False,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as error:
        raise CEPIndisponivel(
            "A consulta de CEP está indisponível. Preencha o endereço manualmente ou tente novamente."
        ) from error
    invalid = "O serviço de CEP retornou uma resposta inválida. Preencha o endereço manualmente."
    if not isinstance(data, dict):
        raise CEPIndisponivel(invalid)
    if data.get("erro") in (True, "true"):
        raise CEPNaoEncontrado(
            "CEP não encontrado. Confira os números ou preencha o endereço manualmente."
        )
    fields = {
        "endereco": ("logradouro", 100),
        "bairro": ("bairro", 100),
        "cidade": ("localidade", 100),
        "estado": ("uf", 2),
    }
    result = {"cep": cep}
    for field, (source, limit) in fields.items():
        value = data.get(source)
        if not isinstance(value, str) or len(value) > limit:
            raise CEPIndisponivel(invalid)
        result[field] = value
    returned_cep = data.get("cep")
    if (
        not result["cidade"]
        or not re.fullmatch(r"[A-Z]{2}", result["estado"])
        or not isinstance(returned_cep, str)
        or returned_cep.replace("-", "") != cep
    ):
        raise CEPIndisponivel(invalid)
    cache.set(key, result, timeout=60 * 60 * 24)
    return result
