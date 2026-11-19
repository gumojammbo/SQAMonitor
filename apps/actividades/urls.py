from django.urls import path

from . import views

app_name = "actividades"
urlpatterns = [
    path("nueva/", views.formulario, name="nueva"),
    path("<int:actividad_id>/editar/", views.formulario, name="editar"),
    path("<int:actividad_id>/eliminar/", views.eliminar, name="eliminar"),
    path("<int:actividad_id>/checklist/", views.checklist, name="checklist"),
    path("<int:actividad_id>/checklist/crear/", views.crear_checklist, name="crear_checklist"),
    path("<int:actividad_id>/checklist/criterios/", views.nuevo_criterio, name="nuevo_criterio"),
    path("<int:actividad_id>/defectos/", views.defectos, name="defectos"),
    path("<int:actividad_id>/defectos/<int:defecto_id>/editar/", views.editar_defecto,
         name="editar_defecto"),
    path("<int:actividad_id>/defectos/<int:defecto_id>/estado/", views.cambiar_estado_defecto,
         name="estado_defecto"),
]
