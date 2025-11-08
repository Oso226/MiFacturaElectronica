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
from .models import Producto
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
import json
from .models import DTE
from .models import DTE, DetalleDTE
from django.utils.timezone import localtime
import tempfile
from weasyprint import HTML
import os
from datetime import datetime
from .models import Cliente, DTE, DetalleDTE, Empresa
import threading
from weasyprint import HTML, CSS


# ======================================================
# 🔐 AUTENTICACIÓN
# ======================================================

def iniciar_sesion(request):
    """
    Inicia sesión de usuario verificando rol y empresa asociada.
    Si el usuario ya está autenticado, lo redirige a su menú principal.
    """
    if request.user.is_authenticated:
        return redirect('menu_principal')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # 🔹 Cargar perfil asociado al usuario
            perfil = Perfil.objects.filter(user=user).select_related('empresa').first()

            # 🔒 Validar si el perfil existe
            if not perfil:
                logout(request)
                messages.error(request, "El usuario no tiene un perfil asignado.")
                return redirect('login')

            # 🔒 Validar si el usuario tiene empresa (multiempresa)
            if not perfil.empresa:
                messages.warning(request, "No se encontró empresa asignada al usuario.")
            else:
                request.session['empresa_id'] = perfil.empresa.id

            messages.success(request, f"Inicio de sesión exitoso como {perfil.rol}.")
            return redirect('menu_principal')
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")

    return render(request, 'registration/login.html')


def cerrar_sesion(request):
    """
    Cierra la sesión del usuario actual y limpia los datos de sesión.
    """
    if 'empresa_id' in request.session:
        del request.session['empresa_id']
    logout(request)
    messages.success(request, "Sesión cerrada correctamente.")
    return redirect('login')


