from django.apps import AppConfig

class FacturacionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Modulos.Facturacion'

    def ready(self):
        import Modulos.Facturacion.signals  # 👈 carga el signal al iniciar el servidor
