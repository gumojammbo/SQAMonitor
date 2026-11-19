import pytest
from django.urls import reverse

from apps.cuentas.models import Usuario
from apps.proyectos.models import Metrica

DATOS = {"cobertura": "82.5", "ejecutadas": 40, "aprobadas": 38, "flake8": 3}


def url(sprint):
    return reverse("proyectos:metricas", args=[sprint.proyecto_id, sprint.pk])


def test_capturar_y_corregir_usa_un_solo_registro(client, ana, sprint):
    client.force_login(ana)
    assert client.post(url(sprint), DATOS).status_code == 302
    client.post(url(sprint), {**DATOS, "flake8": 0})
    m = Metrica.objects.get()
    assert m.sprint == sprint and m.flake8 == 0 and m.cobertura == 82.5


@pytest.mark.parametrize("cambio", [
    {"cobertura": 120},
    {"cobertura": -1},
    {"aprobadas": 41},    # mas aprobadas que ejecutadas
    {"flake8": -2},
])
def test_rechaza_valores_invalidos(client, ana, sprint, cambio):
    client.force_login(ana)
    client.post(url(sprint), {**DATOS, **cambio})
    assert not Metrica.objects.exists()


def test_porcentaje_de_pruebas_aprobadas(sprint):
    assert Metrica(sprint=sprint, cobertura=0, ejecutadas=40, aprobadas=30,
                   flake8=0).pct_aprobadas() == 75
    assert Metrica(sprint=sprint, cobertura=0, ejecutadas=0, aprobadas=0,
                   flake8=0).pct_aprobadas() is None


def test_no_integrante_recibe_404(client, sprint):
    client.force_login(Usuario.objects.create_user("z@mail.com"))
    assert client.get(url(sprint)).status_code == 404


def test_detalle_muestra_metricas(client, ana, sprint):
    Metrica.objects.create(sprint=sprint, **{**DATOS, "cobertura": 82.5})
    client.force_login(ana)
    html = client.get(reverse("proyectos:detalle", args=[sprint.proyecto_id])).content.decode()
    assert "82,5%" in html and "38/40" in html
