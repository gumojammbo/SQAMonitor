"""Carga el proyecto SQA Monitor (datos de docs/). Uso, con el stack levantado:
docker compose exec -T web python manage.py shell < cargar_datos.py
"""
import json
import unicodedata
from datetime import date, datetime

from django.db import transaction
from django.utils import timezone

from apps.actividades.models import Actividad, Checklist, Criterio, Defecto
from apps.cuentas.models import Usuario
from apps.proyectos.models import Metrica, Proyecto, Sprint

DATOS = json.load(open("cargar_datos.json", encoding="utf-8"))
PASSWORD = "calidad2026"
SPRINTS = {1: ("Sprint 1", date(2026, 10, 21), date(2026, 11, 3)),
           2: ("Sprint 2", date(2026, 11, 4), date(2026, 11, 19))}
# medido con pytest, pytest-cov (sin tests ni migraciones) y flake8 el 2026-11-19
METRICAS_SPRINT2 = dict(cobertura=97.8, ejecutadas=75, aprobadas=75, flake8=0)


def correo(nombre):  # nombre.apellido sin acentos
    p = unicodedata.normalize("NFKD", nombre.lower()).encode("ascii", "ignore").decode().split()
    return f"{p[0]}.{p[-2] if len(p) > 2 else p[-1]}@example.com"


assert not Proyecto.objects.filter(nombre="SQA Monitor").exists(), "ya está cargado"
with transaction.atomic():
    usuarios = {}
    for nombre in DATOS["integrantes"]:
        usuarios[nombre] = Usuario.objects.create_user(correo(nombre), PASSWORD)
    proyecto = Proyecto.objects.create(nombre="SQA Monitor")
    proyecto.integrantes.set(usuarios.values())
    sprints = {n: Sprint.objects.create(proyecto=proyecto, nombre=s[0], inicio=s[1], fin=s[2])
               for n, s in SPRINTS.items()}
    Metrica.objects.create(sprint=sprints[2], **METRICAS_SPRINT2)

    for nombre, textos in DATOS["plantillas"].items():
        p = Checklist.objects.create(proyecto=proyecto, nombre=nombre)
        Criterio.objects.bulk_create([Criterio(checklist=p, texto=t) for t in textos])

    por_nombre = {}
    for a in DATOS["actividades"]:
        act = Actividad.objects.create(
            sprint=sprints[a["sprint"]], nombre=a["nombre"], dimension=a["dimension"],
            fecha=date.fromisoformat(a["fecha"]), hecha=a["hecha"],
            responsable=usuarios[a["responsable"]],
            revisor=usuarios[a["revisor"]] if a["revisor"] else None)
        # estado_revision no es editable ni se fija con save(): se escribe directo
        Actividad.objects.filter(pk=act.pk).update(estado_revision=a["estado"])
        por_nombre[a["nombre"]] = act
        if a["checklist"]:
            lista = Checklist.objects.create(
                proyecto=proyecto, nombre=a["checklist"], actividad=act)
            Criterio.objects.bulk_create([
                Criterio(checklist=lista, texto=t, valoracion="cumple" if ok else "no_cumple")
                for t, ok in a["criterios"]])

    for d in DATOS["defectos"]:
        act = por_nombre[d["actividad"]]
        defecto = Defecto.objects.create(actividad=act, descripcion=d["descripcion"],
                                         registrado_por=act.revisor)
        Defecto.objects.filter(pk=defecto.pk).update(  # fecha es auto_now_add
            fecha=timezone.make_aware(datetime.fromisoformat(d["fecha"])),
            estado="corregido" if d["corregido"] else "abierto")

print("OK:", Actividad.objects.count(), "actividades,", Defecto.objects.count(), "defectos,",
      Checklist.objects.count(), "checklists,", Usuario.objects.count(), "usuarios")
for u in Usuario.objects.all():
    print(u.correo)
