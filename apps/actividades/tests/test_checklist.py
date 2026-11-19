import pytest
from django.urls import reverse

from apps.actividades.models import Actividad, Checklist, Criterio


@pytest.fixture
def act(ana, beto, proyecto, sprint):
    # actividad de ana revisada por beto, con dos criterios
    proyecto.integrantes.add(beto)
    a = Actividad.objects.create(sprint=sprint, nombre="SRS", dimension="especificacion",
                                 fecha="2026-01-10", responsable=ana, revisor=beto)
    lista = Checklist.objects.create(proyecto=proyecto, nombre="SRS", actividad=a)
    Criterio.objects.create(checklist=lista, texto="Es claro")
    Criterio.objects.create(checklist=lista, texto="Es completo")
    return a


def url(act, nombre="checklist"):
    return reverse(f"actividades:{nombre}", args=[act.sprint.proyecto_id, act.pk])


def valorar(client, act, valores, cerrar=None):
    # envia el formset con una valoracion por criterio
    datos = {"form-TOTAL_FORMS": len(valores), "form-INITIAL_FORMS": len(valores)}
    for i, (c, v) in enumerate(zip(act.checklist.criterios.all(), valores)):
        datos |= {f"form-{i}-id": c.pk, f"form-{i}-valoracion": v, f"form-{i}-observacion": ""}
    if cerrar:
        datos["cerrar"] = cerrar
    return client.post(url(act), datos)


def test_revisor_valora_y_cierra(client, beto, act):
    client.force_login(beto)
    valorar(client, act, ["cumple", "no_aplica"], cerrar="aprobada")
    act.refresh_from_db()
    assert act.estado_revision == "aprobada"
    valores = act.checklist.criterios.values_list("valoracion", flat=True)
    assert list(valores) == ["cumple", "no_aplica"]


def test_cerrar_rechazada(client, beto, act):
    client.force_login(beto)
    valorar(client, act, ["cumple", "no_cumple"], cerrar="rechazada")
    act.refresh_from_db()
    assert act.estado_revision == "rechazada"


def test_no_cierra_con_criterios_sin_valorar(client, beto, act):
    client.force_login(beto)
    valorar(client, act, ["cumple", ""], cerrar="aprobada")
    act.refresh_from_db()
    assert act.estado_revision == "pendiente"


def test_no_cierra_sin_criterios(client, beto, act):
    act.checklist.criterios.all().delete()
    client.force_login(beto)
    client.post(url(act), {"form-TOTAL_FORMS": 0, "form-INITIAL_FORMS": 0, "cerrar": "aprobada"})
    act.refresh_from_db()
    assert act.estado_revision == "pendiente"


def test_cerrado_ya_no_se_edita(client, beto, act):
    client.force_login(beto)
    valorar(client, act, ["cumple", "cumple"], cerrar="aprobada")
    assert valorar(client, act, ["no_cumple", "no_cumple"]).status_code == 403
    assert client.post(url(act, "nuevo_criterio"), {"texto": "x"}).status_code == 403


def test_solo_el_revisor_edita(client, ana, act):
    client.force_login(ana)
    assert client.get(url(act)).status_code == 200
    assert valorar(client, act, ["cumple", "cumple"]).status_code == 403
    assert client.post(url(act, "nuevo_criterio"), {"texto": "x"}).status_code == 403


def test_agregar_criterio(client, beto, act):
    client.force_login(beto)
    client.post(url(act, "nuevo_criterio"), {"texto": "Es verificable"})
    assert act.checklist.criterios.count() == 3


def test_sin_revisor_no_hay_checklist(client, ana, act):
    act.revisor = None
    act.save()
    client.force_login(ana)
    assert client.get(url(act)).status_code == 404


def test_revisor_crea_checklist_una_sola_vez(client, ana, beto, act):
    act.checklist.delete()
    act = Actividad.objects.get(pk=act.pk)
    client.force_login(ana)
    assert client.post(url(act, "crear_checklist"), {"nombre": "X"}).status_code == 403
    client.force_login(beto)
    client.post(url(act, "crear_checklist"), {"nombre": "SRS"})
    client.post(url(act, "crear_checklist"), {"nombre": "Otro"})
    lista = Checklist.objects.get()
    assert lista.actividad == act and lista.proyecto == act.sprint.proyecto
    assert lista.nombre == "SRS"
