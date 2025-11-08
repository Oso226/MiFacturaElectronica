#!/usr/bin/env bash
# build.sh — Render build script automático para Django

echo "📦 Instalando dependencias..."
pip install -r requirements.txt

echo "⚙️ Aplicando migraciones..."
python manage.py migrate --noinput

echo "🧱 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

echo "✅ Build completado correctamente."
