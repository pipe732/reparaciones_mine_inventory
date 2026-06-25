from django.db import models


class Almacen(models.Model):
    id_almacen = models.AutoField(primary_key=True)
    nombre_almacen = models.CharField(max_length=150)
    ubicacion = models.CharField(max_length=255)

    class Meta:
        db_table = "almacen"
        verbose_name = "Almacén"
        verbose_name_plural = "Almacenes"

    def __str__(self):
        return self.nombre_almacen


class Estante(models.Model):
    id_estante = models.AutoField(primary_key=True)
    codigo_estante = models.CharField(max_length=50, unique=True)
    almacen = models.ForeignKey(
        Almacen,
        on_delete=models.CASCADE,
        db_column="id_almacen",
        related_name="estantes",
    )

    class Meta:
        db_table = "estante"
        verbose_name = "Estante"
        verbose_name_plural = "Estantes"

    def __str__(self):
        return self.codigo_estante
