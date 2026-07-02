from django.urls import path
from . import views

# Note: Commented out app_name to register urls globally so that the templates' non-namespaced url resolutions (e.g. {% url 'prestamo' %}) work.
# app_name = "prestamo"

globals()["urlpatterns"] = [
    path("", views.prestamo_view, name="prestamo"),
    path("usuario/", views.prestamo_usuario_view, name="prestamo_usuario"),
    path(
        "instructores/", views.prestamo_instructores_view, name="prestamo_instructores"
    ),
    path("devoluciones/", views.devoluciones_view, name="devoluciones"),
    path("<int:pk>/json/", views.prestamo_detalle_json, name="prestamo_detalle_json"),
]
