import pytest
from django.urls import reverse

from apps.actividades.models import Actividad, Checklist, Criterio, Defecto
from apps.cuentas.models import Usuario
from apps.proyectos.models import Proyecto, Sprint


@pytest.fixture
def act(ana, beto, proyecto, sprint):
    proyecto.integrantes.add(beto)
    a = Actividad.objects.create(sprint=sprint, nombre="A", dimension="especificacion",
                                 fecha="2026-01-10", responsable=ana, revisor=beto)
    lista = Checklist.objects.create(proyecto=proyecto, nombre="C", actividad=a)
    Criterio.objects.create(checklist=lista, texto="x")
    Defecto.objects.create(actividad=a, descripcion="d", registrado_por=ana)
    return a


def url(act):
    return reverse("actividades:eliminar", args=[act.sprint.proyecto_id, act.pk])


def test_elimina_actividad_con_checklist_y_defectos(client, ana, act):
    client.force_login(ana)
    assert client.post(url(act)).status_code == 302
    assert not (Actividad.objects.exists() or Checklist.objects.exists()
                or Criterio.objects.exists() or Defecto.objects.exists())


def test_no_elimina_con_get(client, ana, act):
    client.force_login(ana)
    assert client.get(url(act)).status_code == 405
    assert Actividad.objects.exists()


def test_no_integrante_recibe_404(client, act):
    client.force_login(Usuario.objects.create_user("z@mail.com"))
    assert client.post(url(act)).status_code == 404
    assert Actividad.objects.exists()


def test_no_elimina_actividad_de_otro_proyecto(client, ana, act):
    otro = Proyecto.objects.create(nombre="Otro")
    otro.integrantes.add(ana)
    ajena = Sprint.objects.create(proyecto=otro, nombre="S", inicio="2026-01-01", fin="2026-01-31")
    a2 = Actividad.objects.create(sprint=ajena, nombre="B", dimension="diseno",
                                  fecha="2026-01-05", responsable=ana)
    client.force_login(ana)
    resp = client.post(reverse("actividades:eliminar", args=[act.sprint.proyecto_id, a2.pk]))
    assert resp.status_code == 404 and Actividad.objects.filter(pk=a2.pk).exists()
