from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from . import pdf, salud
from .forms import IntegranteForm, MetricaForm, ProyectoForm, SprintForm


# devuelve el proyecto solo si el usuario es integrante (si no, 404)
def proyecto_de(request, pk):
    return get_object_or_404(request.user.proyectos, pk=pk)


# muestra los errores de un formulario como mensajes
def avisar(request, form):
    for errores in form.errors.values():
        for error in errores:
            messages.error(request, error)


def lista(request):
    return render(request, "proyectos/lista.html", {"proyectos": request.user.proyectos.all()})


def nuevo(request):
    # crea el proyecto y deja al creador como integrante
    form = ProyectoForm(request.POST or None)
    if form.is_valid():
        proyecto = form.save()
        proyecto.integrantes.add(request.user)
        return redirect("proyectos:detalle", proyecto.pk)
    return render(request, "form.html", {"form": form, "titulo": "Nuevo proyecto"})


def detalle(request, pk):
    proyecto = proyecto_de(request, pk)
    return render(request, "proyectos/detalle.html", {
        "proyecto": proyecto,
        "form_integrante": IntegranteForm(proyecto=proyecto),
        "form_sprint": SprintForm(),
    })


@require_POST
def agregar_integrante(request, pk):
    proyecto = proyecto_de(request, pk)
    form = IntegranteForm(request.POST, proyecto=proyecto)
    if form.is_valid():
        proyecto.integrantes.add(form.usuario)
    else:
        avisar(request, form)
    return redirect("proyectos:detalle", pk)


@require_POST
def quitar_integrante(request, pk, usuario_id):
    proyecto = proyecto_de(request, pk)
    if usuario_id == request.user.pk:
        messages.error(request, "No puedes quitarte a ti mismo del proyecto.")
    elif proyecto.sprints.filter(Q(actividades__responsable_id=usuario_id)
                                 | Q(actividades__revisor_id=usuario_id)).exists():
        messages.error(request, "Ese integrante tiene actividades asignadas; reasígnalas primero.")
    else:
        proyecto.integrantes.remove(usuario_id)
    return redirect("proyectos:detalle", pk)


@require_POST
def nuevo_sprint(request, pk):
    proyecto = proyecto_de(request, pk)
    form = SprintForm(request.POST)
    if form.is_valid():
        sprint = form.save(commit=False)
        sprint.proyecto = proyecto
        sprint.save()
    else:
        avisar(request, form)
    return redirect("proyectos:detalle", pk)


# captura o corrige las metricas de un sprint
def metricas(request, pk, sprint_id):
    proyecto = proyecto_de(request, pk)
    sprint = get_object_or_404(proyecto.sprints, pk=sprint_id)
    form = MetricaForm(request.POST or None, instance=getattr(sprint, "metrica", None))
    if form.is_valid():
        form.instance.sprint = sprint
        form.save()
        return redirect("proyectos:detalle", pk)
    return render(request, "form.html", {
        "form": form, "titulo": f"Métricas: {sprint.nombre}",
        "volver": reverse("proyectos:detalle", args=[pk]),
    })


def reporte(request, pk):
    proyecto = proyecto_de(request, pk)
    return render(request, "proyectos/reporte.html", {"r": salud.reporte(proyecto)})


def reporte_pdf(request, pk):
    proyecto = proyecto_de(request, pk)
    resp = HttpResponse(pdf.generar(salud.reporte(proyecto)), content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="reporte-{proyecto.pk}.pdf"'
    return resp
