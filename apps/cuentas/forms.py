from django.contrib.auth.forms import BaseUserCreationForm

from .models import Usuario


class RegistroForm(BaseUserCreationForm):
    class Meta:
        model = Usuario
        fields = ("correo",)

    # guarda el correo en minusculas para que sea unico sin importar el formato
    def clean_correo(self):
        return self.cleaned_data["correo"].lower()
