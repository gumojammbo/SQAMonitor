import pytest
from django.urls import reverse

from apps.proyectos.models import Proyecto


def test_crear_proyecto_deja_al_creador_como_integrante(client, ana):
    client.force_login(ana)
    resp = client.post(reverse("proyectos:nuevo"), {"nombre": "Nuevo"})
    assert resp.status_code == 302
    assert Proyecto.objects.get(nombre="Nuevo").integrantes.filter(pk=ana.pk).exists()


def test_lista_solo_muestra_proyectos_propios(client, ana, beto, proyecto):
    client.force_login(beto)
    assert "Demo" not in client.get("/").content.decode()
    client.force_login(ana)
    assert "Demo" in client.get("/").content.decode()


def test_no_integrante_recibe_404(client, beto, proyecto):
    client.force_login(beto)
    assert client.get(reverse("proyectos:detalle", args=[proyecto.pk])).status_code == 404
    resp = client.post(reverse("proyectos:nuevo_sprint", args=[proyecto.pk]), {})
    assert resp.status_code == 404


def test_agregar_integrante_por_correo(client, ana, beto, proyecto):
    client.force_login(ana)
    url = reverse("proyectos:agregar_integrante", args=[proyecto.pk])
    client.post(url, {"correo": "BETO@mail.com"})
    assert proyecto.integrantes.filter(pk=beto.pk).exists()


@pytest.mark.parametrize("correo", ["nadie@mail.com", "ana@mail.com"])
def test_rechaza_correo_inexistente_o_repetido(client, ana, proyecto, correo):
    client.force_login(ana)
    client.post(reverse("proyectos:agregar_integrante", args=[proyecto.pk]), {"correo": correo})
    assert proyecto.integrantes.count() == 1


def test_quitar_integrante_pero_no_a_uno_mismo(client, ana, beto, proyecto):
    proyecto.integrantes.add(beto)
    client.force_login(ana)
    client.post(reverse("proyectos:quitar_integrante", args=[proyecto.pk, beto.pk]))
    assert not proyecto.integrantes.filter(pk=beto.pk).exists()
    client.post(reverse("proyectos:quitar_integrante", args=[proyecto.pk, ana.pk]))
    assert proyecto.integrantes.filter(pk=ana.pk).exists()


def test_crear_sprint_y_validar_fechas(client, ana, proyecto):
    client.force_login(ana)
    url = reverse("proyectos:nuevo_sprint", args=[proyecto.pk])
    client.post(url, {"nombre": "S1", "inicio": "2026-01-01", "fin": "2026-01-14"})
    client.post(url, {"nombre": "S2", "inicio": "2026-02-10", "fin": "2026-02-01"})
    assert list(proyecto.sprints.values_list("nombre", flat=True)) == ["S1"]
