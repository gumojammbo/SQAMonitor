from django.contrib.auth import views
from django.urls import path

from . import views as vistas

app_name = "cuentas"
urlpatterns = [
    path("login/", views.LoginView.as_view(template_name="cuentas/login.html"), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("registro/", vistas.registro, name="registro"),
]
