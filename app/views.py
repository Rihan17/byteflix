from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Contato, Servico, Categoria, Pedido
from .forms import FormContato, FormServico
from .supabase_client import supabase
import requests
from django.db.models import Count

# Create your views here.
def index(request):
    return render(request, "index.html")


def quem_somos(request):
    """Página institucional pública. A equipe vem do Supabase (banco remoto)."""
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
    """Vitrine pública: serviços/produtos do banco local + produtos de uma API externa."""
    produtos_locais = Servico.objects.filter(ativo=True).exclude(preco=0)

    # Requisição da API externa (FakeStore). Se a API estiver fora do ar,
    # a página continua funcionando só com os produtos locais.
    produtos_api = []
    erro_api = False
    try:
        resposta = requests.get("https://fakestoreapi.com/products", timeout=5)
        resposta.raise_for_status()
        produtos_api = resposta.json()
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
    """Adiciona um produto/serviço local ao carrinho do usuário logado."""
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
    """
    Adiciona um produto da API externa (FakeStore) ao carrinho. Os dados
    (nome, preço, imagem) são buscados na API no momento em que o item é
    adicionado, e ficam guardados no carrinho (sessão) pra não precisar bater
    na API de novo toda vez que a página do carrinho for aberta.
    """
    carrinho = _get_carrinho(request)
    chave = f"api-{produto_id}"

    if chave in carrinho:
        carrinho[chave]["quantidade"] += 1
    else:
        try:
            resposta = requests.get(f"https://fakestoreapi.com/products/{produto_id}", timeout=5)
            resposta.raise_for_status()
            produto = resposta.json()
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
    """Mostra os itens do carrinho antes de finalizar a compra."""
    carrinho_sessao = _get_carrinho(request)
    itens = []
    total = 0
    carrinho_alterado = False

    for chave, item in list(carrinho_sessao.items()):
        if item["origem"] == Pedido.ORIGEM_LOCAL:
            servico = Servico.objects.filter(id=item["id"], ativo=True).first()
            if not servico:
                # o serviço foi removido/desativado depois de entrar no carrinho
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
    """Confirma os itens do carrinho e registra cada um em Meus Pedidos."""
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
            for _ in range(quantidade):
                Pedido.objects.create(usuario=request.user, servico=servico, origem=Pedido.ORIGEM_LOCAL)
                pedidos_criados += 1
        else:
            # revalida o preço na API antes de confirmar, pra evitar preço desatualizado
            try:
                resposta = requests.get(f"https://fakestoreapi.com/products/{item['id']}", timeout=5)
                resposta.raise_for_status()
                produto = resposta.json()
            except requests.RequestException:
                pendentes[chave] = item
                continue

            if not produto or "title" not in produto:
                pendentes[chave] = item
                continue

            for _ in range(quantidade):
                Pedido.objects.create(
                    usuario=request.user,
                    origem=Pedido.ORIGEM_API,
                    produto_nome=produto.get("title", item.get("nome", "Produto parceiro")),
                    produto_preco=produto.get("price") or item.get("preco") or 0,
                    produto_imagem_url=produto.get("image", item.get("imagem", "")),
                )
                pedidos_criados += 1

    _salvar_carrinho(request, pendentes)

    if pedidos_criados:
        messages.success(request, f"Compra finalizada! {pedidos_criados} item(ns) adicionados aos seus pedidos.")

    if pendentes:
        messages.error(request, "Alguns itens não puderam ser confirmados agora e continuam no seu carrinho.")
        return redirect('carrinho')

    return redirect('meus_pedidos')


@login_required
def meus_pedidos(request):
    pedidos = Pedido.objects.filter(usuario=request.user).select_related('servico')
    total = sum((p.preco or 0) for p in pedidos)

    return render(request, "meus-pedidos.html", {
        "pedidos": pedidos,
        "total": total,
    })


