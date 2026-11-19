from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.proyectos.models import Proyecto, Sprint

DIMENSIONES = [
    ("especificacion", "Especificación"),
    ("diseno", "Diseño"),
    ("construccion", "Construcción"),
    ("conformidad", "Conformidad"),
]
ESTADOS = [
    ("sin_revision", "Sin revisión"),
    ("pendiente", "Pendiente"),
    ("aprobada", "Aprobada"),
    ("rechazada", "Rechazada"),
]


class Actividad(models.Model):
    sprint = models.ForeignKey(Sprint, on_delete=models.CASCADE, related_name="actividades")
    nombre = models.CharField(max_length=150)
    dimension = models.CharField(max_length=20, choices=DIMENSIONES)
    fecha = models.DateField()
    responsable = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                    related_name="actividades")
    revisor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True,
                                blank=True, related_name="revisiones")
    hecha = models.BooleanField(default=False)
    estado_revision = models.CharField(max_length=15, choices=ESTADOS, default="sin_revision",
                                       editable=False)

    class Meta:
        ordering = ["fecha"]

    # valida que la fecha caiga en el sprint y que el revisor sea otra persona
    def clean(self):
        sprint = self.sprint if self.sprint_id else None
        if sprint and self.fecha and not sprint.inicio <= self.fecha <= sprint.fin:
            raise ValidationError({"fecha": "La fecha debe estar dentro del sprint."})
        if self.revisor_id and self.revisor_id == self.responsable_id:
            raise ValidationError({"revisor": "El revisor no puede ser el responsable."})

    # sin revisor no hay revision; con revisor arranca pendiente
    def save(self, *args, **kwargs):
        if not self.revisor_id:
            self.estado_revision = "sin_revision"
        elif self.estado_revision == "sin_revision":
            self.estado_revision = "pendiente"
        super().save(*args, **kwargs)

    def abiertos(self):
        return self.defectos.filter(estado="abierto").count()

    def __str__(self):
        return self.nombre


VALORACIONES = [("cumple", "Cumple"), ("no_cumple", "No cumple"), ("no_aplica", "No aplica")]


# sin actividad es una plantilla del proyecto; con actividad es su revision
class Checklist(models.Model):
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name="checklists")
    nombre = models.CharField(max_length=100)
    actividad = models.OneToOneField(Actividad, on_delete=models.CASCADE, null=True, blank=True,
                                     related_name="checklist")

    def __str__(self):
        return self.nombre


class Criterio(models.Model):
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, related_name="criterios")
    texto = models.CharField(max_length=200)
    valoracion = models.CharField(max_length=10, choices=VALORACIONES, blank=True)
    observacion = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.texto


SEVERIDADES = [("baja", "Baja"), ("media", "Media"), ("alta", "Alta"), ("critica", "Crítica")]


class Defecto(models.Model):
    actividad = models.ForeignKey(Actividad, on_delete=models.CASCADE, related_name="defectos")
    descripcion = models.CharField(max_length=300)
    severidad = models.CharField(max_length=10, choices=SEVERIDADES, default="media")
    estado = models.CharField(max_length=10, default="abierto", editable=False,
                              choices=[("abierto", "Abierto"), ("corregido", "Corregido")])
    registrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                       related_name="defectos")
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.descripcion
