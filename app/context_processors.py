def carrinho_contexto(request):
    """Disponibiliza a quantidade de itens do carrinho em todos os templates,
    para mostrar o número no menu de navegação sem precisar repetir isso em
    cada view."""
    carrinho = request.session.get("carrinho", {})
    quantidade_total = sum(item.get("quantidade", 0) for item in carrinho.values())
    return {"carrinho_quantidade": quantidade_total}
