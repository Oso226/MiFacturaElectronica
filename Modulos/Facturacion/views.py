from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.utils.timezone import now
from decimal import Decimal
from openpyxl.styles import Alignment, Font, Border, Side
import openpyxl
from django.db import IntegrityError

# Modelos y formularios
from .models import DTE, Perfil, Cliente, Proveedor, Producto, Inventario, Compra
from .forms import ClienteForm, ProveedorForm, ProductoForm
from .permisos import rol_requerido
import uuid
import io
import base64
import qrcode
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

# 🔧 NUEVO - librerías para QR, UUID, base64 y utilidades
import uuid
import io
import base64
import qrcode
import time
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail


# ======================================================
# 🔐 AUTENTICACIÓN
# ======================================================

def iniciar_sesion(request):
    if request.user.is_authenticated:
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
    return render(request, 'registration/login.html')


def cerrar_sesion(request):
    logout(request)
    messages.success(request, "Sesión cerrada correctamente.")
    return redirect('login')


def registro(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password1')
        rol = request.POST.get('rol')

        if User.objects.filter(username=username).exists():
            messages.error(request, "El nombre de usuario ya existe.")
        else:
            user = User.objects.create_user(username=username, password=password)
            perfil = Perfil.objects.get(user=user)
            perfil.rol = rol
            perfil.save()
            messages.success(request, f"Usuario '{username}' registrado exitosamente como {rol}.")
            return redirect('login')

    return render(request, 'registration/registro.html')


# ======================================================
# 🧭 MENÚ PRINCIPAL
# ======================================================

@login_required
def menu_principal(request):
    perfil = Perfil.objects.get(user=request.user)
    return render(request, 'Facturacion/menu_principal.html', {'rol': perfil.rol})


# ======================================================
# 🧾 FACTURACIÓN
# ======================================================

@rol_requerido(['Administrador', 'Contador', 'Empleado'])
def lista_dte(request):
    dtes = DTE.objects.all()
    return render(request, 'Facturacion/lista_dte.html', {'dtes': dtes})


@rol_requerido(['Administrador', 'Empleado'])
def crear_dte(request, tipo_dte=None):
    if not tipo_dte:
        messages.warning(request, "Debes seleccionar un tipo de documento.")
        return redirect('menu_principal')

    # 🔹 Ajuste de rutas (ya no existe carpeta forms)
    plantillas_dte = {
        '01': 'Facturacion/factura01.html',
        '03': 'Facturacion/ccf03.html',
        '05': 'Facturacion/notaCredito05.html',
        '06': 'Facturacion/notaDebito06.html',
        '07': 'Facturacion/retencion07.html',
        '11': 'Facturacion/liquidacion11.html',
    }

    template = plantillas_dte.get(tipo_dte, 'Facturacion/factura01.html')
    return render(request, template, {'tipo_dte': tipo_dte})


@rol_requerido(['Administrador', 'Contador'])
def anular_dte(request, id):
    dte = get_object_or_404(DTE, id=id)
    dte.estado = 'Anulado'
    dte.save()
    messages.success(request, f'Documento {dte.numero_control} ha sido anulado.')
    return redirect('lista_dte')


@rol_requerido(['Administrador', 'Contador'])
def reporte_ventas(request):
    dtes = DTE.objects.filter(estado='Activo').order_by('-fecha_emision')
    total_general = sum(d.total for d in dtes)
    return render(request, 'Facturacion/ventas.html', {
        'dtes': dtes,
        'total': total_general
    })

@login_required
def menu_facturacion(request):
    """ Muestra menú general de facturación """
    return render(request, 'Facturacion/menu_facturacion.html')


def nueva_factura(request, tipo):
    """ Vista individual de factura tipo 01 """
    dte = get_object_or_404(DTE, tipo_dte=tipo)
    return render(request, 'Facturacion/factura01.html', {
        'dte': dte,
        'empresa': dte.empresa,
        'cliente': dte.cliente
    })

from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
import time

@csrf_exempt
@login_required
def generar_dte(request, tipo):
    """
    Simula envío del DTE al Ministerio y envío por correo al cliente.
    """
    try:
        dte = DTE.objects.filter(tipo_dte=tipo).last()
        if not dte:
            return JsonResponse({'success': False, 'error': 'No se encontró el documento.'})

        # Simulación de envío al Ministerio
        time.sleep(2)
        dte.codigo_generacion = "MH-" + str(int(time.time()))
        dte.sello_recepcion = "SELLO-" + str(int(time.time()))
        dte.save()

        # Envío de correo (simulado)
        if dte.cliente and dte.cliente.correo:
            send_mail(
                subject="Comprobante Electrónico Aprobado",
                message=f"Estimado {dte.cliente.nombre}, su documento {dte.get_tipo_dte_display()} ha sido aprobado por el Ministerio de Hacienda.",
                from_email="facturacion@tusistema.com",
                recipient_list=[dte.cliente.correo],
                fail_silently=True,
            )

        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ======================================================
# 📚 CATÁLOGOS
# ======================================================

@login_required
def menu_catalogos(request):
    return render(request, 'Facturacion/menu_catalogos.html')


@rol_requerido(['Administrador', 'Empleado'])
def lista_clientes(request):
    clientes = Cliente.objects.all().order_by('-id')[:20]
    return render(request, 'Facturacion/clientes.html', {'clientes': clientes})


@rol_requerido(['Administrador', 'Empleado'])
def crear_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        return JsonResponse({'error': 'Formulario inválido'}, status=400)
    else:
        form = ClienteForm()
        return render(request, 'Facturacion/form_cliente.html', {'form': form})


@rol_requerido(['Administrador', 'Contador'])
def editar_cliente(request, id):
    cliente = get_object_or_404(Cliente, id=id)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, "Cliente actualizado correctamente.")
            return redirect('lista_clientes')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'Facturacion/form_cliente.html', {'form': form})