def registro(request):
    """
    Registra un nuevo usuario con su rol y crea automáticamente el perfil.
    Por seguridad, puede deshabilitarse el acceso público en producción.
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password1')
        rol = request.POST.get('rol')
        empresa_id = request.POST.get('empresa')  # opcional si se asigna desde admin

        if User.objects.filter(username=username).exists():
            messages.error(request, "El nombre de usuario ya existe.")
        else:
            user = User.objects.create_user(username=username, password=password)
            perfil = Perfil.objects.create(user=user, rol=rol)

            # 🔹 Si se envía empresa desde el formulario
            if empresa_id:
                from .models import Empresa
                empresa = Empresa.objects.filter(id=empresa_id).first()
                if empresa:
                    perfil.empresa = empresa
                    perfil.save()

            messages.success(request, f"Usuario '{username}' registrado exitosamente como {rol}.")
            return redirect('login')

    return render(request, 'registration/registro.html')

# ======================================================
# 🧭 MENÚ PRINCIPAL
# ======================================================

@login_required
def menu_principal(request):
    """
    Muestra el menú principal con el rol y empresa del usuario logueado.
    No genera error si el perfil no tiene empresa asignada.
    """
    perfil = Perfil.objects.select_related('empresa').filter(user=request.user).first()

    # Si no hay perfil asociado al usuario
    if not perfil:
        messages.error(request, "No se encontró un perfil asociado al usuario.")
        return redirect('logout')

    # Si el perfil no tiene empresa, evitar error 500
    if not perfil.empresa:
        empresa_nombre = "Sin empresa asignada"
    else:
        empresa_nombre = perfil.empresa.nombre
        request.session['empresa_id'] = perfil.empresa.id  # Guardar en sesión

    # 🔹 Contexto enviado al template
    contexto = {
        'rol': perfil.rol,
        'empresa': empresa_nombre
    }

    print("Rol:", perfil.rol)
    print("Empresa mostrada:", empresa_nombre)

    return render(request, 'Facturacion/menu_principal.html', contexto)

# 📄 Lista de documentos emitidos
@rol_requerido(['Administrador', 'Contador', 'Empleado'])
def lista_dte(request):
    dtes = DTE.objects.all().order_by('-fecha_emision')
    return render(request, 'Facturacion/lista_dte.html', {'dtes': dtes})


# 🧾 Crear nuevo documento
@rol_requerido(['Administrador', 'Empleado'])
def crear_dte(request, tipo_dte=None):
    if not tipo_dte:
        messages.warning(request, "Debes seleccionar un tipo de documento.")
        return redirect('menu_facturacion')

    # 🔹 Ajuste de rutas de plantillas
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


# ❌ Anular documento
@rol_requerido(['Administrador', 'Contador'])
def anular_dte(request, id):
    dte = get_object_or_404(DTE, id=id)
    dte.estado = 'Anulado'
    dte.save()
    messages.success(request, f'Documento {dte.numero_control} ha sido anulado correctamente.')
    return redirect('lista_dte')


# 📊 Reporte de ventas
@rol_requerido(['Administrador', 'Contador'])
def reporte_ventas(request):
    dtes = DTE.objects.filter(estado='Activo').order_by('-fecha_emision')
    total_general = sum(d.total for d in dtes)
    return render(request, 'Facturacion/ventas.html', {
        'dtes': dtes,
        'total': total_general
    })


# 🧭 Menú principal de facturación
@login_required
def menu_facturacion(request):
    """ Muestra menú general de facturación con diseño coherente """
    perfil = getattr(request.user, 'perfil', None)
    rol = perfil.rol if perfil else 'Sin Rol'

    return render(request, 'Facturacion/menu_facturacion.html', {
        'rol': rol,
        'empresa': getattr(perfil, 'empresa', 'Sin empresa asignada')
    })


# 🧾 Vista individual de factura tipo 01
@login_required
def nueva_factura(request, tipo):
    dte = get_object_or_404(DTE, tipo_dte=tipo)
    return render(request, 'Facturacion/factura01.html', {
        'dte': dte,
        'empresa': dte.empresa,
        'cliente': dte.cliente
    })


# ======================================================
# ⚙️ GENERAR DTE (Simulación de envío con PDF y JSON)
# ======================================================
@csrf_exempt
@login_required
def generar_dte(request, tipo):
    """
    Simula el envío del DTE al Ministerio y envía al cliente:
    - El aviso de aprobación.
    - Adjuntos: comprobante en PDF y JSON.
    """
    try:
        dte = DTE.objects.filter(tipo_dte=tipo).last()
        if not dte:
            return JsonResponse({'success': False, 'error': 'No se encontró el documento.'})

        # ⏳ Simulación de tiempo de procesamiento
        time.sleep(2)

        # 🔹 Generar códigos simulados
        dte.codigo_generacion = "MH-" + str(int(time.time()))
        dte.sello_recepcion = "SELLO-" + str(int(time.time()))
        dte.save()

        # 🔹 Crear JSON con los datos del DTE
        import tempfile, json
        json_path = tempfile.gettempdir() + f"\\DTE_{dte.numero_control}.json"

        dte_json = {
            "tipo_dte": dte.tipo_dte,
            "numero_control": dte.numero_control,
            "cliente": dte.cliente.nombre if dte.cliente else "Sin cliente",
            "correo": dte.cliente.correo if dte.cliente else "",
            "fecha_emision": dte.fecha_emision.strftime("%Y-%m-%d"),
            "total": float(dte.total),
            "codigo_generacion": dte.codigo_generacion,
            "sello_recepcion": dte.sello_recepcion,
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(dte_json, f, ensure_ascii=False, indent=4)

        # 🔹 Generar PDF con la plantilla oficial (factura01.html)
        from io import BytesIO
        from django.template.loader import render_to_string
        from xhtml2pdf import pisa

        pdf_buffer = BytesIO()
        # 📄 Renderizar la factura con tu plantilla HTML original
        html_content = render_to_string("Facturacion/factura01.html", {
            "dte": dte,
            "empresa": dte.empresa,
            "cliente": dte.cliente,
            "editable": False,
            "qr_data": None,
        })

        # 🎨 Agregar tus estilos CSS reales
        css_path = os.path.join(settings.BASE_DIR, 'Modulos', 'Facturacion', 'static', 'css', 'factura01.css')
        pdf_buffer = BytesIO()

        # 🖨️ Generar PDF con WeasyPrint (idéntico a lo que ves en el navegador)
        HTML(string=html_content, base_url=request.build_absolute_uri("/")).write_pdf(
        pdf_buffer, stylesheets=[CSS(filename=css_path)]
    )

        pdf_buffer.seek(0)

        # 🔹 Envío de correo al cliente
        if dte.cliente and dte.cliente.correo:
            from django.core.mail import EmailMessage

            email = EmailMessage(
                subject="📄 Comprobante Electrónico Aprobado - OMNIGEST",
                body=(
                    f"Estimado {dte.cliente.nombre},\n\n"
                    f"Su documento electrónico tipo {dte.get_tipo_dte_display()} "
                    f"ha sido aprobado por el Ministerio de Hacienda.\n\n"
                    "Adjunto encontrará su comprobante en formato PDF y JSON.\n\n"
                    "Saludos cordiales,\nEquipo OMNIGEST"
                ),
                from_email="facturacion@omnigest.com",
                to=[dte.cliente.correo],
            )

            # Adjuntar PDF
            email.attach(f"DTE_{dte.numero_control}.pdf", pdf_buffer.read(), "application/pdf")

            # Adjuntar JSON
            with open(json_path, "r", encoding="utf-8") as f:
                email.attach(f"DTE_{dte.numero_control}.json", f.read(), "application/json")

            email.send(fail_silently=False)

        return JsonResponse({'success': True, 'msg': 'DTE enviado con comprobantes adjuntos.'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ======================================================
# ✏️ EDITAR CAMPOS DEL CLIENTE EN UN DTE
# ======================================================
@rol_requerido(['Administrador', 'Gerente'])
@csrf_exempt
def editar_datos_dte(request, id):
    """
    Permite modificar datos del cliente (nombre, correo, NIT, dirección)
    y reenviar el comprobante actualizado (PDF + JSON) al cliente.
    """
    dte = get_object_or_404(DTE, id=id)

    if request.method == "POST":
        try:
            import json, tempfile
            data = json.loads(request.body.decode('utf-8'))

            # 🔹 Actualizar datos del cliente
            cliente = dte.cliente
            cliente.nombre = data.get('nombre', cliente.nombre)
            cliente.correo = data.get('correo', cliente.correo)
            cliente.nit = data.get('nit', cliente.nit)
            cliente.direccion = data.get('direccion', cliente.direccion)
            cliente.save()

            # 🔹 Simular nuevo código MH
            time.sleep(2)
            dte.codigo_generacion = "MH-" + str(int(time.time()))
            dte.sello_recepcion = "SELLO-" + str(int(time.time()))
            dte.save()

            # 🔹 Crear JSON actualizado
            json_path = tempfile.gettempdir() + f"\\DTE_{dte.numero_control}.json"

            dte_json = {
                "tipo_dte": dte.tipo_dte,
                "numero_control": dte.numero_control,
                "cliente": cliente.nombre,
                "correo": cliente.correo,
                "fecha_emision": dte.fecha_emision.strftime("%Y-%m-%d"),
                "total": float(dte.total),
                "codigo_generacion": dte.codigo_generacion,
                "sello_recepcion": dte.sello_recepcion,
            }

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(dte_json, f, ensure_ascii=False, indent=4)

            # 🔹 Crear PDF actualizado con factura01.html
            from io import BytesIO
            from django.template.loader import render_to_string
            from xhtml2pdf import pisa

            pdf_buffer = BytesIO()
            # 📄 Renderizar la factura con tu plantilla HTML original
            html_content = render_to_string("Facturacion/factura01.html", {
                 "dte": dte,
                "empresa": dte.empresa,
                "cliente": dte.cliente,
                "editable": False,
                "qr_data": None,
            })

            # 🎨 Agregar tus estilos CSS reales
            css_path = os.path.join(settings.BASE_DIR, 'Modulos', 'Facturacion', 'static', 'css', 'factura01.css')
            pdf_buffer = BytesIO()

            # 🖨️ Generar PDF con WeasyPrint (idéntico a lo que ves en el navegador)
            HTML(string=html_content, base_url=request.build_absolute_uri("/")).write_pdf(
            pdf_buffer, stylesheets=[CSS(filename=css_path)]
            )

            pdf_buffer.seek(0)

            # 🔹 Enviar correo al cliente con los adjuntos
            if cliente.correo:
                from django.core.mail import EmailMessage

                email = EmailMessage(
                    subject="📄 DTE Actualizado y Aprobado - OMNIGEST",
                    body=(
                        f"Estimado {cliente.nombre},\n\n"
                        "Su documento electrónico ha sido actualizado y aprobado "
                        "por el Ministerio de Hacienda.\n\n"
                        "Adjunto encontrará su comprobante actualizado en PDF y JSON.\n\n"
                        "Saludos,\nEquipo OMNIGEST"
                    ),
                    from_email="facturacion@omnigest.com",
                    to=[cliente.correo],
                )

                # Adjuntar PDF actualizado
                email.attach(f"DTE_{dte.numero_control}.pdf", pdf_buffer.read(), "application/pdf")

                # Adjuntar JSON actualizado
                with open(json_path, "r", encoding="utf-8") as f:
                    email.attach(f"DTE_{dte.numero_control}.json", f.read(), "application/json")

                email.send(fail_silently=False)

            return JsonResponse({
                "status": "ok",
                "msg": "Documento actualizado y reenviado al cliente con comprobantes adjuntos."
            })

        except Exception as e:
            return JsonResponse({"status": "error", "msg": str(e)})

    return JsonResponse({"status": "error", "msg": "Método no permitido."})


@login_required
def ver_dte_json(request, id):
    """Devuelve los datos del DTE en formato JSON para edición rápida"""
    dte = get_object_or_404(DTE, id=id)
    return JsonResponse({
        "id": dte.id,
        "tipo_dte": dte.tipo_dte,
        "numero_control": dte.numero_control,
        "fecha": dte.fecha_emision.strftime("%Y-%m-%d %H:%M"),
        "estado": dte.estado,
        "total": float(dte.total),
        "cliente_nombre": dte.cliente.nombre if dte.cliente else "",
        "cliente_correo": dte.cliente.correo if dte.cliente else "",
        "cliente_nit": dte.cliente.nit if dte.cliente else "",
        "cliente_direccion": dte.cliente.direccion if dte.cliente else ""
    })

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
    Muestra el DTE (desde el botón Editar o QR), con productos incluidos.
    Si el usuario es Administrador, el modal será editable.
    """
    from .models import DTE, DetalleDTE, Perfil

    dte = get_object_or_404(DTE, id=dte_id)
    empresa = dte.empresa
    cliente = dte.cliente

    # 🔹 Obtener los productos asociados
    detalles = DetalleDTE.objects.filter(dte=dte).select_related('producto')

    # 🔹 Verificar si el usuario es Administrador
    perfil = Perfil.objects.filter(user=request.user).first()
    es_admin = perfil and perfil.rol.lower() == 'administrador'

    # 🔹 Generar QR
    qr_text = f"{dte.numero_control}|{empresa.nit}|{cliente.nit}|{dte.total:.2f}"
    qr_data = _generar_qr_datauri(qr_text)

    # 🔹 Plantilla según tipo
    plantillas_dte = {
        '01': 'Facturacion/factura01.html',
        '03': 'Facturacion/ccf03.html',
        '05': 'Facturacion/notaCredito05.html',
        '06': 'Facturacion/notaDebito06.html',
        '07': 'Facturacion/retencion07.html',
        '11': 'Facturacion/liquidacion11.html',
    }
    template = plantillas_dte.get(dte.tipo_dte, 'Facturacion/factura01.html')

    # 🔹 Contexto
    contexto = {
        'dte': dte,
        'empresa': empresa,
        'cliente': cliente,
        'detalles': detalles,
        'qr_data': qr_data,
        'editable': es_admin,  # habilita edición si es admin
    }

    return render(request, template, contexto)


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
    
