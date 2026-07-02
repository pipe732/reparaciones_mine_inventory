from django.contrib import admin

from .models import Prestamo, DetallePrestamo, DevolucionHerramienta

admin.site.register(Prestamo)
admin.site.register(DetallePrestamo)
admin.site.register(DevolucionHerramienta)