@rol_requerido(['Administrador'])
def eliminar_cliente(request, id):
    cliente = get_object_or_404(Cliente, id=id)
    cliente.delete()
    messages.success(request, "Cliente eliminado correctamente.")
    return redirect('lista_clientes')


# ======================================================
# 🏢 PROVEEDORES
# ======================================================

@login_required
def lista_proveedores(request):
    proveedores = Proveedor.objects.all()
    return render(request, 'Facturacion/proveedores.html', {'proveedores': proveedores})


@login_required
def crear_proveedor(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Proveedor agregado correctamente.")
            return redirect('lista_proveedores')
    else:
        form = ProveedorForm()
    return render(request, 'Facturacion/form_proveedor.html', {'form': form})


@login_required
def editar_proveedor(request, id):
    proveedor = get_object_or_404(Proveedor, id=id)
    if request.method == 'POST':
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            messages.success(request, f"Proveedor '{proveedor.nombre}' actualizado correctamente.")
            return redirect('lista_proveedores')
    else:
        form = ProveedorForm(instance=proveedor)
    return render(request, 'Facturacion/form_proveedor.html', {'form': form})


@login_required
def eliminar_proveedor(request, id):
    proveedor = get_object_or_404(Proveedor, id=id)
    proveedor.delete()
    messages.success(request, f"Proveedor '{proveedor.nombre}' eliminado correctamente.")
    return redirect('lista_proveedores')


# ======================================================
# 📦 PRODUCTOS E INVENTARIO
# ======================================================

@login_required
def lista_productos(request):
    productos = Producto.objects.all()
    return render(request, 'Facturacion/productos.html', {'productos': productos})


@login_required
def crear_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            codigo = form.cleaned_data['codigo']
            if Producto.objects.filter(codigo=codigo).exists():
                return JsonResponse({'error': f"El código '{codigo}' ya existe."}, status=400)
            
            producto = form.save(commit=False)
            producto.inventario = 0
            producto.save()
            return JsonResponse({'success': True})
        return JsonResponse({'error': 'Formulario inválido'}, status=400)
    else:
        form = ProductoForm()
        return render(request, 'Facturacion/form_producto.html', {'form': form})


@login_required
def inventario(request):
    query = request.GET.get('q', '')
    productos = Producto.objects.all().order_by('codigo')
    if query:
        productos = productos.filter(Q(codigo__icontains=query) | Q(descripcion__icontains(query)))
    return render(request, 'Facturacion/inventario.html', {'productos': productos, 'query': query})


@login_required
def eliminar_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    producto.delete()
    messages.success(request, f"Producto '{producto.descripcion}' eliminado correctamente.")
    return redirect('inventario')


# ======================================================
# 💰 COMPRAS E INVENTARIO
# ======================================================

@login_required
def registrar_compra(request):
    if request.method == 'POST':
        try:
            producto_id = request.POST.get('producto')
            cantidad = int(request.POST.get('cantidad'))
            proveedor_id = request.POST.get('proveedor')

            producto = Producto.objects.get(id=producto_id)
            proveedor = Proveedor.objects.get(id=proveedor_id)

            subtotal = producto.precio_unitario * Decimal(cantidad)
            iva_13 = subtotal * Decimal('0.13')
            total = subtotal + iva_13

            # Actualiza inventario
            Inventario.objects.create(
                producto=producto,
                tipo='Entrada',
                cantidad=cantidad,
                descripcion=f"Compra registrada de {proveedor.nombre}"
            )

            Compra.objects.create(
                fecha=now(),
                comprobante_numero=f"COMP-{now().strftime('%Y%m%d%H%M%S')}",
                registro_nrc=proveedor.nrc or "N/A",
                proveedor=proveedor.nombre,
                compras_gravadas=subtotal,
                iva_13=iva_13,
                total=total
            )

            from .models import Empresa, Cliente
            empresa = Empresa.objects.first()
            cliente = Cliente.objects.first()
            if empresa and cliente:
                DTE.objects.create(
                    empresa=empresa,
                    cliente=cliente,
                    tipo_dte='03',
                    numero_control=f"COMP-{now().strftime('%Y%m%d%H%M%S')}",
                    subtotal=subtotal,
                    iva=iva_13,
                    total=total,
                    codigo_generacion=f"Compra a proveedor: {proveedor.nombre}",
                    estado='Activo',
                    fecha_emision=now()
                )

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f"Compra registrada correctamente. Se añadieron {cantidad} unidades al inventario de '{producto.descripcion}'."
                })

            messages.success(request, "✅ Compra registrada correctamente.")
            return redirect('inventario')

        except Exception as e:
            error_msg = f"Ocurrió un error al registrar la compra: {str(e)}"
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)
            return redirect('inventario')

    productos = Producto.objects.all().order_by('descripcion')
    proveedores = Proveedor.objects.all().order_by('nombre')
    return render(request, 'Facturacion/form_compra.html', {
        'productos': productos,
        'proveedores': proveedores
    })


