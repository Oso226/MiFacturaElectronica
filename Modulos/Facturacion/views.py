from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from django.http import HttpResponse
from django.utils.timezone import now
import openpyxl
from openpyxl.styles import Alignment, Font, Border, Side
from .models import DTE, Perfil, Cliente, Proveedor, Producto, Inventario
from .forms import ClienteForm, ProveedorForm, ProductoForm
from .permisos import rol_requerido
from decimal import Decimal
from django.db import IntegrityError
from django.utils.timezone import now
from .models import Compra
from django.http import JsonResponse




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
            user.save()
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

    plantillas_dte = {
        '01': 'Facturacion/forms/factura01.html',
        '03': 'Facturacion/forms/ccf03.html',
        '05': 'Facturacion/forms/notaCredito05.html',
        '06': 'Facturacion/forms/notaDebito06.html',
        '07': 'Facturacion/forms/retencion07.html',
        '11': 'Facturacion/forms/liquidacion11.html',
    }
    template = plantillas_dte.get(tipo_dte, 'forms/factura01.html')
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
    dtes = DTE.objects.filter(estado='Activo')
    total_general = sum(d.total for d in dtes)
    return render(request, 'Facturacion/ventas.html', {'dtes': dtes, 'total': total_general})


@login_required
def menu_facturacion(request):
    return render(request, 'Facturacion/menu_facturacion.html')


# ======================================================
# 📚 CATÁLOGOS
# ======================================================

@login_required
def menu_catalogos(request):
    return render(request, 'Facturacion/menu_catalogos.html')


@rol_requerido(['Administrador', 'Empleado'])
def lista_clientes(request):
    clientes = Cliente.objects.all().order_by('-id')[:20]  # 🔹 20 registros más nuevos
    return render(request, 'Facturacion/clientes.html', {'clientes': clientes})


@rol_requerido(['Administrador', 'Empleado'])
def crear_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})  # ✅ Para cerrar el modal
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
# 🏢 PROVEEDORES (COMPLETO)
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
    """
    Crea un nuevo producto en el catálogo base (para el modal).
    """
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            codigo = form.cleaned_data['codigo']
            if Producto.objects.filter(codigo=codigo).exists():
                return JsonResponse({'error': f"El código '{codigo}' ya existe."}, status=400)
            
            producto = form.save(commit=False)
            producto.inventario = 0
            producto.save()
            return JsonResponse({'success': True})  # ✅ Cierra modal al guardar
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
# 💰 REGISTRAR COMPRAS (Actualiza inventario y libro)
# ======================================================

from django.http import JsonResponse

