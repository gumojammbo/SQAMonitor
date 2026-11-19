from django.contrib import admin

from .models import Actividad, Checklist, Criterio, Defecto

admin.site.register([Actividad, Checklist, Criterio, Defecto])
