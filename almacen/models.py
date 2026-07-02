from django.db import models


class Almacen(models.Model):
    id_almacen = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=150, db_column='nombre_almacen')
    ubicacion = models.CharField(max_length=255, blank=True, null=True)
    detalles = models.TextField(blank=True, null=True)
    capacidad = models.IntegerField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "almacen"
        verbose_name = "Almacén"
        verbose_name_plural = "Almacenes"

    def __str__(self):
        return self.nombre


class Estante(models.Model):
    id_estante = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=50, unique=True, db_column='codigo_estante')
    detalles = models.TextField(blank=True, null=True)
    capacidad = models.IntegerField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
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
        return self.codigo
