import pytest
from django.urls import reverse

from apps.actividades.models import Actividad
from apps.cuentas.models import Usuario


@pytest.fixture
def datos(ana, beto, proyecto, sprint):
    proyecto.integrantes.add(beto)
    return {"nombre": "Revisar SRS", "sprint": sprint.pk, "dimension": "especificacion",
            "fecha": "2026-01-10", "responsable": ana.pk}


def crear(client, proyecto, datos):
    return client.post(reverse("actividades:nueva", args=[proyecto.pk]), datos)


def test_crear_sin_revisor_queda_sin_revision(client, ana, proyecto, datos):
    client.force_login(ana)
    assert crear(client, proyecto, datos).status_code == 302
    assert Actividad.objects.get().estado_revision == "sin_revision"


def test_con_revisor_queda_pendiente(client, ana, beto, proyecto, datos):
    client.force_login(ana)
    crear(client, proyecto, {**datos, "revisor": beto.pk})
    assert Actividad.objects.get().estado_revision == "pendiente"


@pytest.mark.parametrize("cambio", [
    {"revisor": "ana"},         # revisor igual al responsable
    {"fecha": "2026-03-01"},    # fecha fuera del sprint
    {"responsable": "ajeno"},   # responsable que no es integrante
])
def test_rechaza_datos_invalidos(client, ana, proyecto, datos, cambio):
    ajeno = Usuario.objects.create_user("x@mail.com")
    ids = {"ana": ana.pk, "ajeno": ajeno.pk}
    client.force_login(ana)
    crear(client, proyecto, {**datos, **{k: ids.get(v, v) for k, v in cambio.items()}})
    assert not Actividad.objects.exists()


def test_editar_actividad(client, ana, proyecto, datos):
    client.force_login(ana)
    crear(client, proyecto, datos)
    a = Actividad.objects.get()
    client.post(reverse("actividades:editar", args=[proyecto.pk, a.pk]),
                {**datos, "nombre": "Otro", "hecha": "on"})
    a.refresh_from_db()
    assert a.nombre == "Otro" and a.hecha


def test_no_integrante_recibe_404(client, proyecto, datos):
    client.force_login(Usuario.objects.create_user("c@mail.com"))
    assert client.get(reverse("actividades:nueva", args=[proyecto.pk])).status_code == 404


def test_detalle_muestra_la_actividad(client, ana, proyecto, datos):
    client.force_login(ana)
    crear(client, proyecto, datos)
    resp = client.get(reverse("proyectos:detalle", args=[proyecto.pk]))
    assert "Revisar SRS" in resp.content.decode()


@pytest.mark.parametrize("campo", ["responsable", "revisor"])
def test_no_se_quita_integrante_con_actividades(client, ana, beto, proyecto, datos, campo):
    client.force_login(ana)
    crear(client, proyecto, {**datos, "responsable": ana.pk, "revisor": beto.pk}
          if campo == "revisor" else {**datos, "responsable": beto.pk})
    resp = client.post(reverse("proyectos:quitar_integrante", args=[proyecto.pk, beto.pk]))
    assert resp.status_code == 302 and proyecto.integrantes.filter(pk=beto.pk).exists()
