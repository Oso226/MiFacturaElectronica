from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from .models import DTE, Perfil, Cliente, Proveedor, Producto
from .forms import ClienteForm
from .permisos import rol_requerido

# ======================================================
# AUTENTICACIÓN
# ======================================================

def iniciar_sesion(request):
    if request.user.is_authenticated:
        # Si ya inició sesión, lo llevamos al menú
        return redirect('menu_principal')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Inicio de sesión exitoso.")
            return redirect('menu_principal')
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")

    # Si es GET o falló el login, muestra la plantilla de login
    return render(request, 'registration/login.html')


@login_required
def menu_principal(request):
    return render(request, 'Facturacion/menu_principal.html')


def cerrar_sesion(request):
    logout(request)
    messages.success(request, "Sesión cerrada correctamente.")
    return redirect('login')


from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import Perfil

def registro(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password1')
        rol = request.POST.get('rol')

        # Verifica si el usuario ya existe
        if User.objects.filter(username=username).exists():
            messages.error(request, "El nombre de usuario ya existe.")
        else:
            # ✅ Crea el usuario (el signal creará el perfil automáticamente)
            user = User.objects.create_user(username=username, password=password)
            user.save()

            # ✅ Recupera el perfil creado por el signal
            perfil = Perfil.objects.get(user=user)
            perfil.rol = rol  # actualiza el rol elegido en el formulario
            perfil.save()

            messages.success(request, f"Usuario '{username}' registrado exitosamente como {rol}.")
            return redirect('login')

    return render(request, 'registration/registro.html')



# ======================================================
# FACTURACIÓN
# ======================================================

@login_required
def lista_dte(request):
    """
    Redirige directamente al menú principal, ya que ahora cada tipo de DTE
    tiene su propia plantilla (factura01, ccf03, etc.)
    """
    messages.info(request, "Selecciona el tipo de documento a emitir desde el menú principal.")
    return redirect('menu_principal')


@login_required
def crear_dte(request, tipo_dte=None):
    """
    Muestra la plantilla correspondiente al tipo de documento (DTE)
    según el código recibido en la URL: 01, 03, 05, 06, 07, 11, etc.
    """

    if not tipo_dte:
        messages.warning(request, "Debes seleccionar un tipo de documento.")
        return redirect('menu_principal')

    # Mapeo tipo de documento → plantilla HTML existente
    plantillas_dte = {
        '01': 'Facturacion/forms/factura01.html',
        '03': 'Facturacion/forms/ccf03.html',
        '05': 'Facturacion/forms/notaCredito05.html',
        '06': 'Facturacion/forms/notaDebito06.html',
        '07': 'Facturacion/forms/retencion07.html',
        '11': 'Facturacion/forms/liquidacion11.html',
    }

    # Busca la plantilla según el tipo recibido, usa factura01 como fallback
    template = plantillas_dte.get(tipo_dte, 'Facturacion/forms/factura01.html')

    context = {
        'tipo_dte': tipo_dte,
    }

    return render(request, template, context)


@login_required
def anular_dte(request, id):
    dte = get_object_or_404(DTE, id=id)
    dte.estado = 'Anulado'
    dte.save()
    messages.success(request, f'Documento {dte.numero_control} ha sido anulado.')
    return redirect('menu_principal')


@login_required
def reporte_ventas(request):
    dtes = DTE.objects.filter(estado='Activo')
    total_general = sum(d.total for d in dtes)
    return render(request, 'Facturacion/ventas.html', {'dtes': dtes, 'total': total_general})


@login_required
def menu_facturacion(request):
    """
    Vista intermedia que muestra las opciones para emitir documentos
    (factura, CCF, nota crédito, etc.)
    """
    return render(request, 'Facturacion/menu_facturacion.html')



# ======================================================
# CATÁLOGOS
# ======================================================

@login_required
def menu_catalogos(request):
    """
    Vista intermedia para acceder a los catálogos: Clientes, Proveedores y Productos.
    """
    return render(request, 'Facturacion/menu_catalogos.html')


def lista_clientes(request):
    clientes = Cliente.objects.all()
    return render(request, 'Facturacion/clientes.html', {'clientes': clientes})

def crear_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_clientes')
    else:
        form = ClienteForm()
    return render(request, 'Facturacion/form_cliente.html', {'form': form})

def editar_cliente(request, id):
    cliente = get_object_or_404(Cliente, id=id)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect('lista_clientes')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'Facturacion/form_cliente.html', {'form': form})

