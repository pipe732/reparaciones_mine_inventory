from django.db import models

from inventario.models import Herramienta
from usuario.models import Usuario


class Prestamo(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        APROBADO = "APROBADO", "Aprobado"
        RECHAZADO = "RECHAZADO", "Rechazado"
        DEVUELTO = "DEVUELTO", "Devuelto"

    id_prestamo = models.AutoField(primary_key=True)
    herramienta = models.ForeignKey(
        Herramienta,
        on_delete=models.PROTECT,
        db_column="id_herramienta",
        related_name="prestamos",
    )
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        db_column="numero_documento",
        related_name="prestamos",
    )
    id_estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.PENDIENTE
    )
    observaciones = models.TextField(blank=True, null=True)
    fecha_solicitud = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "prestamo"
        verbose_name = "Préstamo"
        verbose_name_plural = "Préstamos"

    def __str__(self):
        return f"Préstamo #{self.id_prestamo} - {self.usuario.nombre_completo}"


class DetallePrestamo(models.Model):
    id_detalle_prestamo = models.AutoField(primary_key=True)
    prestamo = models.ForeignKey(
        Prestamo,
        on_delete=models.CASCADE,
        db_column="id_prestamo",
        related_name="detalles",
    )
    herramienta = models.ForeignKey(
        Herramienta,
        on_delete=models.PROTECT,
        db_column="id_herramienta",
        related_name="detalles_prestamo",
    )
    cantidad = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "detalle_prestamo"
        verbose_name = "Detalle de préstamo"
        verbose_name_plural = "Detalles de préstamo"

    def __str__(self):
        return f"Detalle préstamo #{self.id_detalle_prestamo}"


class DevolucionHerramienta(models.Model):
    id_devolucion_herramienta = models.AutoField(primary_key=True)
    detalle_prestamo = models.ForeignKey(
        DetallePrestamo,
        on_delete=models.CASCADE,
        db_column="id_detalle_prestamo",
        related_name="devoluciones",
    )
    herramienta = models.ForeignKey(
        Herramienta,
        on_delete=models.PROTECT,
        db_column="id_herramienta",
        related_name="devoluciones",
    )
    observaciones = models.TextField(blank=True, null=True)
    fecha_devolucion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "devolucion_herramienta"
        verbose_name = "Devolución de herramienta"
        verbose_name_plural = "Devoluciones de herramienta"

    def __str__(self):
        return f"Devolución #{self.id_devolucion_herramienta}"
