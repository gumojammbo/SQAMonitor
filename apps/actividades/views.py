from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.proyectos.views import proyecto_de

from .forms import (ActividadForm, ChecklistForm, CriterioForm, CriterioFormSet, DefectoForm,
                    PlantillaForm)
from .models import Actividad, Checklist, Criterio, Defecto


# crea o edita una actividad del proyecto
def formulario(request, pk, actividad_id=None):
    proyecto = proyecto_de(request, pk)
    actividad = None
    if actividad_id:
        actividad = get_object_or_404(Actividad, pk=actividad_id, sprint__proyecto=proyecto)
    form = ActividadForm(request.POST or None, instance=actividad, proyecto=proyecto)
    if form.is_valid():
        form.save()
        return redirect("proyectos:detalle", pk)
    return render(request, "form.html", {
        "form": form,
        "titulo": "Editar actividad" if actividad else "Nueva actividad",
        "volver": reverse("proyectos:detalle", args=[pk]),
    })


# elimina la actividad junto con su checklist y sus defectos (cascada)
@require_POST
def eliminar(request, pk, actividad_id):
    proyecto = proyecto_de(request, pk)
    get_object_or_404(Actividad, pk=actividad_id, sprint__proyecto=proyecto).delete()
    return redirect("proyectos:detalle", pk)


# busca una actividad con revisor del proyecto (si no hay revisor no hay checklist)
def con_checklist(request, pk, actividad_id):
    proyecto = proyecto_de(request, pk)
    return get_object_or_404(Actividad, pk=actividad_id, sprint__proyecto=proyecto,
                             revisor__isnull=False)


# solo el revisor asignado edita, y solo mientras la revision esta pendiente
def puede_editar(usuario, actividad):
    return usuario == actividad.revisor and actividad.estado_revision == "pendiente"


# muestra el checklist; el revisor lo valora y lo cierra con aprobada o rechazada
def checklist(request, pk, actividad_id):
    actividad = con_checklist(request, pk, actividad_id)
    lista = Checklist.objects.filter(actividad=actividad).first()
    editable = bool(lista) and puede_editar(request.user, actividad)
    formset = None
    if request.method == "POST":
        if not editable:
            raise PermissionDenied
        formset = CriterioFormSet(request.POST, queryset=lista.criterios.all())
        if formset.is_valid():
            formset.save()
            resultado = request.POST.get("cerrar")
            if resultado in ("aprobada", "rechazada"):
                if not lista.criterios.exists() or lista.criterios.filter(valoracion="").exists():
                    messages.error(request, "Para cerrar hay que valorar todos los criterios.")
                else:
                    actividad.estado_revision = resultado
                    actividad.save()
            return redirect("actividades:checklist", pk, actividad_id)
    elif editable:
        formset = CriterioFormSet(queryset=lista.criterios.all())
    return render(request, "actividades/checklist.html", {
        "actividad": actividad, "pk": pk, "lista": lista, "formset": formset,
        "form": CriterioForm() if lista else ChecklistForm(proyecto=actividad.sprint.proyecto),
        "editable": puede_editar(request.user, actividad),
    })


# el revisor crea el checklist de la actividad (uno solo)
@require_POST
def crear_checklist(request, pk, actividad_id):
    actividad = con_checklist(request, pk, actividad_id)
    if not puede_editar(request.user, actividad):
        raise PermissionDenied
    form = ChecklistForm(request.POST, proyecto=actividad.sprint.proyecto)
    if form.is_valid() and not Checklist.objects.filter(actividad=actividad).exists():
        form.instance.actividad = actividad
        form.instance.proyecto = actividad.sprint.proyecto
        lista = form.save()
        plantilla = form.cleaned_data["plantilla"]
        if plantilla:  # copia los criterios sin valoracion
            Criterio.objects.bulk_create(
                [Criterio(checklist=lista, texto=c.texto) for c in plantilla.criterios.all()])
    return redirect("actividades:checklist", pk, actividad_id)