def eliminar_cliente(request, id):
    cliente = get_object_or_404(Cliente, id=id)
    cliente.delete()
    return redirect('lista_clientes')

@login_required
def lista_proveedores(request):
    proveedores = Proveedor.objects.all()
    return render(request, 'Facturacion/proveedores.html', {'proveedores': proveedores})


@login_required
def lista_productos(request):
    productos = Producto.objects.all()
    return render(request, 'Facturacion/productos.html', {'productos': productos})


@login_required
def lista_usuarios(request):
    usuarios = User.objects.all().select_related('perfil')
    return render(request, 'Facturacion/usuarios.html', {'usuarios': usuarios})

from .forms import ClienteForm, ProveedorForm, ProductoForm

# ======================================================
# FORMULARIOS PROVEEDOR Y PRODUCTO
# ======================================================

@login_required
def crear_proveedor(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Proveedor agregado correctamente.")
            return redirect('menu_principal')
    else:
        form = ProveedorForm()
    return render(request, 'Facturacion/form_proveedor.html', {'form': form})


@login_required
def crear_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Producto agregado correctamente.")
            return redirect('menu_principal')
    else:
        form = ProductoForm()
    return render(request, 'Facturacion/form_producto.html', {'form': form})

# ========================
# MENÚ PRINCIPAL (Todos)
# ========================
@login_required
def menu_principal(request):
    return render(request, 'Facturacion/menu_principal.html')

# ========================
# CLIENTES
# ========================
@rol_requerido(['Administrador', 'Contador', 'Empleado'])
def lista_clientes(request):
    clientes = Cliente.objects.all()
    return render(request, 'Facturacion/clientes.html', {'clientes': clientes})

@rol_requerido(['Administrador'])
def eliminar_cliente(request, id):
    cliente = get_object_or_404(Cliente, id=id)
    cliente.delete()
    return redirect('lista_clientes')

@rol_requerido(['Administrador', 'Contador'])
def editar_cliente(request, id):
    cliente = get_object_or_404(Cliente, id=id)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect('lista_clientes')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'Facturacion/form_cliente.html', {'form': form})

@rol_requerido(['Administrador', 'Empleado'])
def crear_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_clientes')
    else:
        form = ClienteForm()
    return render(request, 'Facturacion/form_cliente.html', {'form': form})

# ========================
# FACTURACIÓN
# ========================
@rol_requerido(['Administrador', 'Contador', 'Empleado'])
def lista_dte(request):
    dtes = DTE.objects.all()
    return render(request, 'Facturacion/lista_dte.html', {'dtes': dtes})

@rol_requerido(['Administrador', 'Empleado'])
def crear_dte(request, tipo_dte=None):
    context = {'tipo_dte': tipo_dte}
    return render(request, 'Facturacion/crear_dte.html', context)

@rol_requerido(['Administrador', 'Contador'])
def anular_dte(request, id):
    dte = get_object_or_404(DTE, id=id)
    dte.estado = 'Anulado'
    dte.save()
    messages.success(request, f'Documento {dte.numero_control} ha sido anulado.')
    return redirect('lista_dte')

# ========================
# REPORTES
# ========================
@rol_requerido(['Administrador', 'Contador'])
def reporte_ventas(request):
    dtes = DTE.objects.filter(estado='Activo')
    total_general = sum(d.total for d in dtes)
    return render(request, 'Facturacion/ventas.html', {'dtes': dtes, 'total': total_general})

# ========================
# USUARIOS
# ========================
@rol_requerido(['Administrador'])
def lista_usuarios(request):
    usuarios = User.objects.all().select_related('perfil')
    return render(request, 'Facturacion/usuarios.html', {'usuarios': usuarios})


