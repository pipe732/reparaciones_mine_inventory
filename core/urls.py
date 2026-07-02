from django.contrib import admin
from django.urls import path, include
from usuario.views import login_view

globals()["urlpatterns"] = [
    path("admin/", admin.site.urls),
    path("", login_view, name="login"),
    # path(
    #     "home/", include("pagina_principal.urls")
    # ),  # Redirige a la página principal o dashboard de administrador
    # path("devoluciones/", include("devoluciones.urls")),
    path("usuario/", include("usuario.urls")),
    path("prestamos/", include("prestamo.urls")),
    path("inventario/", include("inventario.urls")),
    path("almacen/", include("almacen.urls")),
    path("mantenimiento/", include("mantenimiento.urls")),
    # path("reportes/", include("reportes.urls")),
    # path("configuracion/", include("configuracion.urls")),
]
