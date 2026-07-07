from django.urls import path

from . import views

app_name = "mantenimiento"

urlpatterns = [
    # ── Estado actual de herramientas ──────────────────────────
    path(
        "estado-actual/",
        views.estado_actual_lista_view,
        name="estado_actual_lista",
    ),

    # ── Historial por herramienta / producto ───────────────────
    path(
        "historial/<int:pk>/",
        views.historial_producto_view,
        name="historial_producto",
    ),

    # ── Catálogo: Tipos de Estado ──────────────────────────────
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

    # ── Catálogo: Tipos de Mantenimiento ───────────────────────
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
    path(
        "tipo-mantenimiento/inactivar/<int:pk>/",
        views.tipo_mantenimiento_inactivar_view,
        name="tipo_mantenimiento_inactivar",
    ),
    path(
        "tipo-mantenimiento/eliminar/<int:pk>/",
        views.tipo_mantenimiento_confirmar_view,
        name="tipo_mantenimiento_eliminar",
    ),

    # ── Gestión de Mantenimientos ──────────────────────────────
    path(
        "",
        views.mantenimiento_lista_view,
        name="mantenimiento_lista",
    ),
    path(
        "nuevo/",
        views.mantenimiento_crear_view,
        name="mantenimiento_crear",
    ),
    path(
        "<int:pk>/",
        views.mantenimiento_detalle_view,
        name="mantenimiento_detalle",
    ),
    path(
        "<int:pk>/editar/",
        views.mantenimiento_editar_view,
        name="mantenimiento_editar",
    ),

    # ── Acción POST: agregar detalle desde vista detalle ───────
    path(
        "<int:pk>/detalle/crear/",
        views.detalle_mantenimiento_crear_view,
        name="detalle_mantenimiento_crear",
    ),
]
