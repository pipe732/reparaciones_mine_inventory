from functools import wraps
from django.shortcuts import redirect


def login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get("usuario_documento"):
            return redirect("login")
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get("usuario_documento"):
            return redirect("login")
        rol = (request.session.get("usuario_rol") or "").strip().lower()
        if rol not in ("administrador", "admin"):
            return redirect("home_usuario")
        return view_func(request, *args, **kwargs)

    return _wrapped_view
