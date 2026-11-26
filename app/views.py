from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Contato, Servico, Categoria, Pedido
from .forms import FormContato, FormServico
from .supabase_client import supabase
import logging
import requests
from django.db.models import Count

logger = logging.getLogger(__name__)

API_LOJA = "https://dummyjson.com/products"
CAMPOS_API = "id,title,description,price,thumbnail,category"
CABECALHOS_API = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "application/json",
}


def _normalizar_produto(dados):
    return {
        "id": dados.get("id"),
        "title": dados.get("title", ""),
        "description": dados.get("description", ""),
        "price": dados.get("price") or 0,
        "image": dados.get("thumbnail", ""),
        "category": dados.get("category", ""),
    }


def _api_loja(caminho=""):
    parametros = {"select": CAMPOS_API}
    if not caminho:
        parametros["limit"] = 20

    ultimo_erro = None
    for tentativa in (1, 2):
        try:
            resposta = requests.get(
                f"{API_LOJA}{caminho}",
                params=parametros,
                headers=CABECALHOS_API,
                timeout=8,
            )
            resposta.raise_for_status()
            dados = resposta.json()
            if caminho:
                return _normalizar_produto(dados) if dados.get("title") else None
            return [_normalizar_produto(p) for p in dados.get("products", [])]
        except (requests.RequestException, ValueError, AttributeError) as erro:
            ultimo_erro = erro
            logger.error("API de produtos falhou (%s, tentativa %s): %s: %s",
                         caminho or "/products", tentativa, type(erro).__name__, erro)
    raise requests.RequestException(str(ultimo_erro))


# Create your views here.
def index(request):
    return render(request, "index.html")


def quem_somos(request):
    integrantes = []
    erro_supabase = False
    try:
        resposta = supabase.table("integrantes").select("*").execute()
        integrantes = resposta.data
    except Exception:
        erro_supabase = True

    return render(request, "quem-somos.html", {
        "integrantes": integrantes,
        "erro_supabase": erro_supabase,
    })


@login_required
def servicos(request):
    # servicos = Servico.objects.all()

    servicos = Servico.objects.filter(ativo=True)
    servicos = servicos.exclude(preco=0)

    total_servicos = servicos.count()
    tem_servicos = servicos.exists()

    mais_barato = servicos.order_by('preco').first()
    mais_caro = servicos.order_by('-preco').first()

    # recupera o valor do form
    busca = request.GET.get('busca')

    if busca:
        servicos = servicos.filter(nome__icontains=busca)

    # recupera todas as categorias ativas
    categorias = Categoria.objects.filter(ativo=True)

    # recupera o valor do form ele cria a variavel categoria
    categoria = request.GET.get('categoria')

    # se uma categoria foi selecionada
    if categoria:
        # atualiza a lista de serviços de acordo com a categoria
        servicos = servicos.filter(categoria_id=categoria)

    preco = request.GET.get('preco')

    if preco == 'baixo':
        servicos = servicos.filter(preco__lte=500)
    elif preco == 'medio':
        servicos = servicos.filter(
            preco__gte=500,
            preco__lte=1500
        )
    elif preco == 'alto':
        servicos = servicos.filter(preco__gt=1500)

    # recupera o valor da url
    ordem = request.GET.get('ordem')

    if ordem == 'menor':
        servicos = servicos.order_by('preco')  # ordena por preço (crescente)
    elif ordem == 'maior':
        servicos = servicos.order_by('-preco')  # ordena por preço (decrescente)
    elif ordem == 'nome':
        servicos = servicos.order_by('nome')  # ordena por nome (A-Z)
    else:
        servicos = servicos.order_by('nome')

    contexto = {
        'servicos': servicos,
        'total_servicos': total_servicos,
        'tem_servicos': tem_servicos,
        'mais_barato': mais_barato,
        'mais_caro': mais_caro,
        'categorias': categorias,
        'categoria': categoria,
        'preco': preco,
        'ordem': ordem,
    }

    return render(request, "servicos.html", contexto)


