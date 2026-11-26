from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    path("dashboard/", views.dashboard, name="dashboard"),

    path("perfil/", views.perfil, name="perfil"),

    path("alterar-senha/", auth_views.PasswordChangeView.as_view(template_name="alterar_senha.html", success_url="/login/perfil/"), name="alterar_senha"),

    path("cadastro/", views.cadastro, name='cadastro'),

    # Recuperação de senha: usa o mecanismo nativo do Django (sem template_name
    # definido, por isso ele aproveita os templates padrão que já vêm prontos
    # dentro do django.contrib.admin).
    path("esqueci-senha/",
         auth_views.PasswordResetView.as_view(),
         name="password_reset"),
    path("esqueci-senha/enviado/",
         auth_views.PasswordResetDoneView.as_view(),
         name="password_reset_done"),
    path("resetar-senha/<uidb64>/<token>/",
         auth_views.PasswordResetConfirmView.as_view(),
         name="password_reset_confirm"),
    path("resetar-senha/concluido/",
         auth_views.PasswordResetCompleteView.as_view(),
         name="password_reset_complete"),
]
