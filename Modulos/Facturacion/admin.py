from django.contrib import admin
from .models import Empresa, Cliente, Producto, DTE, DetalleDTE
from .models import Perfil

@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('user', 'rol', 'fecha_registro')

admin.site.register(Empresa)
admin.site.register(Cliente)
admin.site.register(Producto)
admin.site.register(DTE)
admin.site.register(DetalleDTE)
