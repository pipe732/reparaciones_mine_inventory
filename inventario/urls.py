from django.urls import path
from . import views

globals()["app_name"] = "inventario"

globals()["urlpatterns"] = [
    path("", views.listado_herramientas, name="inventario"),
    path("<int:pk>/", views.detalle_herramienta, name="detalle_herramienta"),
    path("crear/", views.crear_herramienta, name="crear_herramienta"),
    path("editar/<int:pk>/", views.editar_herramienta, name="editar_herramienta"),
    path("eliminar/<int:pk>/", views.eliminar_herramienta, name="eliminar_herramienta"),
]
