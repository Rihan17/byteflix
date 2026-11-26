# ByteFix — Assistência Técnica (Projeto Django — WEB III)

Projeto desenvolvido em Django para a disciplina de Desenvolvimento Web 3, a
partir da base já existente do aluno, completando os requisitos do enunciado
"WEB III – Projeto Django".

Tema escolhido: **Assistência Técnica** (loja/serviços de informática e celulares).

## Como rodar o projeto

```bash
cd django
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Acesse http://127.0.0.1:8000/

O arquivo `.env` já contém as credenciais do Supabase usadas pelo projeto
original (tabela `integrantes`, usada em "Quem Somos" e em "Equipe").

## Usuários já existentes no banco (db.sqlite3)

| Usuário | Perfil |
|---|---|
| admin | administrador (vai direto para `/admin/`) |
| yohan | cliente (vai para a Dashboard) |
| fatec, matheus, pedro | sem perfil definido ainda (o sistema trata isso automaticamente e considera "cliente" na primeira vez que fizerem login) |

Se não souber as senhas, crie um novo usuário em "Cadastrar Usuário" na tela
de login, ou rode `python manage.py changepassword <usuario>`.

Para testar como administrador sem usar a conta `admin` existente:
```bash
python manage.py createsuperuser
```
e depois, no shell (`python manage.py shell`):
```python
from django.contrib.auth.models import User
from login.models import Perfil
u = User.objects.get(username="SEU_USUARIO")
Perfil.objects.create(usuario=u, tipo_usuario="administrador")
```

## O que foi implementado a partir da base

- **Home**: página institucional com tema visual próprio (ByteFix).
- **Quem Somos** *(nova)*: texto institucional + equipe vinda do Supabase (banco remoto).
- **Produtos**: corrigido um bug que impedia a página de abrir; agora mostra
  os serviços/produtos do banco local e os produtos de uma API externa
  (FakeStore API), **ambos com botão "Adicionar ao carrinho"**, visível só
  para quem está logado.
- **Carrinho** *(novo)*: os produtos vão primeiro para um carrinho (guardado
  na sessão do usuário), mostrado no menu com a quantidade de itens. Na
  página do carrinho dá pra ver cada item, o subtotal, remover itens e só
  então "Finalizar Compra". Nesse momento, os preços dos produtos da API são
  conferidos de novo direto na API (evita preço desatualizado/adulterado) e
  cada item vira um registro em Meus Pedidos.
- **Meus Pedidos** *(novo)*: lista os itens que o cliente logado já comprou
  (tanto os locais quanto os da API, com uma etiqueta indicando a origem de
  cada um), com total da compra.
- **Contato**: formulário público (sem login) + página de gestão das
  mensagens recebidas (dentro da Dashboard, só para logados).
- **Entrar / Cadastro / Recuperar senha**: login, cadastro de novo usuário e
  **recuperação de senha nativa do Django** (link "Esqueceu sua senha?" na
  tela de login — em desenvolvimento, o e-mail aparece no console onde o
  `runserver` está rodando).
- **Redirecionamento por perfil**: administrador vai direto para o admin do
  Django; cliente vai para a Dashboard.
- **Dashboard**: menu com "Dashboard" e "Sair", e cards para Editar Perfil,
  Contatos, Serviços, Equipe, Meus Pedidos e Relatórios.
- **Serviços**: CRUD completo (cadastrar, listar com filtros/estatísticas,
  editar, excluir), agora protegido por login.
- **Equipe**: CRUD completo no Supabase — adicionado o que faltava (**editar**
  integrante); cadastro/edição/exclusão protegidos por login.
- **Relatórios**: gráficos (Chart.js) e estatísticas dos serviços cadastrados.
- Páginas de gestão (Serviços, Contatos, Equipe, Relatórios) agora exigem
  login, e o visual de todas as páginas foi padronizado com o tema ByteFix.

## Observações

- As chamadas ao Supabase e à API externa (FakeStore) são protegidas com
  tratamento de erro: se a internet ou o serviço estiver fora do ar, a página
  continua funcionando e mostra um aviso, em vez de quebrar.
- Os dados de exemplo de Categoria/Serviço foram atualizados para refletir o
  tema de assistência técnica (ex.: "Troca de Tela de Notebook", "Upgrade de
  Memória RAM").

## Deploy no Render

Arquivos já preparados: `build.sh`, `requirements.txt` (com gunicorn, whitenoise,
dj-database-url e psycopg2-binary), `.gitignore`, `.gitattributes` e `.env.example`.
O `settings.py` funciona nos dois ambientes: localmente continua igual; no Render
(que define a variável `RENDER` sozinho) ele desliga o DEBUG e lê as variáveis de ambiente.

1. Suba o projeto para o GitHub (o `.env` fica de fora pelo `.gitignore`).
2. No Render: **New → Web Service**, conecte o repositório.
3. **Build Command:** `bash build.sh`
4. **Start Command:** `gunicorn projeto.wsgi:application`
5. Em **Environment**, crie: `SECRET_KEY` (texto longo e aleatório), `SUPABASE_URL`, `SUPABASE_KEY`.
   (Opcional: `DATABASE_URL` do PostgreSQL do Render; sem ela o projeto usa SQLite.)
6. Depois do deploy, no **Shell** do Render: `python manage.py createsuperuser`.

Limitações: o disco do Render é temporário — com SQLite, usuários, pedidos e imagens
enviadas (`media/`) são perdidos a cada novo deploy/reinício; imagens enviadas também
não são servidas com DEBUG desligado. O e-mail de recuperação de senha só aparece nos logs.