# ======================================================
# 📘 LIBRO DE COMPRAS
# ======================================================

@login_required
def libro_compras(request):
    dtes = DTE.objects.filter(tipo_dte='03', estado='Activo').order_by('-fecha_emision')
    compras_dte = []
    for dte in dtes:
        proveedor = (
            dte.codigo_generacion.replace("Compra a proveedor: ", "")
            if dte.codigo_generacion and "Compra a proveedor:" in dte.codigo_generacion
            else (dte.cliente.nombre if hasattr(dte.cliente, "nombre") else "N/A")
        )
        compras_dte.append({
            "fecha": dte.fecha_emision.strftime("%d/%m/%Y"),
            "comprobante": dte.numero_control,
            "registro": dte.empresa.nrc if hasattr(dte.empresa, "nrc") else "—",
            "proveedor": proveedor,
            "gravadas": float(dte.subtotal),
            "iva": float(dte.iva),
            "total": float(dte.total),
        })

    compras_extra = [
        {
            "fecha": c.fecha.strftime("%d/%m/%Y"),
            "comprobante": c.comprobante_numero,
            "registro": c.registro_nrc,
            "proveedor": c.proveedor,
            "gravadas": float(c.compras_gravadas),
            "iva": float(c.iva_13),
            "total": float(c.total),
        }
        for c in Compra.objects.all().order_by('-fecha')
    ]

    compras = compras_dte + compras_extra

    return render(request, 'Facturacion/libro_compras.html', {'compras': compras})


# ======================================================
# 📗 LIBRO DE VENTAS
# ======================================================

@login_required
def libro_ventas(request):
    dtes = DTE.objects.filter(tipo_dte='01', estado='Activo')

    ventas = [
        {
            "fecha": dte.fecha_emision.strftime("%d/%m/%Y"),
            "numero": dte.numero_control,
            "cliente": dte.cliente.nombre,
            "subtotal": float(dte.subtotal),
            "iva": float(dte.iva),
            "total": float(dte.total),
        }
        for dte in dtes
    ]

    return render(request, 'Facturacion/libro_ventas.html', {'ventas': ventas})


# ======================================================
# 🧑‍💼 USUARIOS
# ======================================================

@rol_requerido(['Administrador'])
def lista_usuarios(request):
    usuarios = User.objects.all().select_related('perfil')
    return render(request, 'Facturacion/usuarios.html', {'usuarios': usuarios})

def _generar_numero_control(tipo):
    """Genera un número de control ficticio único."""
    return f"DTE-{tipo}-" + uuid.uuid4().hex[:8].upper()


