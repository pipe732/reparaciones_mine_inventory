from django.db import models

from inventario.models import Herramienta


class Mantenimiento(models.Model):
    id_mantenimiento = models.AutoField(primary_key=True)
    herramienta = models.ForeignKey(
        Herramienta,
        on_delete=models.CASCADE,
        db_column="id_herramienta",
        related_name="mantenimientos",
    )
    # El MER muestra "id_producto" repetido dos veces. Se deja un solo
    # campo para evitar duplicidad de columna; si en realidad son dos
    # referencias distintas, avisa y se separan en dos campos.
    id_producto = models.CharField(max_length=50, blank=True, null=True)
    tipo_mantenimiento = models.CharField(max_length=100)
    descripcion = models.TextField()
    fecha_ingreso = models.DateTimeField()
    fecha_salida = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "mantenimiento"
        verbose_name = "Mantenimiento"
        verbose_name_plural = "Mantenimientos"

    def __str__(self):
        return f"Mantenimiento #{self.id_mantenimiento} - {self.herramienta}"


class DetalleMantenimiento(models.Model):
    id_detalle_mantenimiento = models.AutoField(primary_key=True)
    mantenimiento = models.ForeignKey(
        Mantenimiento,
        on_delete=models.CASCADE,
        db_column="id_mantenimiento",
        related_name="detalles",
    )
    accion_realizada = models.TextField()
    materiales_usados = models.TextField(blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "detalle_mantenimiento"
        verbose_name = "Detalle de mantenimiento"
        verbose_name_plural = "Detalles de mantenimiento"

    def __str__(self):
        return f"Detalle mantenimiento #{self.id_detalle_mantenimiento}"


class BitacoraEstado(models.Model):
    id_bitacora_estado = models.AutoField(primary_key=True)
    mantenimiento = models.ForeignKey(
        Mantenimiento,
        on_delete=models.CASCADE,
        db_column="id_mantenimiento",
        related_name="bitacoras",
    )
    descripcion = models.TextField()
    estado = models.CharField(max_length=100)
    nivel_estado = models.CharField(max_length=50)

    class Meta:
        db_table = "bitacora_estado"
        verbose_name = "Bitácora de estado"
        verbose_name_plural = "Bitácoras de estado"

    def __str__(self):
        return f"Bitácora #{self.id_bitacora_estado} - {self.estado}"


class TipoEstado(models.Model):
    id_tipo_estado = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, unique=True)
    nivel = models.CharField(max_length=50)

    class Meta:
        db_table = "tipo_estado"
        verbose_name = "Tipo de Estado"
        verbose_name_plural = "Tipos de Estado"

    def __str__(self):
        return self.nombre


class TipoMantenimiento(models.Model):
    id_tipo_mantenimiento = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "tipo_mantenimiento"
        verbose_name = "Tipo de Mantenimiento"
        verbose_name_plural = "Tipos de Mantenimiento"

    def __str__(self):
        return self.nombre

