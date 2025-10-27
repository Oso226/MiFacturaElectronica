from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.redireccion_inicio, name='inicio'),  # 👈 Redirige al login
    path('lista/', views.lista_dte, name='lista_dte'),
    path('crear/', views.crear_dte, name='crear_dte'),
]

