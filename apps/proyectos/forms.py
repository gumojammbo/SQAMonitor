from django import forms

from apps.cuentas.models import Usuario

from .models import Metrica, Proyecto, Sprint


class ProyectoForm(forms.ModelForm):
    class Meta:
        model = Proyecto
        fields = ("nombre",)


class SprintForm(forms.ModelForm):
    class Meta:
        model = Sprint
        fields = ("nombre", "inicio", "fin")
        widgets = {c: forms.DateInput(attrs={"type": "date"}) for c in ("inicio", "fin")}


class MetricaForm(forms.ModelForm):
    class Meta:
        model = Metrica
        fields = ("cobertura", "ejecutadas", "aprobadas", "flake8")


class IntegranteForm(forms.Form):
    correo = forms.EmailField()

    def __init__(self, *args, proyecto, **kwargs):
        super().__init__(*args, **kwargs)
        self.proyecto = proyecto

    # busca al usuario registrado y rechaza a quien ya es integrante
    def clean_correo(self):
        correo = self.cleaned_data["correo"].lower()
        self.usuario = Usuario.objects.filter(correo=correo).first()
        if not self.usuario:
            raise forms.ValidationError("No hay un usuario registrado con ese correo.")
        if self.proyecto.integrantes.filter(pk=self.usuario.pk).exists():
            raise forms.ValidationError("Ese usuario ya es integrante.")
        return correo
