from django.shortcuts import render

# Create your views here.

from django.contrib.auth.decorators import login_required
from .models import DTE 
from django.shortcuts import redirect

def redireccion_inicio(request):
    if request.user.is_authenticated:
        # 👇 Si el usuario ya inició sesión, lo enviamos a la lista de DTE
        return redirect('lista_dte')
    else:
        # 👇 Si no está autenticado, lo enviamos al login
        return redirect('login')


@login_required
def lista_dte(request):
    dtes = DTE.objects.all()
    return render(request, 'Facturacion/lista_dte.html', {'dtes': dtes})

# 👇 Crea un nuevo DTE (por ahora vista vacía)
@login_required
def crear_dte(request):
    return render(request, 'Facturacion/crear_dte.html')


