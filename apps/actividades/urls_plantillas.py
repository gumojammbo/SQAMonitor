from django.urls import path

from . import views

app_name = "plantillas"
urlpatterns = [
    path("", views.plantillas, name="lista"),
    path("<int:plantilla_id>/", views.plantilla, name="detalle"),
    path("<int:plantilla_id>/criterios/<int:criterio_id>/quitar/", views.quitar_criterio,
         name="quitar_criterio"),
    path("<int:plantilla_id>/borrar/", views.borrar_plantilla, name="borrar"),
]
