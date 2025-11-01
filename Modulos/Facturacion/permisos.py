# Modulos/Facturacion/permisos.py
from django.shortcuts import redirect
from functools import wraps

# ======== FUNCIONES AUXILIARES ========

def rol_requerido(roles_permitidos):
    """
    Decorador para restringir acceso según el rol del usuario.
    Ejemplo: @rol_requerido(['Administrador', 'Contador'])
    """
    def decorador(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            perfil = getattr(request.user, 'perfil', None)
            if perfil and perfil.rol in roles_permitidos:
                return view_func(request, *args, **kwargs)
            else:
                return redirect('menu_principal')  # redirige si no tiene permiso
        return wrapper
    return decorador
