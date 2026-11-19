from django.contrib.auth import login
from django.contrib.auth.decorators import login_not_required
from django.shortcuts import redirect, render

from .forms import RegistroForm


@login_not_required
def registro(request):
    # registra al usuario y le inicia sesion
    form = RegistroForm(request.POST or None)
    if form.is_valid():
        login(request, form.save())
        return redirect("inicio")
    return render(request, "cuentas/registro.html", {"form": form})