def buscar_dte(request):
    """Busca documentos DTE por cliente o número de control"""
    q = request.GET.get("q", "").strip()
    resultados = []

    if q:
        # 🔹 Filtramos por cliente o número de control
        dtes = (
            DTE.objects.filter(
                Q(cliente__nombre__icontains=q) | Q(numero_control__icontains=q)
            )
            .select_related("cliente")
            .order_by("-fecha_emision")[:10]  # ✅ Solo los 10 más recientes
        )

        resultados = [
            {
                "id": d.id,
                "tipo_dte": d.get_tipo_dte_display(),
                "numero_control": d.numero_control,
                "cliente": d.cliente.nombre,
                # ✅ Convertir la fecha a zona local (El Salvador) y formatearla
                "fecha": localtime(d.fecha_emision).strftime("%Y-%m-%d %H:%M"),
                "total": str(round(d.total, 2)),
                "estado": d.estado,
            }
            for d in dtes
        ]

    return JsonResponse({"resultados": resultados})

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

def registrar_venta(request):
    if request.method == "POST":
        try:
            producto_id = int(request.POST.get('producto_id'))
            cantidad = int(request.POST.get('cantidad'))

            producto = get_object_or_404(Producto, id=producto_id)

            # Validar stock
            if producto.inventario < cantidad:
                return JsonResponse({'status': 'error', 'mensaje': 'Stock insuficiente'}, status=400)

            # Descontar inventario
            producto.inventario -= cantidad
            producto.save()

            return JsonResponse({'status': 'ok', 'nuevo_stock': producto.inventario})
        except Exception as e:
            return JsonResponse({'status': 'error', 'mensaje': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'}, status=405)

def enviar_correo_async(email):
    """Envía el correo en un hilo separado para evitar timeout en Render."""
    try:
        print("🚀 Intentando enviar correo a:", email.to)
        email.send(fail_silently=False)
        print("✅ Correo enviado correctamente (modo async).")
    except Exception as e:
        print(f"❌ Error al enviar correo async: {e}")

def enviar_correo(request):
    """Envía el comprobante de venta al correo del cliente con PDF y JSON adjuntos."""
    if request.method == "POST":
        try:
            # 📦 Obtener datos enviados desde el frontend
            data = json.loads(request.body)

            correo = data.get("correo")
            cliente_nombre = data.get("cliente")
            producto = data.get("producto")
            cantidad = data.get("cantidad")
            precio_unitario = float(data.get("precio_unitario", 0))
            subtotal = float(data.get("subtotal", 0))
            iva = float(data.get("iva", 0))
            total = float(data.get("total", 0))
            tipo_dte = data.get("tipo_dte", "01")

            # 🧩 Intentar obtener el cliente real desde la BD (si se envía ID o nombre)
            cliente_obj = None
            if isinstance(cliente_nombre, int) or str(cliente_nombre).isdigit():
                cliente_obj = Cliente.objects.filter(id=int(cliente_nombre)).first()
            elif isinstance(cliente_nombre, str):
                cliente_obj = Cliente.objects.filter(nombre__iexact=cliente_nombre.strip()).first()

            if cliente_obj:
                cliente_nombre = cliente_obj.nombre
                correo = cliente_obj.correo or correo or "cliente@ejemplo.com"

            if not correo:
                return JsonResponse({"status": "error", "msg": "Correo no proporcionado"})

            # 🏢 Obtener datos de la empresa (si existe)
            empresa = Empresa.objects.first()

            # ✅ Crear contexto para la plantilla
            contexto = {
                "empresa": {
                    "nombre": empresa.nombre if empresa else "Omnigest S.A. de C.V.",
                    "nit": empresa.nit if empresa else "0623-123456-1-9",
                    "nrc": empresa.nrc if empresa else "000000-0",
                    "direccion": empresa.direccion if empresa else "San Salvador Centro frente a Salvador del Mundo",
                    "telefono": empresa.telefono if empresa else "2290-9444",
                    "correo": empresa.correo if empresa else "info@omnigest.com",
                    "sucursal": "Sucursal Salvador del Mundo",
                },
                "cliente": {
                    "nombre": cliente_nombre,
                    "direccion": cliente_obj.direccion if cliente_obj else "Ahuachapán",
                    "nit": cliente_obj.nit if cliente_obj else "0101-231288-103-0",
                    "correo": correo,
                },
                "dte": {
                    "tipo": tipo_dte,
                    "numero_control": f"DTE-{tipo_dte}-{datetime.now().strftime('%H%M%S')}",
                    "fecha_emision": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "condicion": "Contado",
                    "caja": "101",
                    "tipo_venta": "CONTADO",
                    "vendedor": "Sucursal Salvador del Mundo",
                },
                "detalle": [
                    {
                        "codigo": "P001",
                        "descripcion": producto,
                        "cantidad": cantidad,
                        "precio_unitario": precio_unitario,
                        "total_item": subtotal,
                    }
                ],
                "totales": {
                    "subtotal": subtotal,
                    "iva": iva,
                    "total": total,
                },
                "notas": "Gracias por su compra. Conserve este comprobante como respaldo de su operación.",
                "en_letras": f"{total:.2f} dólares",
            }

            # ✅ Renderizar HTML de la factura
            html_string = render_to_string("Facturacion/factura01.html", contexto)

            # ✅ Generar PDF temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as pdf_temp:
                HTML(string=html_string, base_url=request.build_absolute_uri("/")).write_pdf(pdf_temp.name)
                pdf_temp.seek(0)
                pdf_bytes = pdf_temp.read()

            # ✅ Crear JSON estructurado
            json_bytes = json.dumps(contexto, indent=4, ensure_ascii=False).encode("utf-8")

            # ✅ Renderizar cuerpo del correo (HTML)
            html_content = render_to_string("Facturacion/email_comprobante.html", {
                "cliente": cliente_nombre,
                "producto": producto,
                "total": total,
                "tipo_dte": dict(DTE.TIPO_DTE_CHOICES).get(tipo_dte, "Factura")
            })

            # ✅ Asunto del correo
            asunto = f"📄 Comprobante Electrónico ({dict(DTE.TIPO_DTE_CHOICES).get(tipo_dte, 'Factura')}) - {cliente_nombre}"

            # ✅ Crear correo
            email = EmailMessage(
                subject=asunto,
                body=html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[correo],
            )
            email.content_subtype = "html"

            # ✅ Adjuntar PDF y JSON
            email.attach(f"Comprobante_{cliente_nombre}.pdf", pdf_bytes, "application/pdf")
            email.attach(f"Comprobante_{cliente_nombre}.json", json_bytes, "application/json")

            # ✅ Enviar correo en hilo separado (evita timeout en Render)
            threading.Thread(target=enviar_correo_async, args=(email,)).start()

            # ✅ Eliminar archivo temporal
            os.remove(pdf_temp.name)

            # ✅ Responder inmediatamente al cliente
            return JsonResponse({
                "status": "ok",
                "msg": f"El comprobante está siendo enviado a {correo}."
            })

        except Exception as e:
            print(f"❌ Error al enviar correo: {e}")
            return JsonResponse({"status": "error", "msg": str(e)})

    # Si no es método POST
    return JsonResponse({"status": "error", "msg": "Método no permitido"})

