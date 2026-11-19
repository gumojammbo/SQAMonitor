from django import forms

from .models import Actividad, Checklist, Criterio, Defecto


class ActividadForm(forms.ModelForm):
    class Meta:
        model = Actividad
        fields = ("nombre", "sprint", "dimension", "fecha", "responsable", "revisor", "hecha")
        widgets = {"fecha": forms.DateInput(attrs={"type": "date"})}

    # limita sprint, responsable y revisor a lo que pertenece al proyecto
    def __init__(self, *args, proyecto, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sprint"].queryset = proyecto.sprints.all()
        self.fields["responsable"].queryset = proyecto.integrantes.all()
        self.fields["revisor"].queryset = proyecto.integrantes.all()


class PlantillaForm(forms.ModelForm):
    class Meta:
        model = Checklist
        fields = ("nombre",)


# checklist de una actividad; opcionalmente parte de una plantilla del proyecto
class ChecklistForm(PlantillaForm):
    plantilla = forms.ModelChoiceField(queryset=None, required=False, empty_label="Sin plantilla")

    def __init__(self, *args, proyecto, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["plantilla"].queryset = proyecto.checklists.filter(actividad__isnull=True)


class CriterioForm(forms.ModelForm):
    class Meta:
        model = Criterio
        fields = ("texto",)


# una fila por criterio para valorarlo y comentarlo
CriterioFormSet = forms.modelformset_factory(Criterio, fields=("valoracion", "observacion"),
                                             extra=0)


class DefectoForm(forms.ModelForm):
    class Meta:
        model = Defecto
        fields = ("descripcion", "severidad")
