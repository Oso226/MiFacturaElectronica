"""
Django settings for MiFacturaElectronica project.
Configurado para despliegue en Render (versión optimizada y limpia).
"""

from pathlib import Path
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# =====================================================
# SEGURIDAD Y CONFIGURACIÓN BÁSICA
# =====================================================
SECRET_KEY = os.getenv('SECRET_KEY', 'clave-secreta-local')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = ['*']  # Render asigna el dominio automáticamente

# =====================================================
# APLICACIONES
# =====================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'Modulos.Facturacion',
]

# =====================================================
# MIDDLEWARE
# =====================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', 
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'MiFacturaElectronica.urls'

# =====================================================
# TEMPLATES
# =====================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'Modulos' / 'Facturacion' / 'templates' / 'Facturacion'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'MiFacturaElectronica.wsgi.application'

# =====================================================
# BASE DE DATOS (Render → PostgreSQL, Local → SQLite)
# =====================================================
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'MiFacturaElectronica.db.sqlite3'}",
        conn_max_age=600
    )
}

# =====================================================
# VALIDACIÓN DE CONTRASEÑAS
# =====================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# =====================================================
# INTERNACIONALIZACIÓN
# =====================================================
LANGUAGE_CODE = 'es-sv'
TIME_ZONE = 'America/El_Salvador'
USE_I18N = True
USE_TZ = True

# =====================================================
# ARCHIVOS ESTÁTICOS (Render + Whitenoise)
# =====================================================
STATIC_URL = '/static/'

# En desarrollo: carga archivos desde tu app
if DEBUG:
    STATICFILES_DIRS = [BASE_DIR / 'Modulos' / 'Facturacion' / 'static']
    STATIC_ROOT = BASE_DIR / 'staticfiles_dev'
else:
    # En Render: solo una carpeta limpia
    STATIC_ROOT = BASE_DIR / 'staticfiles'

# Whitenoise servirá los archivos comprimidos en producción
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# =====================================================
# CONFIGURACIÓN DE LOGIN / LOGOUT
# =====================================================
LOGIN_REDIRECT_URL = 'menu_principal'
LOGOUT_REDIRECT_URL = 'login'
LOGIN_URL = 'login'

# =====================================================
# CORREO ELECTRÓNICO (Gmail)
# =====================================================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "manuelito2327@gmail.com"
EMAIL_HOST_PASSWORD = "kzygnyzhqweihsxh"  # Contraseña de aplicación
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# =====================================================
# CONFIGURACIÓN DE SEGURIDAD PARA RENDER
# =====================================================
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_TRUSTED_ORIGINS = ['https://*.onrender.com']

# =====================================================
# AJUSTES EXTRA PARA ENTORNO LOCAL
# =====================================================
if DEBUG:
    import mimetypes
    mimetypes.add_type("text/css", ".css", True)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


