from django.db import migrations


def criar_tabela_contato(apps, schema_editor):
    Contato = apps.get_model("app", "Contato")
    tabelas = schema_editor.connection.introspection.table_names()
    if Contato._meta.db_table not in tabelas:
        schema_editor.create_model(Contato)


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0006_pedido_origem_pedido_produto_imagem_url_and_more"),
    ]

    operations = [
        migrations.RunPython(criar_tabela_contato, migrations.RunPython.noop),
    ]
