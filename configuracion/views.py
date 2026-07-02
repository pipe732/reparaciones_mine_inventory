import re
from pathlib import Path
from urllib.parse import urlparse

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET

from usuario.decorators import admin_required

from .models import ConfiguracionSistema

ENV_PATH = Path(__file__).resolve().parent.parent / '.env'


def _leer_env(clave: str, default: str = '') -> str:
    """Lee el valor actual de una clave en el .env."""
    if not ENV_PATH.exists():
        return default
    contenido = ENV_PATH.read_text(encoding='utf-8')
    patron = re.compile(rf'^{re.escape(clave)}\s*=\s*(.+)$', re.MULTILINE)
    match = patron.search(contenido)
    return match.group(1).strip() if match else default


def _actualizar_env(clave: str, valor: str):
    """Reemplaza o agrega una clave en el archivo .env."""
    if not ENV_PATH.exists():
        ENV_PATH.write_text(f'{clave}={valor}\n', encoding='utf-8')
        return

    contenido = ENV_PATH.read_text(encoding='utf-8')
    patron = re.compile(rf'^{re.escape(clave)}\s*=.*$', re.MULTILINE)

    if patron.search(contenido):
        nuevo = patron.sub(f'{clave}={valor}', contenido)
    else:
        nuevo = contenido.rstrip('\n') + f'\n{clave}={valor}\n'

    ENV_PATH.write_text(nuevo, encoding='utf-8')


def _forzar_recarga():
    """Toca settings.py y views.py para forzar recarga del runserver."""
    base = Path(__file__).resolve().parent.parent
    for path in [
        base / 'core' / 'settings.py',
        Path(__file__).resolve(),
    ]:
        if path.exists():
            path.touch()


@admin_required
def configuracion_view(request):
    almacenamiento_actual = _leer_env('DB_ENGINE', default='local').strip().lower() or 'local'
    database_url_actual = _leer_env('DATABASE_URL', default='').strip()

    if request.method == 'POST':
        almacenamiento = request.POST.get('almacenamiento', 'local').strip().lower() or 'local'
        database_url = request.POST.get('database_url', '').strip()

        _actualizar_env('DB_ENGINE', almacenamiento)
        if database_url:
            _actualizar_env('DATABASE_URL', database_url)
        else:
            _actualizar_env('DATABASE_URL', '')
        _forzar_recarga()

        request.session.flush()

        nombre_bd = 'Local (SQLite)' if almacenamiento == 'local' else 'Nube (Neon PostgreSQL)'
        messages.success(
            request,
            f'Base de datos cambiada a {nombre_bd}. '
            'Espera unos segundos e inicia sesión nuevamente.'
        )
        return redirect('login')

    class Config:
        pass

    config = Config()
    config.almacenamiento = almacenamiento_actual
    config.database_url = database_url_actual

    context = {'config': config}
    return render(request, 'configuracion.html', context)


@admin_required
@require_GET
def probar_conexion_neon(request):
    try:
        import psycopg2
    except ImportError as exc:
        return JsonResponse({'ok': False, 'error': f'psycopg2 no instalado: {exc}'})

    try:
        database_url = _leer_env('DATABASE_URL', default='').strip()
        if database_url:
            parsed = urlparse(database_url)
            conn = psycopg2.connect(
                dbname=parsed.path.lstrip('/'),
                user=parsed.username,
                password=parsed.password,
                host=parsed.hostname,
                port=parsed.port or 5432,
                connect_timeout=5,
                sslmode='require',
            )
        else:
            conn = psycopg2.connect(
                dbname=_leer_env('DB_NAME', default=''),
                user=_leer_env('DB_USER', default=''),
                password=_leer_env('DB_PASSWORD', default=''),
                host=_leer_env('DB_HOST', default=''),
                port=_leer_env('DB_PORT', default='5432'),
                connect_timeout=5,
                sslmode='require',
            )
        conn.close()
        return JsonResponse({'ok': True})
    except Exception as exc:
        return JsonResponse({'ok': False, 'error': str(exc)})