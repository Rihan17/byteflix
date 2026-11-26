from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Categoria(models.Model):
    nome = models.CharField(max_length=100, default="Geral")
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome


class Servico(models.Model):
    nome = models.CharField(max_length=150)
    descricao = models.TextField(blank=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    imagem = models.ImageField(upload_to='servicos/', blank=True, null=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='servicos', null = True, blank = True)
    
    def __str__(self):
        return self.nome


class Contato(models.Model):
    nome = models.CharField(max_length=100)
    email = models.EmailField()
    telefone = models.CharField(max_length=20, blank=True)
    mensagem = models.TextField()

    class Meta:
        db_table = "contato_contato"

    def __str__(self):
        return self.nome


class Pedido(models.Model):
    """
    Registro de uma compra feita por um cliente logado.

    Pode ser:
    - um serviço/produto do banco local (campo `servico` preenchido), ou
    - um produto vindo da API externa (campos `produto_*` preenchidos, já
      que esses produtos não existem numa tabela local).
    """
    ORIGEM_LOCAL = 'local'
    ORIGEM_API = 'api'
    ORIGEM_CHOICES = [
        (ORIGEM_LOCAL, 'Produto/serviço local'),
        (ORIGEM_API, 'Produto de loja parceira (API)'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pedidos')
    servico = models.ForeignKey(Servico, on_delete=models.CASCADE, related_name='pedidos', null=True, blank=True)
    origem = models.CharField(max_length=10, choices=ORIGEM_CHOICES, default=ORIGEM_LOCAL)

    # Preenchidos só quando origem == 'api': guardam uma "foto" dos dados do
    # produto no momento da compra, já que o produto vem de fora do banco.
    produto_nome = models.CharField(max_length=200, blank=True)
    produto_preco = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    produto_imagem_url = models.URLField(max_length=500, blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']

    @property
    def nome(self):
        return self.servico.nome if self.servico_id else self.produto_nome

    @property
    def preco(self):
        return self.servico.preco if self.servico_id else self.produto_preco

    @property
    def imagem_url(self):
        if self.servico_id and self.servico.imagem:
            return self.servico.imagem.url
        return self.produto_imagem_url

    def __str__(self):
        return f"{self.usuario.username} - {self.nome}"