from django.contrib import admin

# Register your models here.
from .models import Empresa, Cliente, Producto, DTE, DetalleDTE

admin.site.register(Empresa)
admin.site.register(Cliente)
admin.site.register(Producto)
admin.site.register(DTE)
admin.site.register(DetalleDTE)