@login_required
def registrar_compra(request):
    """
    Registra una compra, actualiza inventario y genera el libro de compras.
    Compatible con AJAX y uso normal.
    """
    print("👉 Headers recibidos:", request.headers)  # 👈 debug temporal

    if request.method == 'POST':
        try:
            producto_id = request.POST.get('producto')
            cantidad = int(request.POST.get('cantidad'))
            proveedor_id = request.POST.get('proveedor')

            producto = Producto.objects.get(id=producto_id)
            proveedor = Proveedor.objects.get(id=proveedor_id)

            # 1️⃣ Calcular montos
            subtotal = producto.precio_unitario * Decimal(cantidad)
            iva_13 = subtotal * Decimal('0.13')
            total = subtotal + iva_13

            # 2️⃣ Crear movimiento en Inventario
            Inventario.objects.create(
                producto=producto,
                tipo='Entrada',
                cantidad=cantidad,
                descripcion=f"Compra registrada de {proveedor.nombre}"
            )

            # 3️⃣ Registrar compra
            Compra.objects.create(
                fecha=now(),
                comprobante_numero=f"COMP-{now().strftime('%Y%m%d%H%M%S')}",
                registro_nrc=proveedor.nrc or "N/A",
                proveedor=proveedor.nombre,
                compras_gravadas=subtotal,
                iva_13=iva_13,
                total=total
            )

            # 4️⃣ Registrar DTE
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

            # ✅ Si viene del modal (AJAX)
            if (
                request.headers.get('x-requested-with') == 'XMLHttpRequest' or
                request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
            ):
                return JsonResponse({
                    'success': True,
                    'message': f"Compra registrada correctamente. Se añadieron {cantidad} unidades al inventario de '{producto.descripcion}'."
                })

            # ✅ Si es una petición normal
            messages.success(request, "✅ Compra registrada correctamente.")
            return redirect('inventario')

        except Exception as e:
            error_msg = f"Ocurrió un error al registrar la compra: {str(e)}"

            if (
                request.headers.get('x-requested-with') == 'XMLHttpRequest' or
                request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
            ):
                return JsonResponse({'success': False, 'error': error_msg})

            messages.error(request, error_msg)
            return redirect('inventario')

    # ✅ GET → mostrar formulario
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
    """
    Muestra el libro de compras combinando los registros de DTE (tipo 03)
    y las compras registradas directamente en el modelo Compra.
    """
    # ✅ Reúne los DTE activos tipo '03'
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

    # ✅ Añade también las compras directas (modelo Compra)
    compras_registro = Compra.objects.all().order_by('-fecha')
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
        for c in compras_registro
    ]

    # ✅ Unifica todo
    compras = compras_dte + compras_extra

    # ✅ Exportar a Excel
    if 'exportar' in request.GET:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Libro de Compras"

        negrita = Font(bold=True)
        centrado = Alignment(horizontal="center", vertical="center")
        borde = Border(left=Side(style='thin'), right=Side(style='thin'),
                       top=Side(style='thin'), bottom=Side(style='thin'))

        ws.merge_cells('A1:H1')
        ws['A1'] = "LIBRO DE COMPRAS"
        ws['A1'].font = Font(bold=True, size=14)
        ws['A1'].alignment = centrado

        encabezados = ["N°", "FECHA", "COMPROBANTE", "REGISTRO", "PROVEEDOR",
                       "COMPRAS GRAVADAS", "IVA 13%", "TOTAL"]
        ws.append(encabezados)

        for cell in ws[2]:
            cell.font = negrita
            cell.alignment = centrado
            cell.border = borde

        for i, c in enumerate(compras, start=1):
            ws.append([
                i, c["fecha"], c["comprobante"], c["registro"], c["proveedor"],
                c["gravadas"], c["iva"], c["total"]
            ])

        # Totales
        total_gravadas = sum(c["gravadas"] for c in compras)
        total_iva = sum(c["iva"] for c in compras)
        total_total = sum(c["total"] for c in compras)
        ws.append(["", "", "", "", "TOTALES", total_gravadas, total_iva, total_total])

        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, max_col=8):
            for cell in row:
                cell.border = borde

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = f'attachment; filename=\"Libro_Compras_{now().strftime('%Y%m%d')}.xlsx\"'
        wb.save(response)
        return response

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

    if 'exportar' in request.GET:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Libro de Ventas"

        negrita = Font(bold=True)
        centrado = Alignment(horizontal="center", vertical="center")
        borde = Border(left=Side(style='thin'), right=Side(style='thin'),
                       top=Side(style='thin'), bottom=Side(style='thin'))

        ws.merge_cells('A1:G1')
        ws['A1'] = "LIBRO DE VENTAS"
        ws['A1'].font = Font(bold=True, size=14)
        ws['A1'].alignment = centrado

        encabezados = ["N°", "FECHA", "DOCUMENTO", "CLIENTE",
                       "VENTAS GRAVADAS", "IVA 13%", "TOTAL"]
        ws.append(encabezados)

        for cell in ws[2]:
            cell.font = negrita
            cell.alignment = centrado
            cell.border = borde

        for i, v in enumerate(ventas, start=1):
            ws.append([
                i, v["fecha"], v["numero"], v["cliente"],
                v["subtotal"], v["iva"], v["total"]
            ])

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = f'attachment; filename="Libro_Ventas_{now().strftime("%Y%m%d")}.xlsx"'
        wb.save(response)
        return response

    return render(request, 'Facturacion/libro_ventas.html', {'ventas': ventas})


# ======================================================
# 🧑‍💼 USUARIOS
# ======================================================

@rol_requerido(['Administrador'])
def lista_usuarios(request):
    usuarios = User.objects.all().select_related('perfil')
    return render(request, 'Facturacion/usuarios.html', {'usuarios': usuarios})
