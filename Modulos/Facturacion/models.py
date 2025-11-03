from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now   # ✅ Este es el import correcto
from decimal import Decimal

# ======================================================
# PERFIL DE USUARIO
# ======================================================
class Perfil(models.Model):
    ROLES = [
        ('Administrador', 'Administrador'),
        ('Contador', 'Contador'),
        ('Empleado', 'Empleado'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rol = models.CharField(max_length=50, choices=ROLES)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.rol}"


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
    inventario = models.IntegerField(default=0, editable=False)

    def __str__(self):
        return f"{self.descripcion} (${self.precio_unitario})"


# ======================================================
# MODELO DTE
# ======================================================
class DTE(models.Model):
    TIPO_DTE_CHOICES = [
        ('01', 'Factura'),
        ('03', 'Comprobante de Crédito Fiscal'),
        ('05', 'Nota de Crédito'),
        ('06', 'Nota de Débito'),
    ]
    ESTADOS = [
        ('Activo', 'Activo'),
        ('Anulado', 'Anulado'),
    ]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    tipo_dte = models.CharField(max_length=2, choices=TIPO_DTE_CHOICES, default='03')
    numero_control = models.CharField(max_length=50, unique=True)
    fecha_emision = models.DateTimeField(auto_now_add=True)
    condicion_pago = models.CharField(max_length=20, default='Contado')

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    iva = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    codigo_generacion = models.CharField(max_length=100, blank=True, null=True)
    sello_recepcion = models.CharField(max_length=150, blank=True, null=True)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='Activo')

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


# ======================================================
# MODELO PROVEEDOR
# ======================================================
class Proveedor(models.Model):
    nombre = models.CharField(max_length=120)
    nit = models.CharField(max_length=20, unique=True)
    nrc = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.TextField()
    telefono = models.CharField(max_length=20, blank=True, null=True)
    correo = models.EmailField(blank=True, null=True)
    representante = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.nombre


# ======================================================
# MODELO INVENTARIO
# ======================================================
class Inventario(models.Model):
    TIPO_MOVIMIENTO = [
        ('Entrada', 'Entrada'),
        ('Salida', 'Salida'),
    ]

    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='movimientos_inventario'
    )
    tipo = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO)
    cantidad = models.IntegerField()
    fecha = models.DateField(auto_now_add=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.tipo} - {self.producto.descripcion} ({self.cantidad})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.tipo == 'Entrada':
            self.producto.inventario += self.cantidad
        elif self.tipo == 'Salida':
            self.producto.inventario -= self.cantidad
        self.producto.save()


# ======================================================
# MODELO COMPRA (para Libro de Compras)
# ======================================================
class Compra(models.Model):
    fecha = models.DateTimeField(default=now)  # ✅ ahora funciona correctamente
    comprobante_numero = models.CharField(max_length=50)
    registro_nrc = models.CharField(max_length=20)
    proveedor = models.CharField(max_length=150)
    compras_gravadas = models.DecimalField(max_digits=10, decimal_places=2)
    iva_1 = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    iva_13 = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.proveedor} - {self.fecha.strftime('%d/%m/%Y')}"
