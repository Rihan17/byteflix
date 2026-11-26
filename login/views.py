from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# form do usuario
from django.contrib.auth.forms import UserCreationForm
from .forms import CadastroForm
from .models import Perfil


@login_required
def dashboard(request):
    perfil, _ = Perfil.objects.get_or_create(
        usuario=request.user,
        defaults={
            'tipo_usuario': 'administrador' if request.user.is_superuser else 'cliente'
        }
    )

    if perfil.tipo_usuario == 'administrador' or request.user.is_superuser:
        return redirect("/admin/")

    return render(request, "dashboard.html", {"perfil": perfil})


@login_required
def perfil(request):

    if request.method == "POST":
        usuario = request.user

        usuario.first_name = request.POST.get("nome")
        usuario.last_name = request.POST.get("sobrenome")
        usuario.email = request.POST.get("email")

        usuario.save()

        messages.success(request, "Perfil atualizado com sucesso!")
        return redirect("perfil")

    return render(request, "perfil.html")


def cadastro(request):
    if request.method == 'POST':
        form = CadastroForm(request.POST)

        if form.is_valid():
            usuario = form.save()
            Perfil.objects.create(usuario=usuario, tipo_usuario='cliente')
            messages.success(request, "Conta criada com sucesso! Faça login para continuar.")
            return redirect('login')
    else:
        form = CadastroForm()

    return render(request, 'cadastro.html', {'form': form})
