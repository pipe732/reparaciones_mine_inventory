import os
import sys
import subprocess
from datetime import timedelta

from django.utils import timezone

APPS = ["almacen", "inventario", "mantenimiento", "prestamo", "usuario"]
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


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
    subprocess.run([sys.executable, manage_py, "migrate", "--noinput"], check=True)


def asegurar_columnas_compatibles():
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute("ALTER TABLE almacen ADD COLUMN IF NOT EXISTS detalles text")
        cursor.execute("ALTER TABLE almacen ADD COLUMN IF NOT EXISTS capacidad integer")
        cursor.execute("ALTER TABLE almacen ADD COLUMN IF NOT EXISTS fecha_creacion timestamp with time zone")
        cursor.execute("ALTER TABLE estante ADD COLUMN IF NOT EXISTS detalles text")
        cursor.execute("ALTER TABLE estante ADD COLUMN IF NOT EXISTS capacidad integer")
        cursor.execute("ALTER TABLE estante ADD COLUMN IF NOT EXISTS fecha_creacion timestamp with time zone")


def poblar_datos():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    import django
    django.setup()

    from django.contrib.auth.models import User
    from django.db import connection
    from almacen.models import Almacen, Estante
    from inventario.models import (
        CategoriaHerramienta,
        Herramienta,
        Inventario,
        Proveedor,
        Movimiento,
        DetalleMovimiento,
    )
    from mantenimiento.models import Mantenimiento, DetalleMantenimiento, BitacoraEstado
    from prestamo.models import Prestamo, DetallePrestamo, DevolucionHerramienta
    from usuario.models import Usuario

    def borrar_tablas():
        with connection.cursor() as cursor:
            cursor.execute("SET CONSTRAINTS ALL DEFERRED")

        for model in [
            DetalleMovimiento,
            Movimiento,
            DevolucionHerramienta,
            DetallePrestamo,
            Prestamo,
            BitacoraEstado,
            DetalleMantenimiento,
            Mantenimiento,
            Inventario,
            Herramienta,
            CategoriaHerramienta,
            Proveedor,
            Usuario,
            User,
        ]:
            try:
                model.objects.all().delete()
            except Exception as exc:
                print(f"Advertencia al borrar {model.__name__}: {exc}")

        try:
            Estante.objects.all().delete()
        except Exception as exc:
            print(f"Advertencia al borrar Estante: {exc}")

        try:
            Almacen.objects.all().delete()
        except Exception as exc:
            print(f"Advertencia al borrar Almacen: {exc}")

    asegurar_columnas_compatibles()
    borrar_tablas()

    almacen1 = Almacen.objects.create(nombre="Almacén Norte", ubicacion="Bodega 1")
    almacen2 = Almacen.objects.create(nombre="Almacén Sur", ubicacion="Bodega 2")

    estante1 = Estante.objects.create(codigo="E-101", almacen=almacen1)
    estante2 = Estante.objects.create(codigo="E-202", almacen=almacen1)
    estante3 = Estante.objects.create(codigo="E-303", almacen=almacen2)

    categoria1 = CategoriaHerramienta.objects.create(descripcion="Eléctricas", tipo_herramienta="Eléctrica")
    categoria2 = CategoriaHerramienta.objects.create(descripcion="Manuales", tipo_herramienta="Manual")
    categoria3 = CategoriaHerramienta.objects.create(descripcion="Seguridad", tipo_herramienta="Protección")

    proveedores = [
        Proveedor.objects.create(nit_proveedor="900001234", telefono_contacto="3001112222", correo_proveedor="proveedor1@test.com", descripcion="Proveedor A"),
        Proveedor.objects.create(nit_proveedor="900001235", telefono_contacto="3001113333", correo_proveedor="proveedor2@test.com", descripcion="Proveedor B"),
    ]

    herramientas = [
        Herramienta.objects.create(codigo_sku="SKU-001", categoria_herramienta=categoria1, nombre_herramienta="Taladro inalámbrico", descripcion="Taladro de 18V", disponibilidad=True),
        Herramienta.objects.create(codigo_sku="SKU-002", categoria_herramienta=categoria2, nombre_herramienta="Llave inglesa", descripcion="Llave de 12 pulgadas", disponibilidad=True),
        Herramienta.objects.create(codigo_sku="SKU-003", categoria_herramienta=categoria3, nombre_herramienta="Casco de seguridad", descripcion="Casco industrial", disponibilidad=False),
        Herramienta.objects.create(codigo_sku="SKU-004", categoria_herramienta=categoria1, nombre_herramienta="Multímetro", descripcion="Medición eléctrica", disponibilidad=True),
    ]

    inventarios = []
    for herramienta, estante, cantidad in zip(herramientas, [estante1, estante2, estante3, estante1], [10, 15, 8, 5]):
        inventarios.append(Inventario.objects.create(herramienta=herramienta, estante=estante, cantidad=cantidad, responsable="Carlos Mendoza", observaciones="Stock inicial"))

    for inv, proveedor in zip(inventarios[:2], proveedores):
        movimiento = Movimiento.objects.create(inventario=inv, proveedor=proveedor, cantidad=3, tipo_de_movimiento="Entrada")
        DetalleMovimiento.objects.create(movimiento=movimiento, inventario=inv, descripcion="Ingreso de prueba")

    movimiento_error = Movimiento.objects.create(inventario=inventarios[2], proveedor=None, cantidad=1, tipo_de_movimiento="Salida")
    DetalleMovimiento.objects.create(movimiento=movimiento_error, inventario=inventarios[2], descripcion="Movimiento con datos incompletos")

    usuarios = []
    admin_user = User.objects.create_user(username="admin", password="@dmin123", email="admin@test.com")
    admin_user.is_superuser = True
    admin_user.is_staff = True
    admin_user.save()
    admin_usuario = Usuario.objects.create(
        numero_documento="0000000000",
        user=admin_user,
        id_rol="ADMIN",
        nombre_completo="Administrador Principal",
        correo="admin@test.com",
        telefono="3000000000",
        tipo_documento="CC",
    )
    usuarios.append(admin_usuario)

    for idx, (username, rol, nombre) in enumerate([
        ("instr1", "INSTRUCTOR", "Luis Pérez"),
        ("apr1", "APRENDIZ", "Sofía Torres"),
        ("alm1", "ALMACENISTA", "Mateo Ruiz"),
    ], start=2):
        user = User.objects.create_user(username=username, password="12345678", email=f"user{idx}@test.com")
        usuario = Usuario.objects.create(
            numero_documento=f"100000{idx}",
            user=user,
            id_rol=rol,
            nombre_completo=nombre,
            correo=f"{username}@test.com",
            telefono=f"30000000{idx}",
            tipo_documento="CC",
        )
        usuarios.append(usuario)

    prestamo = Prestamo.objects.create(herramienta=herramientas[0], usuario=usuarios[1], id_estado="PENDIENTE", observaciones="Préstamo para capacitación")
    DetallePrestamo.objects.create(prestamo=prestamo, herramienta=herramientas[0], cantidad=2)

    prestamo_aprobado = Prestamo.objects.create(herramienta=herramientas[1], usuario=usuarios[2], id_estado="APROBADO", observaciones="Préstamo aprobado")
    DetallePrestamo.objects.create(prestamo=prestamo_aprobado, herramienta=herramientas[1], cantidad=1)

    prestamo_devuelto = Prestamo.objects.create(herramienta=herramientas[3], usuario=usuarios[3], id_estado="DEVUELTO", observaciones="Herramienta devuelta")
    detalle = DetallePrestamo.objects.create(prestamo=prestamo_devuelto, herramienta=herramientas[3], cantidad=1)
    DevolucionHerramienta.objects.create(detalle_prestamo=detalle, herramienta=herramientas[3], observaciones="Todo en orden")

    mantenimiento = Mantenimiento.objects.create(
        herramienta=herramientas[0],
        id_producto="PRD-100",
        tipo_mantenimiento="Preventivo",
        descripcion="Revisión general",
        fecha_ingreso=timezone.now() - timedelta(days=5),
        fecha_salida=timezone.now(),
    )
    DetalleMantenimiento.objects.create(mantenimiento=mantenimiento, accion_realizada="Cambio de batería", materiales_usados="Batería 18V")
    BitacoraEstado.objects.create(mantenimiento=mantenimiento, descripcion="Revisado", estado="Completado", nivel_estado="OK")

    mantenimiento2 = Mantenimiento.objects.create(
        herramienta=herramientas[2],
        id_producto="PRD-101",
        tipo_mantenimiento="Correctivo",
        descripcion="Herramienta en mal estado",
        fecha_ingreso=timezone.now() - timedelta(days=1),
        fecha_salida=None,
    )
    DetalleMantenimiento.objects.create(mantenimiento=mantenimiento2, accion_realizada="Sin solución", materiales_usados="Ninguno")
    BitacoraEstado.objects.create(mantenimiento=mantenimiento2, descripcion="Pendiente de revisión", estado="En proceso", nivel_estado="ALERTA")

    print("Datos de prueba generados con éxito.")


if __name__ == "__main__":
    borrar_bd()
    limpiar_migraciones()
    correr_migraciones()
    poblar_datos()
    print("\nListo. BD limpia. Migraciones frescas y datos de prueba cargados.")
    print("Opcional: python manage.py createsuperuser")