from django.urls import path
from . import views
from .views import (
    lista_dte,
    crear_dte,
    anular_dte,
    reporte_ventas,
    menu_facturacion,
    generar_dte,
    editar_datos_dte,
    ver_dte_json,
    buscar_dte,
)

urlpatterns = [
    # ======================================================
    # 🔐 AUTENTICACIÓN
    # ======================================================
    path('', views.iniciar_sesion, name='inicio'),
    path('login/', views.iniciar_sesion, name='login'),
    path('logout/', views.cerrar_sesion, name='logout'),
    path('registro/', views.registro, name='registro'),

    # ======================================================
    # 🧭 MENÚ PRINCIPAL
    # ======================================================
    path('menu/', views.menu_principal, name='menu_principal'),

    # ======================================================
    # 📚 CATÁLOGOS
    # ======================================================
    path('menu/catalogos/', views.menu_catalogos, name='menu_catalogos'),

    # --- Clientes ---
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/crear/', views.crear_cliente, name='crear_cliente'),
    path('clientes/editar/<int:id>/', views.editar_cliente, name='editar_cliente'),
    path('clientes/eliminar/<int:id>/', views.eliminar_cliente, name='eliminar_cliente'),

    # --- Proveedores ---
    path('proveedores/', views.lista_proveedores, name='lista_proveedores'),
    path('proveedores/nuevo/', views.crear_proveedor, name='crear_proveedor'),
    path('proveedores/editar/<int:id>/', views.editar_proveedor, name='editar_proveedor'),
    path('proveedores/eliminar/<int:id>/', views.eliminar_proveedor, name='eliminar_proveedor'),

    # --- Productos e Inventario ---
    path('productos/', views.lista_productos, name='lista_productos'),
    path('productos/crear/', views.crear_producto, name='crear_producto'),
    path('productos/editar/<int:id>/', views.editar_producto, name='editar_producto'),
    path('productos/eliminar/<int:id>/', views.eliminar_producto, name='eliminar_producto'),
    path('inventario/', views.inventario, name='inventario'),

    # --- Compras y ventas ---
    path('compras/registrar/', views.registrar_compra, name='registrar_compra'),
    path('catalogo/', views.catalogo_productos, name='catalogo_productos'),
    path('registrar_venta/', views.registrar_venta, name='registrar_venta'),

    # ======================================================
    # 🧾 FACTURACIÓN ELECTRÓNICA (DTE)
    # ======================================================
    path('menu/facturacion/', views.menu_facturacion, name='menu_facturacion'),
    path('dte/', views.lista_dte, name='lista_dte'),
    path('dte/crear/', views.crear_dte, name='crear_dte'),
    path('dte/nuevo/<str:tipo_dte>/', views.crear_dte, name='crear_dte_tipo'),
    path('dte/modal/<str:tipo>/', views.modal_dte, name='modal_dte'),
    path('dte/generar/<str:tipo>/', views.generar_dte, name='generar_dte'),
    path('dte/ver/<int:dte_id>/', views.ver_dte, name='ver_dte'),

    # --- JSON y Búsqueda ---
    path('dte/ver/<int:id>/json/', ver_dte_json, name='ver_dte_json'),  # ✅ para el modal de edición
    path('dte/buscar/', buscar_dte, name='buscar_dte'),

    # --- Edición ---
    path('dte/editar/<str:numero_control>/', views.editar_dte, name='editar_dte'),
    path('dte/actualizar/<str:numero_control>/', views.actualizar_dte, name='actualizar_dte'),
    path('dte/editar-datos/<int:id>/', editar_datos_dte, name='editar_datos_dte'),

    # --- Anulación ---
    path('dte/anular/<int:id>/', anular_dte, name='anular_dte'),

    # ======================================================
    # 📬 ENVÍO DE CORREOS
    # ======================================================
    path('enviar-correo/', views.enviar_correo, name='enviar_correo'),

    # ======================================================
    # 📘 LIBROS Y REPORTES
    # ======================================================
    path('libros/compras/', views.libro_compras, name='libro_compras'),
    path('libros/ventas/', views.libro_ventas, name='libro_ventas'),
    path('reportes/ventas/', reporte_ventas, name='reporte_ventas'),

    # ======================================================
    # ⚙️ ADMINISTRACIÓN
    # ======================================================
    path('usuarios/', views.lista_usuarios, name='usuarios'),

    # ======================================================
    # 🔑 VALIDACIONES (AJAX / MODALES)
    # ======================================================
    path('auth/validar-admin/', views.validar_admin, name='validar_admin'),
]



