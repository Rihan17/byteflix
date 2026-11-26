def carrinho_contexto(request):
    carrinho = request.session.get("carrinho", {})
    quantidade_total = sum(item.get("quantidade", 0) for item in carrinho.values())
    return {"carrinho_quantidade": quantidade_total}
