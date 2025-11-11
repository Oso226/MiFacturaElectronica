"""
Django settings for MiFacturaElectronica project.
Optimizado para Render, multiempresa y seguridad.
"""

from pathlib import Path
import os
import dj_database_url

# =====================================================
# BASE Y SEGURIDAD
# =====================================================
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'clave-secreta-local')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = ['*']  # Render asigna dominio automáticamente

# =====================================================
# APLICACIONES INSTALADAS
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
# BASE DE DATOS
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
# ARCHIVOS ESTÁTICOS Y MULTIMEDIA
# =====================================================
STATIC_URL = '/static/'

if DEBUG:
    STATICFILES_DIRS = [BASE_DIR / 'Modulos' / 'Facturacion' / 'static']
    STATIC_ROOT = BASE_DIR / 'staticfiles_dev'
else:
    STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# 📦 Archivos de usuario (PDF, imágenes, etc.)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# =====================================================
# LOGIN / LOGOUT
# =====================================================
LOGIN_REDIRECT_URL = 'menu_principal'
LOGOUT_REDIRECT_URL = 'login'
LOGIN_URL = 'login'

import os

# =====================================================
# CONFIGURACIÓN DE CORREO - BREVO SMTP
# =====================================================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp-relay.brevo.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# 🔹 Estos dos datos vienen de tu panel de Brevo
EMAIL_HOST_USER = "9b0157001@smtp-brevo.com"   # Tu usuario SMTP (ver en Brevo)
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")

# 🔹 Este será el correo que aparecerá como remitente
DEFAULT_FROM_EMAIL = "manuelito2327@gmail.com"

EMAIL_TIMEOUT = 30



# =====================================================
# SEGURIDAD PARA RENDER
# =====================================================
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_TRUSTED_ORIGINS = ['https://*.onrender.com']

# =====================================================
# OTROS AJUSTES
# =====================================================
if DEBUG:
    import mimetypes
    mimetypes.add_type("text/css", ".css", True)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PISA_DEFAULT_CSS = os.path.join(BASE_DIR, 'static/css/factura01.css')



