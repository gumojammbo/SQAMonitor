import pytest
from django.urls import reverse

from apps.actividades.models import Actividad, Defecto
from apps.cuentas.models import Usuario


@pytest.fixture
def act(ana, proyecto, sprint):
    return Actividad.objects.create(sprint=sprint, nombre="SRS", dimension="especificacion",
                                    fecha="2026-01-10", responsable=ana)


def url(act, nombre="defectos", *extra):
    return reverse(f"actividades:{nombre}", args=[act.sprint.proyecto_id, act.pk, *extra])


def test_integrante_registra_defecto(client, ana, act):
    client.force_login(ana)
    resp = client.post(url(act), {"descripcion": "Falta un requisito", "severidad": "alta"})
    d = Defecto.objects.get()
    assert resp.status_code == 302 and d.registrado_por == ana and d.estado == "abierto"


def test_severidad_invalida_se_rechaza(client, ana, act):
    client.force_login(ana)
    client.post(url(act), {"descripcion": "x", "severidad": "enorme"})
    assert not Defecto.objects.exists()


def test_no_integrante_recibe_404(client, act):
    client.force_login(Usuario.objects.create_user("z@mail.com"))
    assert client.get(url(act)).status_code == 404


def test_corregir_y_reabrir(client, ana, act):
    d = Defecto.objects.create(actividad=act, descripcion="x", registrado_por=ana)
    client.force_login(ana)
    client.post(url(act, "estado_defecto", d.pk))
    d.refresh_from_db()
    assert d.estado == "corregido"
    client.post(url(act, "estado_defecto", d.pk))
    d.refresh_from_db()
    assert d.estado == "abierto"


def test_editar_defecto(client, ana, act):
    d = Defecto.objects.create(actividad=act, descripcion="x", registrado_por=ana)
    client.force_login(ana)
    client.post(url(act, "editar_defecto", d.pk), {"descripcion": "y", "severidad": "baja"})
    d.refresh_from_db()
    assert (d.descripcion, d.severidad) == ("y", "baja")


def test_defecto_de_otra_actividad_da_404(client, ana, act, sprint):
    otra = Actividad.objects.create(sprint=sprint, nombre="Otra", dimension="diseno",
                                    fecha="2026-01-11", responsable=ana)
    d = Defecto.objects.create(actividad=otra, descripcion="x", registrado_por=ana)
    client.force_login(ana)
    assert client.post(url(act, "estado_defecto", d.pk)).status_code == 404


def test_detalle_muestra_conteo(client, ana, act):
    Defecto.objects.create(actividad=act, descripcion="x", registrado_por=ana)
    client.force_login(ana)
    resp = client.get(reverse("proyectos:detalle", args=[act.sprint.proyecto_id]))
    assert "Defectos (1 abiertos de 1)" in resp.content.decode()
