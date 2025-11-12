from django import forms
from .models import Cliente, Proveedor, Producto

# ======================================================
# FORMULARIO CLIENTE
# ======================================================
class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'dui', 'nit', 'nrc', 'direccion', 'correo', 'telefono']  # ✅ incluye DUI
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre completo'}),
            'dui': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000000-0'}), 
            'nit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 0614-123456-001-0'}),
            'nrc': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de registro'}),
            'direccion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 1,  # ✅ tamaño inicial pequeño
                'style': 'overflow:hidden;resize:none;height:auto;min-height:38px;',  # ✅ autoajuste dinámico
                'placeholder': 'Dirección'
            }),
            'correo': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ejemplo@correo.com'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '7777-7777'}),
        }

# ======================================================
# FORMULARIO PROVEEDOR
# ======================================================
class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = '__all__'
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de proveedor'}),
            'nit': forms.TextInput(attrs={'class': 'form-control'}),
            'nrc': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control'}),
            'representante_legal': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Representante Legal'}),
        }

# ======================================================
# FORMULARIO PRODUCTO
# ======================================================
class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = '__all__'
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Código del producto'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descripción del producto'}),
            'unidad_medida': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: C/U'}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
