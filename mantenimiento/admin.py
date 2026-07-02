from django.contrib import admin

from .models import Mantenimiento, DetalleMantenimiento, BitacoraEstado, TipoEstado, TipoMantenimiento

admin.site.register(Mantenimiento)
admin.site.register(DetalleMantenimiento)
admin.site.register(BitacoraEstado)
admin.site.register(TipoEstado)
admin.site.register(TipoMantenimiento)
