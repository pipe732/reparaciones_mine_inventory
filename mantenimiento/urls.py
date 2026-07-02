from django.urls import path
from . import views

app_name = "mantenimiento"

urlpatterns = [
    # Estado actual de las herramientas
    path(
        "estado-actual/",
        views.estado_actual_lista_view,
        name="estado_actual_lista",
    ),

    # Catálogo de Tipos de Estado
    path(
        "tipo-estado/",
        views.tipo_estado_lista_view,
        name="tipo_estado_lista",
    ),
    path(
        "tipo-estado/nuevo/",
        views.tipo_estado_nuevo_view,
        name="tipo_estado_nuevo",
    ),
    path(
        "tipo-estado/editar/<int:pk>/",
        views.tipo_estado_editar_view,
        name="tipo_estado_editar",
    ),

    # Catálogo de Tipos de Mantenimiento
    path(
        "tipo-mantenimiento/",
        views.tipo_mantenimiento_lista_view,
        name="tipo_mantenimiento_lista",
    ),
    path(
        "tipo-mantenimiento/crear/",
        views.tipo_mantenimiento_crear_view,
        name="tipo_mantenimiento_crear",
    ),
    path(
        "tipo-mantenimiento/editar/<int:pk>/",
        views.tipo_mantenimiento_editar_view,
        name="tipo_mantenimiento_editar",
    ),

    # Gestión de Mantenimientos
    path(
        "lista/",
        views.mantenimiento_lista_view,
        name="mantenimiento_lista",
    ),
    path(
        "detalle/<int:pk>/",
        views.mantenimiento_detalle_view,
        name="mantenimiento_detalle",
    ),
]
