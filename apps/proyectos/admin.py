from django.contrib import admin

from .models import Metrica, Proyecto, Sprint

admin.site.register([Proyecto, Sprint, Metrica])
