from django.db import models

from almacen.models import Estante


class CategoriaHerramienta(models.Model):
    categoria_herramienta_id = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=150)
    tipo_herramienta = models.CharField(max_length=100)
    # En el MER aparece como "id_herramienta" suelto dentro de
    # categoria_herramienta. La relación real categoría -> herramienta
    # (cardinalidad 1-N, "clasifica") se modela desde Herramienta más
    # abajo, así que este campo queda como referencia auxiliar.
    id_herramienta = models.CharField(max_length=50, blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "categoria_herramienta"
        verbose_name = "Categoría de herramienta"
        verbose_name_plural = "Categorías de herramienta"

    def __str__(self):
        return self.descripcion


class Herramienta(models.Model):
    id_herramienta = models.AutoField(primary_key=True)
    codigo_sku = models.CharField(max_length=50, unique=True)
    categoria_herramienta = models.ForeignKey(
        CategoriaHerramienta,
        on_delete=models.PROTECT,
        db_column="categoria_herramienta_id",
        related_name="herramientas",
    )
    nombre_herramienta = models.CharField(max_length=150)
    descripcion = models.TextField()
    disponibilidad = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "herramienta"
        verbose_name = "Herramienta"
        verbose_name_plural = "Herramientas"

    def __str__(self):
        return f"{self.codigo_sku} - {self.nombre_herramienta}"


class Inventario(models.Model):
    id_inventario = models.AutoField(primary_key=True)
    herramienta = models.ForeignKey(
        Herramienta,
        on_delete=models.CASCADE,
        db_column="id_herramienta",
        related_name="inventarios",
    )
    estante = models.ForeignKey(
        Estante,
        on_delete=models.CASCADE,
        db_column="id_estante",
        related_name="inventarios",
    )
    cantidad = models.PositiveIntegerField(default=0)
    responsable = models.CharField(max_length=150)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "inventario"
        verbose_name = "Inventario"
        verbose_name_plural = "Inventario"

    def __str__(self):
        nombre = self.herramienta.nombre_herramienta
        return f"Inventario #{self.id_inventario} - {nombre}"


class Proveedor(models.Model):
    id_proveedor = models.AutoField(primary_key=True)
    nit_proveedor = models.CharField(max_length=30, unique=True)
    telefono_contacto = models.CharField(max_length=30)
    correo_proveedor = models.EmailField()
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "proveedor"
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"

    def __str__(self):
        return self.nit_proveedor


class Movimiento(models.Model):
    id_movimiento = models.AutoField(primary_key=True)
    inventario = models.ForeignKey(
        Inventario,
        on_delete=models.CASCADE,
        db_column="id_inventario",
        related_name="movimientos",
    )
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.SET_NULL,
        db_column="id_proveedor",
        related_name="movimientos",
        blank=True,
        null=True,
    )
    cantidad = models.PositiveIntegerField()
    tipo_de_movimiento = models.CharField(max_length=50)
    fecha_movimiento = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "movimientos"
        verbose_name = "Movimiento"
        verbose_name_plural = "Movimientos"

    def __str__(self):
        return f"Movimiento #{self.id_movimiento} ({self.tipo_de_movimiento})"


class DetalleMovimiento(models.Model):
    id_detalle_movimiento = models.AutoField(primary_key=True)
    movimiento = models.ForeignKey(
        Movimiento,
        on_delete=models.CASCADE,
        db_column="id_movimiento",
        related_name="detalles",
    )
    inventario = models.ForeignKey(
        Inventario,
        on_delete=models.CASCADE,
        db_column="id_inventario",
        related_name="detalles_movimiento",
    )
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "detalle_movimientos"
        verbose_name = "Detalle de movimiento"
        verbose_name_plural = "Detalles de movimiento"

    def __str__(self):
        return f"Detalle movimiento #{self.id_detalle_movimiento}"
