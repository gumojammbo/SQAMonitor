from django.urls import path

from . import views

app_name = "proyectos"
urlpatterns = [
    path("nuevo/", views.nuevo, name="nuevo"),
    path("<int:pk>/", views.detalle, name="detalle"),
    path("<int:pk>/integrantes/", views.agregar_integrante, name="agregar_integrante"),
    path("<int:pk>/integrantes/<int:usuario_id>/quitar/", views.quitar_integrante,
         name="quitar_integrante"),
    path("<int:pk>/reporte/", views.reporte, name="reporte"),
    path("<int:pk>/reporte/pdf/", views.reporte_pdf, name="reporte_pdf"),
    path("<int:pk>/sprints/", views.nuevo_sprint, name="nuevo_sprint"),
    path("<int:pk>/sprints/<int:sprint_id>/metricas/", views.metricas, name="metricas"),
]
