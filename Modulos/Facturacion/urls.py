from django.urls import path
from . import views

urlpatterns = [
    path('', views.iniciar_sesion, name='inicio'),  # 👈 cambia a iniciar_sesion
    path('login/', views.iniciar_sesion, name='login'),
    path('logout/', views.cerrar_sesion, name='logout'),
    path('registro/', views.registro, name='registro'),
    path('lista/', views.lista_dte, name='lista_dte'),
    path('crear/', views.crear_dte, name='crear_dte'),
    path('crear-dte/', views.crear_dte, name='crear_dte'),
    path('crear-dte/<str:tipo_dte>/', views.crear_dte, name='crear_dte_tipo'),
    path('', views.index, name='index'),

    path('factura/', views.factura01, name='factura01'),
    path('ccf/', views.ccf03, name='ccf03'),
    path('liquidacion/', views.liquidacion11, name='liquidacion11'),
    path('nota-credito/', views.notaCredito05, name='notaCredito05'),
    path('nota-debito/', views.notaDebito06, name='notaDebito06'),
    path('retencion/', views.retencion07, name='retencion07'),
]

