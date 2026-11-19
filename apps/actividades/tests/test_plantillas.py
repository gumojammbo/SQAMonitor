import pytest
from django.urls import reverse

from apps.actividades.models import Actividad, Checklist, Criterio
from apps.cuentas.models import Usuario
from apps.proyectos.models import Proyecto


def plantilla_url(proyecto, nombre="lista", *extra):
    return reverse(f"plantillas:{nombre}", args=[proyecto.pk, *extra])


@pytest.fixture
def plantilla(proyecto):
    p = Checklist.objects.create(proyecto=proyecto, nombre="SRS")
    Criterio.objects.create(checklist=p, texto="Es claro")
    Criterio.objects.create(checklist=p, texto="Es completo")
    return p


@pytest.fixture
def act(ana, beto, proyecto, sprint):
    proyecto.integrantes.add(beto)
    return Actividad.objects.create(sprint=sprint, nombre="A", dimension="especificacion",
                                    fecha="2026-01-10", responsable=ana, revisor=beto)


def test_crear_plantilla_sin_actividad(client, ana, proyecto):
    client.force_login(ana)
    resp = client.post(plantilla_url(proyecto), {"nombre": "Diseño"})
    p = Checklist.objects.get()
    assert resp.status_code == 302 and p.actividad is None and p.proyecto == proyecto


def test_lista_solo_muestra_plantillas(client, ana, proyecto, plantilla, act):
    Checklist.objects.create(proyecto=proyecto, nombre="De actividad", actividad=act)
    client.force_login(ana)
    html = client.get(plantilla_url(proyecto)).content.decode()
    assert "SRS" in html and "De actividad" not in html


def test_agregar_y_quitar_criterio(client, ana, proyecto, plantilla):
    client.force_login(ana)
    client.post(plantilla_url(proyecto, "detalle", plantilla.pk), {"texto": "Es verificable"})
    assert plantilla.criterios.count() == 3
    c = plantilla.criterios.first()
    client.post(plantilla_url(proyecto, "quitar_criterio", plantilla.pk, c.pk))
    assert plantilla.criterios.count() == 2


def test_borrar_plantilla(client, ana, proyecto, plantilla):
    client.force_login(ana)
    client.post(plantilla_url(proyecto, "borrar", plantilla.pk))
    assert not Checklist.objects.exists() and not Criterio.objects.exists()


def test_no_integrante_recibe_404(client, proyecto, plantilla):
    client.force_login(Usuario.objects.create_user("z@mail.com"))
    assert client.get(plantilla_url(proyecto)).status_code == 404
    assert client.get(plantilla_url(proyecto, "detalle", plantilla.pk)).status_code == 404


def test_checklist_de_actividad_no_es_plantilla(client, ana, proyecto, act):
    lista = Checklist.objects.create(proyecto=proyecto, nombre="X", actividad=act)
    client.force_login(ana)
    assert client.get(plantilla_url(proyecto, "detalle", lista.pk)).status_code == 404
    assert client.post(plantilla_url(proyecto, "borrar", lista.pk)).status_code == 404


def crear_checklist(client, act, **datos):
    url = reverse("actividades:crear_checklist", args=[act.sprint.proyecto_id, act.pk])
    return client.post(url, {"nombre": "Revision", **datos})


def test_usar_plantilla_copia_criterios_sin_valorar(client, beto, act, plantilla):
    client.force_login(beto)
    crear_checklist(client, act, plantilla=plantilla.pk)
    lista = Checklist.objects.get(actividad=act)
    assert list(lista.criterios.values_list("texto", "valoracion")) == [
        ("Es claro", ""), ("Es completo", "")]
    plantilla.delete()   # borrar la plantilla no toca el checklist creado
    assert lista.criterios.count() == 2


def test_sin_plantilla_queda_vacio(client, beto, act, plantilla):
    client.force_login(beto)
    crear_checklist(client, act)
    assert Checklist.objects.get(actividad=act).criterios.count() == 0


def test_no_acepta_plantilla_de_otro_proyecto(client, beto, act):
    otro = Proyecto.objects.create(nombre="Otro")
    ajena = Checklist.objects.create(proyecto=otro, nombre="Ajena")
    client.force_login(beto)
    crear_checklist(client, act, plantilla=ajena.pk)
    assert not Checklist.objects.filter(actividad=act).exists()
