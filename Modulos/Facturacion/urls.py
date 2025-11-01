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
    path('productos/', views.lista_productos, name='lista_productos'),

    # Facturación
    path('menu/facturacion/', views.menu_facturacion, name='menu_facturacion'),
    path('dte/', views.lista_dte, name='lista_dte'),
    path('dte/crear/', views.crear_dte, name='crear_dte'),
    path('dte/nuevo/<str:tipo_dte>/', views.crear_dte, name='crear_dte_tipo'),
    path('clientes/nuevo/', views.crear_cliente, name='crear_cliente'),
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

]