@login_required
def addServicos(request):
    form = FormServico(request.POST, request.FILES or None)

    if request.POST:
        if form.is_valid():
            form.save()
            return redirect('servicos')

    return render(request, "add-servicos.html", {'form': form})


@login_required
def delServicos(request, id_servico):
    servico = get_object_or_404(Servico, id=id_servico)
    servico.delete()
    return redirect('servicos')


@login_required
def editServicos(request, id_servico):
    servico = get_object_or_404(Servico, id=id_servico)
    form = FormServico(request.POST or None, request.FILES or None, instance=servico)

    if request.POST:
        if form.is_valid():
            form.save()
            return redirect('servicos')

    return render(request, "edit-servicos.html", {'form': form})


def add_contato(request):
    form = FormContato(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Mensagem enviada com sucesso! Em breve entraremos em contato.")
        return redirect("index")
    return render(request, "add-contato.html", {"form": form})


@login_required
def contatos(request):
    return render(request, "contatos.html", {"contatos": Contato.objects.all().order_by('-id')})


@login_required
def del_contato(request, id_contato):
    contato = get_object_or_404(Contato, id=id_contato)
    contato.delete()
    return redirect("contatos")


@login_required
def integrantes(request):
    integrantes = []
    erro_supabase = False
    try:
        resposta = supabase.table("integrantes").select("*").execute()
        integrantes = resposta.data
    except Exception:
        erro_supabase = True

    return render(request, "integrantes.html", {
        'integrantes': integrantes,
        'erro_supabase': erro_supabase,
    })


@login_required
def addIntegrante(request):
    if request.method == "POST":
        nome = request.POST.get("nome")
        cargo = request.POST.get("cargo")
        biografia = request.POST.get("biografia")
        foto = request.POST.get("foto")

        try:
            supabase.table("integrantes").insert({
                "nome": nome, "cargo": cargo, "biografia": biografia, "foto_url": foto
            }).execute()
        except Exception:
            messages.error(request, "Não foi possível cadastrar o integrante no momento.")

        return redirect("integrantes")

    return render(request, "add-integrante.html")


@login_required
def editIntegrante(request, id_integrante):
    if request.method == "POST":
        nome = request.POST.get("nome")
        cargo = request.POST.get("cargo")
        biografia = request.POST.get("biografia")
        foto = request.POST.get("foto")

        try:
            supabase.table("integrantes").update({
                "nome": nome, "cargo": cargo, "biografia": biografia, "foto_url": foto
            }).eq("id", id_integrante).execute()
        except Exception:
            messages.error(request, "Não foi possível salvar as alterações no momento.")
            return redirect("integrantes")

        return redirect("integrantes")

    integrante = None
    try:
        resposta = supabase.table("integrantes").select("*").eq("id", id_integrante).execute()
        integrante = resposta.data[0] if resposta.data else None
    except Exception:
        messages.error(request, "Não foi possível carregar os dados da equipe no momento.")

    return render(request, "edit-integrante.html", {"integrante": integrante})


@login_required
def delIntegrante(request, id_integrante):
    try:
        supabase.table("integrantes").delete().eq("id", id_integrante).execute()
    except Exception:
        messages.error(request, "Não foi possível excluir o integrante no momento.")
    return redirect("integrantes")


@login_required
def relatorios(request):
    servicos = Servico.objects.all()
    servicos_ativos = servicos.filter(ativo=True).count()
    servicos_inativos = servicos.filter(ativo=False).count()

    categorias = servicos.values("categoria__nome").annotate(
        quantidade=Count("id")
    )

    total_pedidos = Pedido.objects.count()

    return render(request, "relatorio.html", {
        "servicos_ativos": servicos_ativos,
        "servicos_inativos": servicos_inativos,
        "total_pedidos": total_pedidos,
        "categorias_labels": [
            item["categoria__nome"] or "Sem categoria"
            for item in categorias
        ],
        "categorias_valores": [
            item["quantidade"] for item in categorias
        ],
    })
