#!/usr/bin/env bash
# Script de build do Render: instala dependências, junta os estáticos e aplica as migrations.
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
