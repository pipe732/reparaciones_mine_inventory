from django.test import TestCase
from almacen.models import Almacen, Estante

class AlmacenModelTests(TestCase):
    def test_crear_almacen_exito(self):
        almacen = Almacen.objects.create(
            nombre="Almacén Principal",
            ubicacion="Bloque A",
            detalles="Almacén de herramientas",
            capacidad=100
        )
        self.assertEqual(almacen.nombre, "Almacén Principal")
        self.assertEqual(almacen.ubicacion, "Bloque A")

    def test_almacen_str(self):
        almacen = Almacen.objects.create(nombre="Almacén Temporal")
        self.assertEqual(str(almacen), "Almacén Temporal")

    def test_almacen_capacidad_nula(self):
        almacen = Almacen.objects.create(nombre="Almacén Capacidad Ilimitada")
        self.assertIsNone(almacen.capacidad)

    def test_almacen_detalles_nulos(self):
        almacen = Almacen.objects.create(nombre="Almacén Sin Detalles")
        self.assertIsNone(almacen.detalles)


class EstanteModelTests(TestCase):
    def setUp(self):
        self.almacen = Almacen.objects.create(
            nombre="Almacén Central",
            ubicacion="Bloque B",
            capacidad=50
        )

    def test_crear_estante_exito(self):
        estante = Estante.objects.create(
            codigo="EST-001",
            detalles="Estante de repuestos",
            capacidad=10,
            almacen=self.almacen
        )
        self.assertEqual(estante.codigo, "EST-001")
        self.assertEqual(estante.almacen, self.almacen)

    def test_estante_str(self):
        estante = Estante.objects.create(
            codigo="EST-002",
            almacen=self.almacen
        )
        self.assertEqual(str(estante), "EST-002")

    def test_estante_capacidad_nula(self):
        estante = Estante.objects.create(
            codigo="EST-003",
            almacen=self.almacen
        )
        self.assertIsNone(estante.capacidad)

    def test_relacion_almacen_estantes(self):
        estante1 = Estante.objects.create(
            codigo="EST-004",
            almacen=self.almacen
        )
        estante2 = Estante.objects.create(
            codigo="EST-005",
            almacen=self.almacen
        )
        self.assertEqual(self.almacen.estantes.count(), 2)
        self.assertIn(estante1, self.almacen.estantes.all())
        self.assertIn(estante2, self.almacen.estantes.all())
