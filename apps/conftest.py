import pytest

from apps.cuentas.models import Usuario
from apps.proyectos.models import Proyecto, Sprint


@pytest.fixture
def ana(db):
    return Usuario.objects.create_user("ana@mail.com", "clave-segura-123")


@pytest.fixture
def beto(db):
    return Usuario.objects.create_user("beto@mail.com", "clave-segura-123")


@pytest.fixture
def proyecto(ana):
    # proyecto con ana como unica integrante
    p = Proyecto.objects.create(nombre="Demo")
    p.integrantes.add(ana)
    return p


@pytest.fixture
def sprint(proyecto):
    # sprint de enero de 2026 dentro del proyecto
    return Sprint.objects.create(proyecto=proyecto, nombre="S1", inicio="2026-01-01",
                                 fin="2026-01-31")
