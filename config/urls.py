from django.contrib import admin
from django.urls import include, path

from apps.proyectos.views import lista

urlpatterns = [
    path("admin/", admin.site.urls),
    path("cuentas/", include("apps.cuentas.urls")),
    path("proyectos/", include("apps.proyectos.urls")),
    path("proyectos/<int:pk>/actividades/", include("apps.actividades.urls")),
    path("proyectos/<int:pk>/plantillas/", include("apps.actividades.urls_plantillas")),
    path("", lista, name="inicio"),
]
