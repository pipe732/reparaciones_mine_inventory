import os
import sys
import shutil
import subprocess

# Apps de tu proyecto. Ya puestas, no tocar.
APPS = ["almacen", "inventario", "mantenimiento", "prestamo", "usuario"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def borrar_bd():
    db_path = os.path.join(BASE_DIR, "db.sqlite3")
    if os.path.exists(db_path):
        os.remove(db_path)
        print("BD borrada.")
    else:
        print("No había BD.")

def limpiar_migraciones():
    for app in APPS:
        carpeta = os.path.join(BASE_DIR, app, "migrations")
        if not os.path.isdir(carpeta):
            print(f"Aviso: {app} no tiene carpeta migrations.")
            continue
        for archivo in os.listdir(carpeta):
            # Mantener __init__.py. Django necesita ese archivo.
            if archivo == "__init__.py":
                continue
            if archivo.endswith(".py") or archivo.endswith(".pyc"):
                os.remove(os.path.join(carpeta, archivo))
        print(f"Migraciones limpias: {app}")

def correr_migraciones():
    manage_py = os.path.join(BASE_DIR, "manage.py")
    print("Generando migraciones nuevas...")
    subprocess.run([sys.executable, manage_py, "makemigrations"], check=True)
    print("Aplicando migraciones...")
    subprocess.run([sys.executable, manage_py, "migrate"], check=True)

if __name__ == "__main__":
    borrar_bd()
    limpiar_migraciones()
    correr_migraciones()
    print("\nListo. BD limpia. Migraciones frescas.")
    print("Opcional: python manage.py createsuperuser")