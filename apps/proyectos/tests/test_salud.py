import pytest
from django.urls import reverse

from apps.actividades.models import Actividad, Defecto
from apps.cuentas.models import Usuario
from apps.proyectos import salud
from apps.proyectos.models import Metrica


def test_puntaje_de_metricas():
    assert salud.puntaje_metrica("cobertura", 72, 80) == 90
    assert salud.puntaje_metrica("cobertura", 120, 80) == 100
    assert salud.puntaje_metrica("flake8", 3, None) == 40
    assert salud.puntaje_metrica("flake8", 9, None) == 0
    assert salud.puntaje_metrica("plan", None, 75) is None


@pytest.mark.parametrize("puntaje, etiqueta", [
    (100, "Aprobado"), (80, "Aprobado"), (79.9, "En riesgo"), (60, "En riesgo"),
    (59.9, "Bloqueado"), (0, "Bloqueado"), (None, "Sin dato"),
])
def test_semaforo(puntaje, etiqueta):
    assert salud.semaforo(puntaje)["etiqueta"] == etiqueta


def test_evaluar_ignora_lo_que_no_tiene_dato():
    r = salud.evaluar({"construccion": {"cobertura": 72, "pruebas": 100, "pasan": None,
                                        "flake8": 3, "plan": 75}})
    construccion = r["dimensiones"][2]
    assert construccion["puntaje"] == 82.5       # (90 + 100 + 40 + 100) / 4
    assert r["dimensiones"][0]["puntaje"] is None
    assert r["puntaje"] == 82.5 and r["semaforo"]["etiqueta"] == "Aprobado"


def test_evaluar_sin_datos():
    assert salud.evaluar({})["puntaje"] is None


@pytest.fixture
def datos(ana, beto, proyecto, sprint):
    proyecto.integrantes.add(beto)
    a1 = Actividad.objects.create(sprint=sprint, nombre="A1", dimension="especificacion",
                                  fecha="2026-01-10", responsable=ana, revisor=beto, hecha=True)
    Actividad.objects.filter(pk=a1.pk).update(estado_revision="aprobada")
    Actividad.objects.create(sprint=sprint, nombre="A2", dimension="especificacion",
                             fecha="2026-01-11", responsable=ana)
    Defecto.objects.create(actividad=a1, descripcion="x", registrado_por=ana, estado="corregido")
    Defecto.objects.create(actividad=a1, descripcion="y", registrado_por=ana)
    Metrica.objects.create(sprint=sprint, cobertura=80, ejecutadas=10, aprobadas=9, flake8=2)
    return sprint


def test_valores_de_un_sprint(datos):
    v = salud.valores_de(datos)
    assert v["especificacion"] == {"plan": 50, "revisados": 100, "pasan": 100, "defectos": 50}
    assert v["diseno"]["plan"] is None and v["diseno"]["defectos"] is None
    assert v["construccion"]["cobertura"] == 80 and v["construccion"]["pruebas"] == 90
    assert v["construccion"]["flake8"] == 2


def test_dimension_con_actividades_sin_defectos_vale_100(ana, proyecto, sprint):
    Actividad.objects.create(sprint=sprint, nombre="A", dimension="diseno",
                             fecha="2026-01-10", responsable=ana)
    assert salud.valores_de(sprint)["diseno"]["defectos"] == 100


def test_puntaje_del_proyecto_es_promedio_de_sprints(datos, proyecto):
    r = salud.reporte(proyecto)
    assert len(r["sprints"]) == 1 and r["puntaje"] == r["sprints"][0]["puntaje"]


def test_pantalla_y_pdf(client, ana, datos):
    client.force_login(ana)
    pk = datos.proyecto_id
    resp = client.get(reverse("proyectos:reporte", args=[pk]))
    assert "Reporte de salud" in resp.content.decode()
    resp = client.get(reverse("proyectos:reporte_pdf", args=[pk]))
    assert resp["Content-Type"] == "application/pdf" and resp.content.startswith(b"%PDF")


def test_pdf_con_nombre_fuera_de_latin1(client, ana, proyecto, sprint):
    proyecto.nombre = "Proyecto ✓ 日本"
    proyecto.save()
    client.force_login(ana)
    assert client.get(reverse("proyectos:reporte_pdf", args=[proyecto.pk])).status_code == 200


def test_reporte_vacio_no_falla(client, ana, proyecto):
    client.force_login(ana)
    assert client.get(reverse("proyectos:reporte", args=[proyecto.pk])).status_code == 200
    assert client.get(reverse("proyectos:reporte_pdf", args=[proyecto.pk])).status_code == 200


def test_no_integrante_recibe_404(client, proyecto):
    client.force_login(Usuario.objects.create_user("z@mail.com"))
    assert client.get(reverse("proyectos:reporte", args=[proyecto.pk])).status_code == 404
    assert client.get(reverse("proyectos:reporte_pdf", args=[proyecto.pk])).status_code == 404
