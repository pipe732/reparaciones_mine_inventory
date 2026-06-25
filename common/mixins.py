from functools import wraps
from django.shortcuts import redirect


def sesion_requerida(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get("usuario_documento"):
            return redirect("login")
        return view_func(request, *args, **kwargs)

    return _wrapped_view
