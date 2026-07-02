from django.contrib import admin

from .models import (
    CategoriaHerramienta,
    Herramienta,
    Inventario,
    Proveedor,
    Movimiento,
    DetalleMovimiento,
)

admin.site.register(CategoriaHerramienta)
admin.site.register(Herramienta)
admin.site.register(Inventario)
admin.site.register(Proveedor)
admin.site.register(Movimiento)
admin.site.register(DetalleMovimiento)