def produtos(request):
    produtos_locais = Servico.objects.filter(ativo=True).exclude(preco=0)

    produtos_api = []
    erro_api = False
    try:
        produtos_api = _api_loja()
    except requests.RequestException:
        erro_api = True

    return render(request, "produtos.html", {
        "produtos": produtos_locais,
        "produtos_api": produtos_api,
        "erro_api": erro_api,
    })


def _get_carrinho(request):
    return request.session.setdefault("carrinho", {})


def _salvar_carrinho(request, carrinho):
    request.session["carrinho"] = carrinho
    request.session.modified = True


@login_required
def adicionar_carrinho_local(request, id_servico):
    servico = get_object_or_404(Servico, id=id_servico, ativo=True)

    carrinho = _get_carrinho(request)
    chave = f"local-{servico.id}"

    if chave in carrinho:
        carrinho[chave]["quantidade"] += 1
    else:
        carrinho[chave] = {"origem": Pedido.ORIGEM_LOCAL, "id": servico.id, "quantidade": 1}

    _salvar_carrinho(request, carrinho)
    messages.success(request, f'"{servico.nome}" foi adicionado ao carrinho!')
    return redirect('produtos')


@login_required
def adicionar_carrinho_api(request, produto_id):
    carrinho = _get_carrinho(request)
    chave = f"api-{produto_id}"

    if chave in carrinho:
        carrinho[chave]["quantidade"] += 1
    else:
        try:
            produto = _api_loja(f"/{produto_id}")
        except requests.RequestException:
            messages.error(request, "Não foi possível adicionar esse produto ao carrinho agora. Tente novamente mais tarde.")
            return redirect('produtos')

        if not produto or "title" not in produto:
            messages.error(request, "Produto não encontrado na loja parceira.")
            return redirect('produtos')

        carrinho[chave] = {
            "origem": Pedido.ORIGEM_API,
            "id": produto_id,
            "quantidade": 1,
            "nome": produto.get("title", "Produto parceiro"),
            "preco": float(produto.get("price") or 0),
            "imagem": produto.get("image", ""),
        }

    _salvar_carrinho(request, carrinho)
    messages.success(request, "Produto adicionado ao carrinho!")
    return redirect('produtos')


@login_required
def remover_carrinho(request, chave):
    carrinho = _get_carrinho(request)
    carrinho.pop(chave, None)
    _salvar_carrinho(request, carrinho)
    return redirect('carrinho')


@login_required
def carrinho(request):
    carrinho_sessao = _get_carrinho(request)
    itens = []
    total = 0
    carrinho_alterado = False

    for chave, item in list(carrinho_sessao.items()):
        if item["origem"] == Pedido.ORIGEM_LOCAL:
            servico = Servico.objects.filter(id=item["id"], ativo=True).first()
            if not servico:
                carrinho_sessao.pop(chave, None)
                carrinho_alterado = True
                continue
            preco_unitario = servico.preco
            nome = servico.nome
            imagem = servico.imagem.url if servico.imagem else ""
        else:
            preco_unitario = item["preco"]
            nome = item["nome"]
            imagem = item.get("imagem", "")

        subtotal = preco_unitario * item["quantidade"]
        total += subtotal

        itens.append({
            "chave": chave,
            "origem": item["origem"],
            "nome": nome,
            "imagem": imagem,
            "preco_unitario": preco_unitario,
            "quantidade": item["quantidade"],
            "subtotal": subtotal,
        })

    if carrinho_alterado:
        _salvar_carrinho(request, carrinho_sessao)

    return render(request, "carrinho.html", {
        "itens": itens,
        "total": total,
    })


@login_required
def finalizar_compra(request):
    if request.method != "POST":
        return redirect('carrinho')

    carrinho_sessao = _get_carrinho(request)

    if not carrinho_sessao:
        messages.error(request, "Seu carrinho está vazio.")
        return redirect('produtos')

    pendentes = {}
    pedidos_criados = 0

    for chave, item in carrinho_sessao.items():
        quantidade = item["quantidade"]

        if item["origem"] == Pedido.ORIGEM_LOCAL:
            servico = Servico.objects.filter(id=item["id"], ativo=True).first()
            if not servico:
                pendentes[chave] = item
                continue
            for _ in
