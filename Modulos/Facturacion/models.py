from django.db import models

# ======================================================
# MODELO EMPRESA
# ======================================================
class Empresa(models.Model):
    nombre = models.CharField(max_length=120)
    nit = models.CharField(max_length=20, unique=True)
    nrc = models.CharField(max_length=20, unique=True)
    direccion = models.TextField()
    telefono = models.CharField(max_length=20, blank=True, null=True)
    correo = models.EmailField(blank=True, null=True)
    actividad_economica = models.CharField(max_length=150, blank=True, null=True)
    representante_legal = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.nombre


# ======================================================
# MODELO CLIENTE
# ======================================================
class Cliente(models.Model):
    nombre = models.CharField(max_length=120)
    nit = models.CharField(max_length=20)
    nrc = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.TextField()
    correo = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.nombre


# ======================================================
# MODELO PRODUCTO
# ======================================================
class Producto(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    descripcion = models.CharField(max_length=150)
    unidad_medida = models.CharField(max_length=10, default='C/U')
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.descripcion} (${self.precio_unitario})"


# ======================================================
# MODELO DTE (Documento Tributario Electrónico)
# ======================================================
class DTE(models.Model):
    TIPO_DTE_CHOICES = [
        ('01', 'Factura'),
        ('03', 'Comprobante de Crédito Fiscal'),
        ('05', 'Nota de Crédito'),
        ('06', 'Nota de Débito'),
    ]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    tipo_dte = models.CharField(max_length=2, choices=TIPO_DTE_CHOICES, default='03')
    numero_control = models.CharField(max_length=50, unique=True)
    fecha_emision = models.DateTimeField(auto_now_add=True)
    condicion_pago = models.CharField(max_length=20, default='Contado')

    # Campos financieros
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    iva = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Datos fiscales otorgados por Hacienda
    codigo_generacion = models.CharField(max_length=100, blank=True, null=True)
    sello_recepcion = models.CharField(max_length=150, blank=True, null=True)

    def __str__(self):
        return f"{self.get_tipo_dte_display()} - {self.numero_control}"


# ======================================================
# MODELO DETALLE DEL DTE
# ======================================================
class DetalleDTE(models.Model):
    dte = models.ForeignKey(DTE, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    total_item = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.producto.descripcion} ({self.cantidad})"

