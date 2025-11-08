from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from decimal import Decimal
from django.db.models.signals import post_save
from django.dispatch import receiver

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
# PERFIL DE USUARIO
# ======================================================
class Perfil(models.Model):
    ROLES = [
        ('Administrador', 'Administrador'),
        ('Gerente', 'Gerente'),
        ('Contador', 'Contador'),
        ('Empleado', 'Empleado'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rol = models.CharField(max_length=50, choices=ROLES)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        empresa = self.empresa.nombre if self.empresa else "Sin empresa"
        return f"{self.user.username} - {self.rol} ({empresa})"


# ======================================================
# SIGNAL: CREAR PERFIL AUTOMÁTICAMENTE
# ======================================================
@receiver(post_save, sender=User)
def crear_perfil_automatico(sender, instance, created, **kwargs):
    """
    Crea un perfil automáticamente para cada nuevo usuario.
    Si no se le asigna rol o empresa, el rol por defecto es 'Empleado'.
    """
    if created:
        Perfil.objects.create(user=instance, rol='Empleado')


# ======================================================
# MODELO CLIENTE
# ======================================================
class Cliente(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, null=True, blank=True)
    nombre = models.CharField(max_length=120)
    nit = models.CharField(max_length=20)
    nrc = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.TextField()
    correo = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.nombre

    @property
    def nombre_cliente(self):
        return self.nombre or "Cliente sin nombre"


# ======================================================
# MODELO PRODUCTO
# ======================================================
class Producto(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, null=True, blank=True)
    codigo = models.CharField(max_length=20, unique=True)
    descripcion = models.CharField(max_length=150)
    unidad_medida = models.CharField(max_length=10, default='C/U')
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    inventario = models.IntegerField(default=0, editable=False)

    def __str__(self):
        return f"{self.descripcion} (${self.precio_unitario})"


# ======================================================
# MODELO PROVEEDOR
# ======================================================
class Proveedor(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, null=True, blank=True)
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
# MODELO DTE (DOCUMENTO TRIBUTARIO ELECTRÓNICO)
# ======================================================
class DTE(models.Model):
    TIPO_DTE_CHOICES = [
        ('01', 'Factura'),
        ('03', 'Comprobante de Crédito Fiscal'),
        ('05', 'Nota de Crédito'),
        ('06', 'Nota de Débito'),
        ('07', 'Retención'),
        ('11', 'Liquidación'),
    ]
    ESTADOS = [
        ('Activo', 'Activo'),
        ('Anulado', 'Anulado'),
    ]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    tipo_dte = models.CharField(max_length=2, choices=TIPO_DTE_CHOICES, default='01')
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

    def actualizar_totales(self):
        """Recalcula subtotal, IVA y total según los detalles."""
        detalles = self.detalles.all()
        subtotal = sum(d.total_item for d in detalles)
        iva = subtotal * Decimal('0.13')
        total = subtotal + iva
        self.subtotal = subtotal
        self.iva = iva
        self.total = total
        self.save()

    @property
    def nombre_cliente(self):
        return self.cliente.nombre_cliente


# ======================================================
# MODELO DETALLE DEL DTE
# ======================================================
class DetalleDTE(models.Model):
    dte = models.ForeignKey(DTE, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    total_item = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        """Calcula el total del ítem antes de guardar."""
        self.total_item = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
        self.dte.actualizar_totales()

    def __str__(self):
        return f"{self.producto.descripcion} ({self.cantidad})"


# ======================================================
# MODELO INVENTARIO
# ======================================================
class Inventario(models.Model):
    TIPO_MOVIMIENTO = [
        ('Entrada', 'Entrada'),
        ('Salida', 'Salida'),
    ]

    producto = models.ForeignKey(
        Producto, on_delete=models.CASCADE, related_name='movimientos_inventario'
    )
    tipo = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO)
    cantidad = models.IntegerField()
    fecha = models.DateField(auto_now_add=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.tipo} - {self.producto.descripcion} ({self.cantidad})"

    def save(self, *args, **kwargs):
        """Actualiza inventario del producto automáticamente."""
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
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, null=True, blank=True)
    fecha = models.DateTimeField(default=now)
    comprobante_numero = models.CharField(max_length=50)
    registro_nrc = models.CharField(max_length=20)
    proveedor = models.CharField(max_length=150)
    compras_gravadas = models.DecimalField(max_digits=10, decimal_places=2)
    iva_1 = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    iva_13 = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.proveedor} - {self.fecha.strftime('%d/%m/%Y')}"
