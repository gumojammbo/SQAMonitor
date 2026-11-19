import pytest
from django.urls import reverse

from apps.cuentas.models import Usuario

pytestmark = pytest.mark.django_db
CLAVE = "clave-segura-123"


def test_sin_sesion_redirige_al_login(client):
    resp = client.get("/")
    assert resp.status_code == 302 and reverse("cuentas:login") in resp["Location"]


def test_registro_guarda_correo_en_minusculas_e_inicia_sesion(client):
    datos = {"correo": "Ana@Mail.com", "password1": CLAVE, "password2": CLAVE}
    assert client.post(reverse("cuentas:registro"), datos).status_code == 302
    assert Usuario.objects.filter(correo="ana@mail.com").exists()
    assert client.get("/").status_code == 200


def test_login_y_logout(client):
    Usuario.objects.create_user("ana@mail.com", CLAVE)
    resp = client.post(reverse("cuentas:login"), {"username": "ana@mail.com", "password": CLAVE})
    assert resp.status_code == 302 and client.get("/").status_code == 200
    client.post(reverse("cuentas:logout"))
    assert client.get("/").status_code == 302
