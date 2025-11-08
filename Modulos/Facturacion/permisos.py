from django.shortcuts import redirect
from functools import wraps
from django.contrib import messages
from .models import Perfil

def rol_requerido(roles_permitidos):
    """
    Decorador para restringir acceso según el rol del usuario.
    Permite jerarquía y control por empresa:
      - El 'Administrador' tiene acceso a todo el sistema.
      - Otros roles acceden solo si están en roles_permitidos.
      - Si el usuario no tiene empresa asociada, se bloquea el acceso.
    
    Ejemplo:
        @rol_requerido(['Gerente', 'Contador'])
    """
    def decorador(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # 1️⃣ Verificar autenticación
            if not request.user.is_authenticated:
                messages.warning(request, "Debe iniciar sesión para continuar.")
                return redirect('login')

            # 2️⃣ Obtener perfil del usuario
            perfil = getattr(request.user, 'perfil', None)
            if not perfil:
                messages.error(request, "No se ha asignado un perfil al usuario.")
                return redirect('login')

            # 3️⃣ Validar empresa (solo se bloquea si no es Admin)
            if perfil.rol != 'Administrador' and not perfil.empresa:
                messages.error(request, "Su usuario no está asociado a ninguna empresa.")
                return redirect('menu_principal')

            # 4️⃣ Jerarquía de roles
            if perfil.rol == 'Administrador' or perfil.rol in roles_permitidos:
                return view_func(request, *args, **kwargs)

            # 5️⃣ Si no tiene permisos suficientes
            messages.warning(
                request,
                f"Acceso denegado. Su rol '{perfil.rol}' no tiene permisos para esta sección."
            )
            return redirect('menu_principal')

        return wrapper
    return decorador