def _generar_qr_datauri(text):
    """Genera un QR embebido en formato base64."""
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(bio.getvalue()).decode()}"

@csrf_exempt
@login_required
def modal_dte(request, tipo):
    """Crea y carga el DTE con datos del catálogo (producto, cliente, totales)"""
    from .models import Empresa, Cliente, DTE
    from django.utils import timezone

    empresa = Empresa.objects.first()
    if not empresa:
        empresa = Empresa.objects.create(
            nombre="Omnigest S.A. de C.V.",
            nit="0614-240325-001-1",
            nrc="123456-7",
            direccion="San Salvador Centro frente a Salvador del Mundo",
            telefono="2290-9444",
            correo="info@omnigest.com",
            representante_legal="Sucursal Salvador del Mundo"
        )

    cliente = Cliente.objects.first()
    producto = None

    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        venta = data.get('producto', {})
        cliente_id = data.get('clienteId')
        nuevo_cliente = data.get('nuevoCliente')

        # Buscar o crear cliente
        if cliente_id:
            cliente = Cliente.objects.filter(id=cliente_id).first()
        elif nuevo_cliente:
            cliente = Cliente.objects.create(
                nombre=nuevo_cliente,
                correo=data.get('correo', ''),
                direccion=data.get('direccion', '')
            )

        if venta:
            producto = {
                'nombre': venta.get('nombre'),
                'cantidad': venta.get('cantidad'),
                'precio': venta.get('precio'),
                'subtotal': venta.get('subtotal'),
                'iva': venta.get('iva'),
                'total': venta.get('total'),
            }

    dte = DTE.objects.create(
        empresa=empresa,
        cliente=cliente,
        tipo_dte=tipo,
        numero_control=f"DTE-{tipo}-{uuid.uuid4().hex[:8].upper()}",
        fecha_emision=timezone.now(),
        condicion_pago="Contado",
        subtotal=producto['subtotal'] if producto else 0,
        iva=producto['iva'] if producto else 0,
        total=producto['total'] if producto else 0,
        codigo_generacion="(Asignado por MH)",
        sello_recepcion="(Pendiente)",
        estado="Activo"
    )

    plantillas_dte = {
        '01': 'Facturacion/factura01.html',
        '03': 'Facturacion/ccf03.html',
        '05': 'Facturacion/notaCredito05.html',
        '06': 'Facturacion/notaDebito06.html',
        '07': 'Facturacion/retencion07.html',
        '11': 'Facturacion/liquidacion11.html',
    }

    return render(request, plantillas_dte.get(tipo, 'Facturacion/factura01.html'), {
        'tipo_dte': tipo,
        'dte': dte,
        'empresa': empresa,
        'cliente': cliente,
        'producto': producto
    })

@login_required
def ver_dte(request, dte_id):
    """
    Muestra el DTE individual (por ejemplo, cuando se abre desde el QR).
    """
    dte = get_object_or_404(DTE, id=dte_id)
    empresa = dte.empresa
    cliente = dte.cliente

    # Generar nuevamente el QR para mostrarlo en pantalla
    qr_text = f"{dte.numero_control}|{empresa.nit}|{cliente.nit}|{dte.total:.2f}"
    qr_data = _generar_qr_datauri(qr_text)

    # Plantilla según tipo de documento
    plantillas_dte = {
        '01': 'Facturacion/factura01.html',
        '03': 'Facturacion/ccf03.html',
        '05': 'Facturacion/notaCredito05.html',
        '06': 'Facturacion/notaDebito06.html',
        '07': 'Facturacion/retencion07.html',
        '11': 'Facturacion/liquidacion11.html',
    }
    template = plantillas_dte.get(dte.tipo_dte, 'Facturacion/ccf03.html')

    return render(request, template, {
        'dte': dte,
        'empresa': empresa,
        'cliente': cliente,
        'qr_data': qr_data
    })

@login_required
def buscar_dte(request):
    """Filtra DTE por cliente o número de control."""
    query = request.GET.get('q', '').strip()
    resultados = []

    if len(query) >= 2:
        dtes = DTE.objects.filter(
            Q(numero_control__icontains=query) |
            Q(codigo_generacion__icontains=query) |
            Q(cliente__nombre__icontains=query)
        ).select_related('cliente').order_by('-fecha_emision')[:15]

        resultados = [{
            'tipo_dte': dte.get_tipo_dte_display(),
            'numero_control': dte.numero_control,
            'cliente': dte.cliente.nombre if dte.cliente else 'N/A',
            'fecha': dte.fecha_emision.strftime("%d/%m/%Y %H:%M"),
            'total': f"{dte.total:.2f}",
            'estado': dte.estado
        } for dte in dtes]

    return JsonResponse({'resultados': resultados})

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth import authenticate
from .models import Perfil
import json

