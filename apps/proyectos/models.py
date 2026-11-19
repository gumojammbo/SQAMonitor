from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Proyecto(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    integrantes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="proyectos")

    def __str__(self):
        return self.nombre


class Sprint(models.Model):
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name="sprints")
    nombre = models.CharField(max_length=100)
    inicio = models.DateField()
    fin = models.DateField()

    class Meta:
        ordering = ["inicio"]

    # valida que el sprint no termine antes de empezar
    def clean(self):
        if self.inicio and self.fin and self.fin < self.inicio:
            raise ValidationError("La fecha de fin no puede ser anterior a la de inicio.")

    def __str__(self):
        return self.nombre


# metricas capturadas a mano; un solo registro por sprint
class Metrica(models.Model):
    sprint = models.OneToOneField(Sprint, on_delete=models.CASCADE, related_name="metrica")
    cobertura = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    ejecutadas = models.PositiveIntegerField("pruebas ejecutadas")
    aprobadas = models.PositiveIntegerField("pruebas aprobadas")
    flake8 = models.PositiveIntegerField("errores de flake8")

    # valida que no haya mas aprobadas que ejecutadas
    def clean(self):
        if self.aprobadas is not None and self.ejecutadas is not None \
                and self.aprobadas > self.ejecutadas:
            raise ValidationError({"aprobadas": "No pueden ser más que las ejecutadas."})

    # porcentaje de pruebas que pasan; sin pruebas ejecutadas no hay dato
    def pct_aprobadas(self):
        return self.aprobadas * 100 / self.ejecutadas if self.ejecutadas else None
