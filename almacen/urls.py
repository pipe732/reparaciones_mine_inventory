from django.urls import path
from . import views

urlpatterns = [
    path("almacenes/", views.almacenes_view, name="almacenes"),
    path(
        "almacenes/<int:pk>/",
        views.detalle_almacen_view,
        name="detalle_almacen",
    ),
    path("estantes/", views.estantes_view, name="estantes"),
]