@csrf_exempt
def validar_admin(request):
    """
    Valida las credenciales de un usuario con rol 'Administrador'.
    Compatible con el modelo Perfil.
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        user = authenticate(username=username, password=password)
        if not user:
            return JsonResponse({'success': False, 'error': 'Usuario o contraseña incorrectos'})

        perfil = Perfil.objects.filter(user=user).first()
        if not perfil:
            return JsonResponse({'success': False, 'error': 'El usuario no tiene perfil asignado'})

        if perfil.rol.lower() == 'administrador':
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'No tiene permisos de administrador'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def editar_dte(request, numero_control):
    """
    Carga el DTE para edición (solo si usuario tiene permisos de administrador).
    """
    from .models import Empresa, Cliente, DTE, DetalleDTE

    dte = get_object_or_404(DTE, numero_control=numero_control)
    detalles = dte.detalles.all()

    if request.method == 'POST':
        # Actualiza los campos
        dte.cliente.nombre = request.POST.get('cliente', dte.cliente.nombre)
        dte.cliente.direccion = request.POST.get('direccion', dte.cliente.direccion)
        dte.cliente.correo = request.POST.get('correo', dte.cliente.correo)
        dte.cliente.save()

        dte.condicion_pago = request.POST.get('condicion_pago', dte.condicion_pago)
        dte.estado = request.POST.get('estado', dte.estado)
        dte.total = request.POST.get('total', dte.total)
        dte.save()

        messages.success(request, "✅ Documento actualizado correctamente.")
        return JsonResponse({'success': True})

    return render(request, 'Facturacion/editar_dte.html', {
        'dte': dte,
        'empresa': dte.empresa,
        'cliente': dte.cliente,
        'detalles': detalles,
    })

@csrf_exempt
@login_required
def actualizar_dte(request, numero_control):
    """
    Actualiza un DTE y recalcula totales para reflejarlo en reportes y libros.
    """
    from .models import DTE, DetalleDTE
    import json

    try:
        dte = DTE.objects.filter(numero_control=numero_control).select_related('cliente', 'empresa').first()
        if not dte:
            return JsonResponse({'success': False, 'error': 'No se encontró el documento.'})

        data = json.loads(request.body.decode('utf-8'))

        # 🔹 Actualizar campos básicos (solo si vienen en el request)
        if 'estado' in data:
            dte.estado = data['estado']
        if 'condicion_pago' in data:
            dte.condicion_pago = data['condicion_pago']
        if 'total' in data:
            try:
                dte.total = Decimal(str(data['total'])).quantize(Decimal('0.01'))
            except Exception:
                dte.total = Decimal('0.00')

        # 🔹 Actualizar cliente si cambió
        if 'cliente' in data:
            dte.cliente.nombre = data['cliente']
        if 'correo' in data:
            dte.cliente.correo = data['correo']
        if 'direccion' in data:
            dte.cliente.direccion = data['direccion']
        dte.cliente.save()

        # 🔹 Recalcular subtotal e IVA
        if hasattr(dte, 'detalles') and dte.detalles.exists():
            subtotal = sum(Decimal(det.total_item) for det in dte.detalles.all())
        else:
            subtotal = (dte.total / Decimal('1.13')).quantize(Decimal('0.01'))

        iva = (subtotal * Decimal('0.13')).quantize(Decimal('0.01'))
        dte.subtotal = subtotal
        dte.iva = iva
        dte.total = subtotal + iva
        dte.fecha_emision = timezone.now()
        dte.save()

        # 🔹 Respuesta de confirmación
        return JsonResponse({
            'success': True,
            'msg': '✅ Documento actualizado y sincronizado correctamente.',
            'total': f"{dte.total:.2f}",
            'iva': f"{dte.iva:.2f}",
            'subtotal': f"{dte.subtotal:.2f}"
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def catalogo_productos(request):
    """
    Muestra los productos en stock, permite seleccionar cantidad, cliente y generar un DTE.
    """
    from .models import Producto, Cliente
    productos = Producto.objects.all().order_by('descripcion')
    clientes = Cliente.objects.all().order_by('nombre')
    return render(request, 'Facturacion/catalogo_productos.html', {
        'productos': productos,
        'clientes': clientes
    })





