from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("quem-somos/", views.quem_somos, name="quem_somos"),
    path("servicos", views.servicos, name="servicos"),
    path("produtos", views.produtos, name="produtos"),
    path("carrinho/adicionar/<int:id_servico>/", views.adicionar_carrinho_local, name="adicionar_carrinho_local"),
    path("carrinho/adicionar-api/<int:produto_id>/", views.adicionar_carrinho_api, name="adicionar_carrinho_api"),
    path("carrinho/remover/<str:chave>/", views.remover_carrinho, name="remover_carrinho"),
    path("carrinho/", views.carrinho, name="carrinho"),
    path("carrinho/finalizar/", views.finalizar_compra, name="finalizar_compra"),
    path("meus-pedidos/", views.meus_pedidos, name="meus_pedidos"),
    path("add-servicos", views.addServicos, name="addServicos"),
    path("del-servicos/<int:id_servico>", views.delServicos, name="delServicos"),
    path("edit-servicos/<int:id_servico>", views.editServicos, name="editServicos"),
    path("contato/add-contato/", views.add_contato, name="add_contato"),
    path("contato/contatos/", views.contatos, name="contatos"),
    path("contato/del-contato/<int:id_contato>/", views.del_contato, name="del_contato"),
    path("integrantes", views.integrantes, name="integrantes"),
    path("add-integrante", views.addIntegrante, name="addIntegrante"),
    path("edit-integrante/<str:id_integrante>/", views.editIntegrante, name="editIntegrante"),
    path("del-integrante/<str:id_integrante>", views.delIntegrante, name="delIntegrante"),
    path("relatorios/", views.relatorios, name="relatorios"),
]
