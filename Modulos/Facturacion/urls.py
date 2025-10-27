from django.urls import path
from . import views

urlpatterns = [
    path('', views.iniciar_sesion, name='inicio'),  # 👈 cambia a iniciar_sesion
    path('login/', views.iniciar_sesion, name='login'),
    path('logout/', views.cerrar_sesion, name='logout'),
    path('registro/', views.registro, name='registro'),
    path('lista/', views.lista_dte, name='lista_dte'),
    path('crear/', views.crear_dte, name='crear_dte'),
]

