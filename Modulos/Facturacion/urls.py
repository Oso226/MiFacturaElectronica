from django.urls import path
from . import views

urlpatterns = [
    path('', views.iniciar_sesion, name='inicio'),
    path('login/', views.iniciar_sesion, name='login'),
    path('logout/', views.cerrar_sesion, name='logout'),
    path('registro/', views.registro, name='registro'),

    # Menú
    path('menu/', views.menu_principal, name='menu_principal'),

    # Catálogos
    path('menu/catalogos/', views.menu_catalogos, name='menu_catalogos'),
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('proveedores/', views.lista_proveedores, name='lista_proveedores'),
    path('proveedores/editar/<int:id>/', views.editar_proveedor, name='editar_proveedor'),
    path('proveedores/eliminar/<int:id>/', views.eliminar_proveedor, name='eliminar_proveedor'),
    path('productos/', views.lista_productos, name='lista_productos'),
    path('libros/compras/', views.libro_compras, name='libro_compras'),
    path('libros/ventas/', views.libro_ventas, name='libro_ventas'),
    path('inventario/', views.inventario, name='inventario'),
    path('productos/eliminar/<int:id>/', views.eliminar_producto, name='eliminar_producto'),
    path('compras/registrar/', views.registrar_compra, name='registrar_compra'),
    path('catalogo/', views.catalogo_productos, name='catalogo_productos'),
    path('registrar_venta/', views.registrar_venta, name='registrar_venta'),

    # Facturación
    path('menu/facturacion/', views.menu_facturacion, name='menu_facturacion'),
    path('dte/', views.lista_dte, name='lista_dte'),
    path('dte/crear/', views.crear_dte, name='crear_dte'),
    path('dte/nuevo/<str:tipo_dte>/', views.crear_dte, name='crear_dte_tipo'),
    path('clientes/nuevo/', views.crear_cliente, name='crear_cliente'),
    path('dte/modal/<str:tipo>/', views.modal_dte, name='modal_dte'),
    path('dte/generar/<str:tipo>/', views.generar_dte, name='generar_dte'),
    path('dte/ver/<int:dte_id>/', views.ver_dte, name='ver_dte'),
    path('dte/buscar/', views.buscar_dte, name='buscar_dte'),
    path('auth/validar-admin/', views.validar_admin, name='validar_admin'),
    path('dte/editar/<str:numero_control>/', views.editar_dte, name='editar_dte'),
    path('dte/actualizar/<str:numero_control>/', views.actualizar_dte, name='actualizar_dte'),
    path('enviar-correo/', views.enviar_correo, name='enviar_correo'),

    # Formularios nuevos
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/crear/', views.crear_cliente, name='crear_cliente'),
    path('clientes/editar/<int:id>/', views.editar_cliente, name='editar_cliente'),
    path('clientes/eliminar/<int:id>/', views.eliminar_cliente, name='eliminar_cliente'),
    path('proveedores/nuevo/', views.crear_proveedor, name='crear_proveedor'),
    path('productos/nuevo/', views.crear_producto, name='crear_producto'),

    # Reportes
    path('reportes/ventas/', views.reporte_ventas, name='reporte_ventas'),

    # Administración
    path('usuarios/', views.lista_usuarios, name='usuarios'),


    path('generar-dte/<str:tipo>/', views.generar_dte, name='generar_dte'),

]


