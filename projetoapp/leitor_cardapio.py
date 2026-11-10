import re
from decimal import Decimal

import pymupdf

# Preço no fim da linha: "R$ 28,00", "28,00", "54.90", com ou sem pontilhado antes
PADRAO_PRECO = re.compile(r'[\s.\-–_]*(?:R\$\s*)?(\d{1,4}(?:[.,]\d{3})*[.,]\d{2})\s*$')

LIMITE_PAGINAS = 10


def extrair_linhas(arquivo_pdf):
    """Lê o PDF e devolve as linhas de texto, com o tamanho da maior letra de cada linha."""
    documento = pymupdf.open(stream=arquivo_pdf, filetype='pdf')
    if len(documento) > LIMITE_PAGINAS:
        raise ValueError(f'O PDF tem mais de {LIMITE_PAGINAS} páginas.')
    linhas = []
    for pagina in documento:
        pedacos = [
            pedaco
            for bloco in pagina.get_text('dict')['blocks']
            for linha in bloco.get('lines', [])
            for pedaco in linha['spans']
            if pedaco['text'].strip()
        ]
        meio = pagina.rect.width / 2

        # A página tem duas colunas se algum texto que não é preço começa na metade direita.
        # Num cardápio de uma coluna, só os preços (alinhados à direita) passam do meio.
        duas_colunas = any(
            p['bbox'][0] >= meio and not PADRAO_PRECO.fullmatch(p['text'].strip())
            for p in pedacos
        )

        # Separa os pedaços por coluna e, dentro de cada coluna, junta os que estão
        # na mesma altura da página (ex.: nome e preço)
        colunas = [{}, {}]
        for pedaco in pedacos:
            coluna = 1 if duas_colunas and pedaco['bbox'][0] >= meio else 0
            altura = round(pedaco['bbox'][1])
            colunas[coluna].setdefault(altura, []).append(pedaco)

        # Lê a coluna da esquerda inteira, depois a da direita
        for coluna in colunas:
            for altura in sorted(coluna):
                pedacos_da_linha = sorted(coluna[altura], key=lambda p: p['bbox'][0])
                texto = '  '.join(p['text'].strip() for p in pedacos_da_linha)
                tamanho = max(p['size'] for p in pedacos_da_linha)
                linhas.append({'texto': texto, 'tamanho': tamanho})
    return linhas


def converter_preco(texto):
    """Transforma '28,00', '54.90' ou '1.234,50' em Decimal."""
    if ',' in texto:
        texto = texto.replace('.', '').replace(',', '.')
    return Decimal(texto)


def eh_categoria(texto, tamanho, tamanho_normal):
    """Linha curta, sem números, em maiúsculas ou com letra maior que a dos produtos."""
    if len(texto) > 40 or any(c.isdigit() for c in texto):
        return False
    return texto.isupper() or (tamanho_normal and tamanho > tamanho_normal + 1)


def juntar_precos_soltos(linhas):
    """Se um preço veio sozinho numa linha, junta ele à linha de cima (o nome do produto)."""
    resultado = []
    for linha in linhas:
        preco = PADRAO_PRECO.search(linha['texto'])
        if preco and not linha['texto'][:preco.start()].strip() and resultado:
            resultado[-1] = dict(resultado[-1], texto=resultado[-1]['texto'] + '  ' + linha['texto'].strip())
        else:
            resultado.append(linha)
    return resultado


def interpretar_cardapio(linhas):
    """Transforma as linhas em uma lista de categorias, cada uma com seus produtos."""
    linhas = juntar_precos_soltos(linhas)

    # Tamanho de letra mais comum entre as linhas com preço = tamanho "normal" dos produtos
    tamanhos = [l['tamanho'] for l in linhas if l.get('tamanho') and PADRAO_PRECO.search(l['texto'])]
    tamanho_normal = max(set(tamanhos), key=tamanhos.count) if tamanhos else None

    categorias = []
    categoria = None
    produto = None
    for linha in linhas:
        texto = linha['texto'].strip()
        tamanho = linha.get('tamanho')
        preco = PADRAO_PRECO.search(texto)

        if preco:
            nome = texto[:preco.start()].strip()
            if categoria is None:
                categoria = {'nome': 'Sem categoria', 'produtos': []}
                categorias.append(categoria)
            produto = {'nome': nome, 'descricao': '', 'preco': converter_preco(preco.group(1))}
            categoria['produtos'].append(produto)
        elif eh_categoria(texto, tamanho, tamanho_normal):
            categoria = {'nome': texto.capitalize(), 'produtos': []}
            categorias.append(categoria)
            produto = None
        elif produto:
            # Linha comum depois de um produto: é a descrição dele
            produto['descricao'] = (produto['descricao'] + ' ' + texto).strip()
        # Linhas antes da primeira categoria (ex.: nome do restaurante) são ignoradas

    # Só ficam as categorias que têm pelo menos um produto
    return [c for c in categorias if c['produtos']]
