from django.contrib import admin
from .models import Categoria, Servico, Contato, Pedido

# Register your models here.
admin.site.register(Categoria)
admin.site.register(Contato)

# admin.site.register(Servico)

@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ["nome", "descricao", "preco", "imagem", "categoria", "ativo"]
    list_filter = ["categoria", "ativo"]
    search_fields = ["nome", "descricao"]
    ordering = ["nome", "preco"]
    list_per_page = 25


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ["usuario", "nome", "origem", "preco", "criado_em"]
    list_filter = ["usuario", "origem"]
    ordering = ["-criado_em"]