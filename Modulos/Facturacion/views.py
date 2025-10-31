from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from .models import DTE 
from django.shortcuts import redirect
from .models import Perfil
from django.contrib.auth import logout
from .models import DTE, Perfil

def iniciar_sesion(request):
    if request.user.is_authenticated:
        return redirect('lista_dte')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Inicio de sesión exitoso.")
            return redirect('lista_dte')
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")

    return render(request, 'Facturacion/index.html')
    
def cerrar_sesion(request):
    logout(request)
    return redirect('login')
    
def registro(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password1')
        rol = request.POST.get('rol')

        # Verifica si ya existe el usuario
        if User.objects.filter(username=username).exists():
            messages.error(request, "El nombre de usuario ya existe.")
        else:
            # Crea el usuario
            user = User.objects.create_user(username=username, password=password)
            user.save()

            # Crea el perfil asociado
            Perfil.objects.create(user=user, rol=rol)

            messages.success(request, f"Usuario '{username}' registrado exitosamente como {rol}.")
            return redirect('login')

    return render(request, 'registration/registro.html')


@login_required
def lista_dte(request):
    dtes = DTE.objects.all()
    return render(request, 'Facturacion/lista_dte.html', {'dtes': dtes})

# 👇 Crea un nuevo DTE (por ahora vista vacía)
@login_required
#def crear_dte(request):
    #return render(request, 'Facturacion/crear_dte.html')

def crear_dte(request, tipo_dte=None):
    context = {
        'tipo_dte': tipo_dte
    }
    return render(request, 'Facturacion/crear_dte.html', context)

def index(request):
    return render(request, 'index.html')

from django.shortcuts import render

def index(request):
    return render(request, 'Facturacion/index.html')

def factura01(request):
    return render(request, 'Facturacion/templates/forms/factura01.html')

def ccf03(request):
    return render(request, 'Facturacion/forms/ccf03.html')

def liquidacion11(request):
    return render(request, 'Facturacion/forms/liquidacion11.html')

def notaCredito05(request):
    return render(request, 'Facturacion/forms/notaCredito05.html')

def notaDebito06(request):
    return render(request, 'Facturacion/forms/notaDebito06.html')

def retencion07(request):
    return render(request, 'Facturacion/forms/retencion07.html')