@require_POST
def nuevo_criterio(request, pk, actividad_id):
    actividad = con_checklist(request, pk, actividad_id)
    if not puede_editar(request.user, actividad):
        raise PermissionDenied
    form = CriterioForm(request.POST)
    if form.is_valid():
        form.instance.checklist = get_object_or_404(Checklist, actividad=actividad)
        form.save()
    return redirect("actividades:checklist", pk, actividad_id)


# lista los defectos de una actividad y registra uno nuevo
def defectos(request, pk, actividad_id):
    proyecto = proyecto_de(request, pk)
    actividad = get_object_or_404(Actividad, pk=actividad_id, sprint__proyecto=proyecto)
    form = DefectoForm(request.POST or None)
    if form.is_valid():
        form.instance.actividad = actividad
        form.instance.registrado_por = request.user
        form.save()
        return redirect("actividades:defectos", pk, actividad_id)
    return render(request, "actividades/defectos.html",
                  {"actividad": actividad, "pk": pk, "form": form})


# busca un defecto de una actividad del proyecto
def buscar_defecto(request, pk, actividad_id, defecto_id):
    proyecto = proyecto_de(request, pk)
    return get_object_or_404(Defecto, pk=defecto_id, actividad_id=actividad_id,
                             actividad__sprint__proyecto=proyecto)


def editar_defecto(request, pk, actividad_id, defecto_id):
    defecto = buscar_defecto(request, pk, actividad_id, defecto_id)
    form = DefectoForm(request.POST or None, instance=defecto)
    if form.is_valid():
        form.save()
        return redirect("actividades:defectos", pk, actividad_id)
    return render(request, "form.html", {
        "form": form, "titulo": "Editar defecto",
        "volver": reverse("actividades:defectos", args=[pk, actividad_id]),
    })


# alterna el defecto entre abierto y corregido
@require_POST
def cambiar_estado_defecto(request, pk, actividad_id, defecto_id):
    defecto = buscar_defecto(request, pk, actividad_id, defecto_id)
    defecto.estado = "abierto" if defecto.estado == "corregido" else "corregido"
    defecto.save()
    return redirect("actividades:defectos", pk, actividad_id)


# busca una plantilla (checklist sin actividad) del proyecto
def buscar_plantilla(request, pk, plantilla_id):
    proyecto = proyecto_de(request, pk)
    return get_object_or_404(Checklist, pk=plantilla_id, proyecto=proyecto,
                             actividad__isnull=True)


# lista las plantillas del proyecto y crea una nueva
def plantillas(request, pk):
    proyecto = proyecto_de(request, pk)
    form = PlantillaForm(request.POST or None)
    if form.is_valid():
        form.instance.proyecto = proyecto
        return redirect("plantillas:detalle", pk, form.save().pk)
    return render(request, "actividades/plantillas.html", {
        "proyecto": proyecto, "form": form,
        "plantillas": proyecto.checklists.filter(actividad__isnull=True),
    })


# muestra una plantilla y agrega criterios
def plantilla(request, pk, plantilla_id):
    lista = buscar_plantilla(request, pk, plantilla_id)
    form = CriterioForm(request.POST or None)
    if form.is_valid():
        form.instance.checklist = lista
        form.save()
        return redirect("plantillas:detalle", pk, plantilla_id)
    return render(request, "actividades/plantilla.html", {"lista": lista, "pk": pk, "form": form})


@require_POST
def quitar_criterio(request, pk, plantilla_id, criterio_id):
    lista = buscar_plantilla(request, pk, plantilla_id)
    get_object_or_404(lista.criterios, pk=criterio_id).delete()
    return redirect("plantillas:detalle", pk, plantilla_id)


@require_POST
def borrar_plantilla(request, pk, plantilla_id):
    buscar_plantilla(request, pk, plantilla_id).delete()
    return redirect("plantillas:lista", pk)
