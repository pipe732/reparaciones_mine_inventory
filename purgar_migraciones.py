import os

# Apps del proyecto. Si agregar app nueva, sumarla aquí.
APPS = ["almacen", "inventario", "mantenimiento", "prestamo", "usuario"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def purgar_migraciones():
    total_borrados = 0
    for app in APPS:
        carpeta = os.path.join(BASE_DIR, app, "migrations")
        if not os.path.isdir(carpeta):
            print(f"Aviso: {app} no tiene carpeta migrations.")
            continue

        # Borrar también __pycache__ de migrations, o quedar .pyc viejo
        # apuntando a migración ya borrada y Django confundirse.
        pycache = os.path.join(carpeta, "__pycache__")
        if os.path.isdir(pycache):
            for f in os.listdir(pycache):
                os.remove(os.path.join(pycache, f))
            os.rmdir(pycache)

        borrados_app = 0
        for archivo in os.listdir(carpeta):
            # Mantener __init__.py. Sin él, Django dejar de ver la
            # carpeta como paquete y la app quedar como "no migrations".
            if archivo == "__init__.py":
                continue
            if archivo.endswith(".py") or archivo.endswith(".pyc"):
                os.remove(os.path.join(carpeta, archivo))
                borrados_app += 1

        total_borrados += borrados_app
        print(f"Migraciones purgadas: {app} ({borrados_app} archivo(s)).")

    print(f"\nListo. {total_borrados} archivo(s) de migración borrados en total.")
    print("Siguiente paso: python manage.py makemigrations && python manage.py migrate")


if __name__ == "__main__":
    confirmar = input(
        "Esto borrar TODAS las migraciones de las apps del proyecto. "
        "¿Continuar? (s/n): "
    ).strip().lower()
    if confirmar == "s":
        purgar_migraciones()
    else:
        print("Cancelado. No se borró nada.")