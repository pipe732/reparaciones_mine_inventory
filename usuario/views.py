import re
import csv
import time
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.core.exceptions import ValidationError

from usuario.decorators import admin_required, login_required

from .models import Usuario
from common.mixins import sesion_requerida
from prestamo.models import Prestamo

globals()["logger"] = logging.getLogger("usuario.views")

globals()["DOC_RULES"] = {
    "CC": re.compile(r"^\d{6,10}$"),
    "CE": re.compile(r"^[A-Za-z0-9]{6,12}$"),
    "PP": re.compile(r"^[A-Za-z0-9]{5,9}$"),
    "TI": re.compile(r"^\d{10,11}$"),
}
globals()["DOC_LABELS"] = {
    "CC": "Cédula de Ciudadanía",
    "CE": "Cédula de Extranjería",
    "PP": "Pasaporte",
    "TI": "Tarjeta de Identidad",
}
globals()["DOC_HINTS"] = {
    "CC": "La Cédula de Ciudadanía debe tener entre 6 y 10 dígitos.",
    "CE": (
        "La Cédula de Extranjería debe tener entre 6 y 12 caracteres alfanuméricos."
    ),
    "PP": "El Pasaporte debe tener entre 5 y 9 caracteres alfanuméricos.",
    "TI": "La Tarjeta de Identidad debe tener 10 u 11 dígitos.",
}
globals()["TIPOS_VALIDOS"] = set(DOC_RULES.keys())
globals()["ROLES_VALIDOS"] = [r[0] for r in Usuario.Rol.choices]
globals()["ROLES"] = [{"id": r[0], "nombre": r[1]} for r in Usuario.Rol.choices]


def _validar_documento(tipo, numero):
    if tipo not in TIPOS_VALIDOS:
        return "Tipo de documento no válido."
    if not DOC_RULES[tipo].match(numero):
        return DOC_HINTS[tipo]
    return None


# ─────────────────────────────────────────────────────────────
#  LOGIN
# ─────────────────────────────────────────────────────────────
def login_view(request):
    if request.session.get("usuario_documento"):
        return redirect("home")

    if request.method == "POST":
        tipo_documento = request.POST.get("tipo_documento", "").strip().upper()
        documento = request.POST.get("documento", "").strip()
        password = request.POST.get("password", "")

        campos_requeridos = {
            "Tipo de documento": tipo_documento,
            "Número de documento": documento,
            "Contraseña": password,
        }
        faltantes = [nombre for nombre, valor in campos_requeridos.items() if not valor]
        if faltantes:
            if len(faltantes) > 1:
                mensaje = (
                    "Faltan completar los siguientes campos: "
                    f"{', '.join(faltantes)}."
                )
            else:
                mensaje = f"Falta completar el campo: {faltantes[0]}."
            messages.error(request, mensaje)
            context = {
                "tipo_documento": tipo_documento,
                "documento": documento,
            }

            return render(request, "login.html", context)

        error_doc = _validar_documento(tipo_documento, documento)
        if error_doc:
            messages.error(request, error_doc)
            context = {
                "tipo_documento": tipo_documento,
                "documento": documento,
            }

            return render(request, "login.html", context)

        try:
            usuario = Usuario.objects.get(
                numero_documento=documento,
                tipo_documento=tipo_documento,
            )
        except Usuario.DoesNotExist:
            messages.error(request, "Documento o contraseña incorrectos.")
            context = {
                "tipo_documento": tipo_documento,
                "documento": documento,
            }

            return render(request, "login.html", context)

        if not check_password(password, usuario.user.password):
            messages.error(request, "Documento o contraseña incorrectos.")
            context = {
                "tipo_documento": tipo_documento,
                "documento": documento,
            }

            return render(request, "login.html", context)

        request.session["usuario_documento"] = usuario.numero_documento
        request.session["usuario_nombre"] = usuario.nombre_completo
        request.session["usuario_rol"] = usuario.id_rol
        request.session["usuario_tipo_documento"] = usuario.tipo_documento

        rol = usuario.id_rol.strip().lower()
        if rol in ("administrador", "instructor"):
            return redirect("home")
        return redirect("home_usuario")

    return render(request, "login.html")


# ─────────────────────────────────────────────────────────────
#  LOGOUT
# ─────────────────────────────────────────────────────────────
def logout_view(request):
    request.session.flush()
    return redirect(reverse("login"))


# ─────────────────────────────────────────────────────────────
#  REGISTRO
# ─────────────────────────────────────────────────────────────
def registro_view(request):
    ctx_base = {
        "roles": ROLES,
        "tipo_documento": "CC",
        "username": "",
        "email": "",
        "documento": "",
        "numero_ficha": "",
        "nombre_programa": "",
    }

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip().lower()
        tipo_documento = request.POST.get("tipo_documento", "").strip().upper()
        documento = request.POST.get("documento", "").strip()
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")
        numero_ficha = request.POST.get("numero_ficha", "").strip()
        nombre_programa = request.POST.get("nombre_programa", "").strip()
        rol_id = "Usuario"

        ctx = {
            **ctx_base,
            "username": username,
            "email": email,
            "tipo_documento": tipo_documento,
            "documento": documento,
            "numero_ficha": numero_ficha,
            "nombre_programa": nombre_programa,
        }

        if not all(
            [
                username,
                email,
                tipo_documento,
                documento,
                password1,
                password2,
            ]
        ):
            messages.error(request, "Completa todos los campos obligatorios.")
            return render(request, "registro.html", ctx)

        error_doc = _validar_documento(tipo_documento, documento)
        if error_doc:
            messages.error(request, error_doc)
            return render(request, "registro.html", ctx)

        if len(password1) < 8:
            messages.error(
                request,
                "La contraseña debe tener al menos " "8 caracteres.",
            )
            return render(request, "registro.html", ctx)

        if password1 != password2:
            messages.error(request, "Las contraseñas no coinciden.")
            return render(request, "registro.html", ctx)

        if Usuario.objects.filter(numero_documento=documento).exists():
            messages.error(
                request,
                "Ya existe un usuario con ese " "número de documento.",
            )
            return render(request, "registro.html", ctx)

        if Usuario.objects.filter(correo=email).exists():
            messages.error(request, "El correo ya está registrado.")
            return render(request, "registro.html", ctx)

        usuario = Usuario(
            numero_documento=documento,
            nombre_completo=username,
            correo=email,
            telefono="",
            tipo_documento=tipo_documento,
            password=make_password(password1),
            rol=rol_id,
            numero_ficha=numero_ficha,
            nombre_programa=nombre_programa,
        )

        try:
            usuario.full_clean()
        except ValidationError as e:
            messages.error(request, " ".join(e.messages))
            return render(request, "registro.html", ctx)

        usuario.save()

        request.session["usuario_documento"] = usuario.numero_documento
        request.session["usuario_nombre"] = usuario.nombre_completo
        request.session["usuario_rol"] = usuario.id_rol
        request.session["usuario_tipo_documento"] = usuario.tipo_documento

        if usuario.id_rol.strip().lower() in ("administrador", "admin", "instructor"):
            return redirect("home")
        return redirect("home_usuario")

    return render(request, "registro.html", ctx_base)


# ─────────────────────────────────────────────────────────────
#  OLVIDÓ CONTRASEÑA
# ─────────────────────────────────────────────────────────────
def olvido_contrasena_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()

        if not email:
            messages.error(request, "Ingresa tu correo electrónico.")
            return render(request, "olvido_contrasena.html")

        try:
            usuario = Usuario.objects.get(correo=email)
        except Usuario.DoesNotExist:
            # Mensaje genérico por seguridad
            messages.success(
                request, "Si el correo está registrado, recibirás un enlace."
            )
            return render(request, "olvido_contrasena.html")

        # Generar token y guardarlo en la base de datos (no en sesión)
        token = get_random_string(40)
        # usuario.reset_token = token
        # usuario.reset_token_expira = time.time() + 900
        # usuario.save(update_fields=["reset_token", "reset_token_expira"])

        uid = urlsafe_base64_encode(force_bytes(usuario.numero_documento))
        link = request.build_absolute_uri(
            reverse("nueva_contrasena", kwargs={"uid": uid, "token": token})
        )

        try:
            send_mail(
                subject="Recuperación de contraseña – SENA Centro Minero",
                message=(
                    f"Hola {usuario.nombre_completo},\n\n"
                    "Haz clic en el siguiente enlace para cambiar tu "
                    f"contraseña:\n\n{link}\n\n"
                    "Este enlace expira en 15 minutos.\n\n"
                    "Si no solicitaste esto, ignora este mensaje.\n\n"
                    "SENA – Centro Minero · Regional Boyacá"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            messages.success(
                request,
                "Te enviamos un enlace a tu correo. " "Tienes 15 minutos para usarlo.",
            )
        except Exception as e:
            # Registrar el error real en consola/logs para poder diagnosticarlo
            logger.error("Error al enviar correo de recuperación: %s", e)
            print(f"[ERROR CORREO] {e}")  # visible en la consola del servidor
            messages.error(request, f"No se pudo enviar el correo. Error: {e}")

    return render(request, "olvido_contrasena.html")


# ─────────────────────────────────────────────────────────────
#  NUEVA CONTRASEÑA
# ─────────────────────────────────────────────────────────────
def nueva_contrasena_view(request, uid, token):
    try:
        documento = force_str(urlsafe_base64_decode(uid))
        usuario = Usuario.objects.get(numero_documento=documento)
    except Exception:
        messages.error(request, "El enlace no es válido.")
        return redirect("olvido_contrasena")

    # Validar token guardado en base de datos
    # if (
    #     not usuario.reset_token
    #     or usuario.reset_token != token
    #     or time.time() > usuario.reset_token_expira
    # ):
    #     messages.error(
    #         request,
    #         "El enlace ya fue usado o expiró. " "Solicita uno nuevo.",
    #     )
    #     return redirect("olvido_contrasena")

    if request.method == "POST":
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")

        if len(password1) < 8:
            messages.error(
                request,
                "La contraseña debe tener al menos " "8 caracteres.",
            )
            return render(request, "nueva_contrasena.html")

        if password1 != password2:
            messages.error(request, "Las contraseñas no coinciden.")
            return render(request, "nueva_contrasena.html")

        usuario.user.set_password(password1)
        usuario.user.save()
        usuario.save(
            update_fields=[
                "reset_token",
                "reset_token_expira",
            ]
        )

        messages.success(
            request,
            "¡Contraseña actualizada! " "Ya puedes iniciar sesión.",
        )
        return redirect("login")

    return render(request, "nueva_contrasena.html")


# ─────────────────────────────────────────────────────────────
#  HOME
# ─────────────────────────────────────────────────────────────
@sesion_requerida
@login_required
def home_usuario_view(request):
    """Página principal para usuarios normales (aprendices, etc.)"""
    if not request.session.get("usuario_documento"):
        return redirect("login")

    usuario_doc = request.session.get("usuario_documento")
    usuario = Usuario.objects.get(numero_documento=usuario_doc)

    from prestamo.models import Prestamo

    prestamos = Prestamo.objects.filter(usuario=usuario)

    context = {
        "usuario": usuario,
        "prestamos": prestamos,
    }
    return render(request, "usuario/home_usuario.html", context)


def home_view(request):
    """Página principal - redirige según el rol"""
    if not request.session.get("usuario_documento"):
        return redirect("login")

    rol = (request.session.get("usuario_rol") or "").strip().lower()
    if rol in ("administrador", "admin", "instructor"):
        from inventario.models import Herramienta, CategoriaHerramienta, Inventario
        from prestamo.models import Prestamo, DetallePrestamo, DevolucionHerramienta
        from django.db.models import Sum
        from django.utils import timezone
        from datetime import timedelta

        # 1. Total herramientas and categories
        total_productos = Herramienta.objects.count()
        total_categorias = CategoriaHerramienta.objects.count()

        # 2. Loan counts
        prestamos_activos_count = Prestamo.objects.filter(id_estado="APROBADO").count()

        limite_vencimiento = timezone.now() - timedelta(days=7)
        prestamos_vencidos_count = Prestamo.objects.filter(
            id_estado="APROBADO", fecha_solicitud__lt=limite_vencimiento
        ).count()

        devoluciones_pendientes_count = Prestamo.objects.filter(
            id_estado="PENDIENTE"
        ).count()

        # 3. Recent loans emulated for template
        prestamos_qs = (
            Prestamo.objects.select_related("usuario")
            .prefetch_related("detalles__herramienta")
            .order_by("-fecha_solicitud")[:5]
        )
        prestamos_recientes = []
        for p in prestamos_qs:
            items = []
            for d in p.detalles.all():

                class FakeProducto:
                    def __init__(self, nombre):
                        self.nombre = nombre

                class FakeItem:
                    def __init__(self, producto, cantidad):
                        self.producto = producto
                        self.cantidad = cantidad

                items.append(
                    FakeItem(FakeProducto(d.herramienta.nombre_herramienta), d.cantidad)
                )

            class FakeItemsRelation:
                def __init__(self, items_list):
                    self.items_list = items_list

                def all(self):
                    return self.items_list

            class FakePrestamo:
                def __init__(self, p_obj, items_relation):
                    self.id = p_obj.id_prestamo
                    self.usuario = p_obj.usuario.nombre_completo
                    if p_obj.id_estado == "APROBADO":
                        self.estado = "activo"
                    elif p_obj.id_estado == "DEVUELTO":
                        self.estado = "devuelto"
                    else:
                        self.estado = p_obj.id_estado.lower()
                    self.fecha_prestamo = p_obj.fecha_solicitud
                    self.items = items_relation

            prestamos_recientes.append(FakePrestamo(p, FakeItemsRelation(items)))

        # 4. Recent returns emulated for template
        devoluciones_qs = DevolucionHerramienta.objects.select_related(
            "detalle_prestamo__prestamo__usuario", "herramienta"
        ).order_by("-fecha_devolucion")[:5]
        devoluciones_recientes = []
        for d_obj in devoluciones_qs:

            class FakeDevolucionPrestamo:
                def __init__(self, prestamo_obj):
                    self.id = prestamo_obj.id_prestamo
                    self.usuario = prestamo_obj.usuario.nombre_completo

            class FakeDevolucion:
                def __init__(self, d_obj):
                    self.prestamo = FakeDevolucionPrestamo(
                        d_obj.detalle_prestamo.prestamo
                    )
                    self.fecha_creacion = d_obj.fecha_devolucion
                    self.devolucion_total = True
                    self.estado = "aprobada"
                    self.get_estado_display = "Aprobada"

            devoluciones_recientes.append(FakeDevolucion(d_obj))

        # 5. Stock per category
        stock_por_categoria = []
        categories = CategoriaHerramienta.objects.all()
        for cat in categories:
            total_stock = (
                Inventario.objects.filter(
                    herramienta__categoria_herramienta=cat
                ).aggregate(total=Sum("cantidad"))["total"]
                or 0
            )

            class FakeCategoryStock:
                def __init__(self, nombre, total_stock):
                    self.nombre = nombre
                    self.total_stock = total_stock

            stock_por_categoria.append(FakeCategoryStock(cat.descripcion, total_stock))

        max_stock = max([c.total_stock for c in stock_por_categoria] + [1])

        # 6. Recent products emulated for template
        tools_qs = Herramienta.objects.select_related("categoria_herramienta").order_by(
            "-creado_en"
        )[:5]
        productos_recientes = []
        for h in tools_qs:
            stock = (
                Inventario.objects.filter(herramienta=h).aggregate(
                    total=Sum("cantidad")
                )["total"]
                or 0
            )

            class FakeCategory:
                def __init__(self, nombre):
                    self.nombre = nombre

            class FakeProduct:
                def __init__(self, h_obj, stock_val):
                    self.codigo_sku = h_obj.codigo_sku
                    self.nombre = h_obj.nombre_herramienta
                    self.descripcion = h_obj.descripcion
                    self.categoria = FakeCategory(
                        h_obj.categoria_herramienta.descripcion
                    )
                    self.stock = stock_val
                    self.actualizado_en = h_obj.creado_en

            productos_recientes.append(FakeProduct(h, stock))

        context = {
            "total_productos": total_productos,
            "total_categorias": total_categorias,
            "prestamos_activos_count": prestamos_activos_count,
            "prestamos_vencidos_count": prestamos_vencidos_count,
            "devoluciones_pendientes_count": devoluciones_pendientes_count,
            "prestamos_recientes": prestamos_recientes,
            "devoluciones_recientes": devoluciones_recientes,
            "stock_por_categoria": stock_por_categoria,
            "max_stock": max_stock,
            "productos_recientes": productos_recientes,
        }
        return render(request, "usuario/pagina_principal.html", context)
    return redirect("home_usuario")


def reportes_view(request):
    """Vista de reportes (placeholder)"""
    messages.info(request, "El módulo de reportes está en desarrollo.")
    return redirect("home")


# ─────────────────────────────────────────────────────────────
#  LISTA DE USUARIOS — solo Admin
@admin_required
def lista_usuarios_view(request):

    # ── POST: editar usuario ──────────────────────────────────
    if request.method == "POST" and request.POST.get("accion") == "editar_usuario":
        doc = request.POST.get("numero_documento", "").strip()
        nombre = request.POST.get("nombre_completo", "").strip()
        correo = request.POST.get("correo", "").strip().lower()
        telefono = request.POST.get("telefono", "").strip()
        numero_ficha = request.POST.get("numero_ficha", "").strip()
        nombre_programa = request.POST.get("nombre_programa", "").strip()
        rol_id = request.POST.get("rol", "").strip()
        nueva_password = request.POST.get("nueva_password", "").strip()

        usuario = get_object_or_404(Usuario, numero_documento=doc)

        if not nombre:
            messages.error(request, "El nombre no puede estar vacío.")
            return redirect("lista_usuarios")

        if not correo or "@" not in correo:
            messages.error(request, "Ingresa un correo válido.")
            return redirect("lista_usuarios")

        if telefono and not telefono.isdigit():
            messages.error(request, "El teléfono solo debe contener dígitos.")
            return redirect("lista_usuarios")

        if Usuario.objects.filter(correo=correo).exclude(numero_documento=doc).exists():
            messages.error(
                request,
                "Ese correo ya está en uso por " "otro usuario.",
            )
            return redirect("lista_usuarios")

        if rol_id not in ROLES_VALIDOS:
            messages.error(request, "Rol no válido.")
            return redirect("lista_usuarios")

        campos = [
            "nombre_completo",
            "correo",
            "telefono",
            "numero_ficha",
            "nombre_programa",
            "rol",
        ]
        usuario.nombre_completo = nombre
        usuario.correo = correo
        usuario.telefono = telefono
        # usuario.numero_ficha = numero_ficha
        # usuario.nombre_programa = nombre_programa
        usuario.id_rol = rol_id

        if nueva_password:
            if len(nueva_password) < 8:
                messages.error(
                    request,
                    "La nueva contraseña debe tener al menos " "8 caracteres.",
                )
                return redirect("lista_usuarios")
            usuario.user.set_password(nueva_password)
            usuario.user.save()

        usuario.save(update_fields=campos)

        messages.success(
            request,
            "Usuario " f"{usuario.nombre_completo} actualizado correctamente.",
        )
        return redirect("lista_usuarios")

    # ── GET: listar con filtros ───────────────────────────────
    qs = Usuario.objects.order_by("nombre_completo")

    q = request.GET.get("q", "").strip()
    rol = request.GET.get("rol", "")
    tipo_doc = request.GET.get("tipo_doc", "")

    if q:
        qs = qs.filter(
            Q(nombre_completo__icontains=q)
            | Q(numero_documento__icontains=q)
            | Q(correo__icontains=q)
        )
    if rol:
        qs = qs.filter(rol=rol)
    if tipo_doc:
        qs = qs.filter(tipo_documento=tipo_doc)

    ctx = {
        "usuarios": qs,
        "roles": ROLES,
        "tipos_doc": Usuario.TipoDocumento.choices,
        "q": q,
        "rol_id": rol,
        "tipo_doc": tipo_doc,
        "total": qs.count(),
    }
    return render(request, "lista_usuarios.html", ctx)


# ─────────────────────────────────────────────────────────────
#  DETALLE USUARIO (JSON para modal)
# ─────────────────────────────────────────────────────────────
@sesion_requerida
def detalle_usuario_json(request, numero_documento):
    usuario = get_object_or_404(
        Usuario.objects.select_related("destinado", "solicitado"),
        numero_documento=numero_documento,
    )

    prestamos_qs = (
        Prestamo.objects.prefetch_related("items__producto")
        .filter(usuario=usuario.numero_documento)
        .order_by("-fecha_prestamo")
    )

    prestamos = []
    for p in prestamos_qs:
        prestamos.append(
            {
                "pk": p.pk,
                "estado": p.estado,
                "estado_display": p.get_estado_display(),
                "fecha_prestamo": p.fecha_prestamo.strftime("%d/%m/%Y"),
                "fecha_vencimiento": (
                    p.fecha_vencimiento.strftime("%d/%m/%Y")
                    if p.fecha_vencimiento
                    else "—"
                ),
                "dias_restantes": p.dias_restantes,
                "observaciones": p.observaciones or "",
                "motivo_solicitud": p.motivo_solicitud or "",
                "pendiente_para_devolucion": p.estado in ["activo", "parcial"],
                "items": [
                    {
                        "nombre": item.producto.nombre,
                        "cantidad": item.cantidad,
                        "devuelto": item.devuelto,
                        "serial": item.serial_entregado,
                    }
                    for item in p.items.all()
                ],
            }
        )

    data = {
        "numero_documento": usuario.numero_documento,
        "nombre_completo": usuario.nombre_completo,
        "correo": usuario.correo,
        "telefono": usuario.telefono,
        "tipo_documento_display": usuario.get_tipo_documento_display(),
        "tipo_documento": usuario.tipo_documento,
        "rol": usuario.id_rol,
        "prestamos_totales": prestamos_qs.count(),
        "prestamos_activos": prestamos_qs.filter(estado="activo").count(),
        "prestamos_parciales": prestamos_qs.filter(estado="parcial").count(),
        "prestamos_vencidos": prestamos_qs.filter(estado="vencido").count(),
        "prestamos": prestamos,
    }
    return JsonResponse(data)


# ─────────────────────────────────────────────────────────────
#  EXPORTAR USUARIOS CSV
# ─────────────────────────────────────────────────────────────
@sesion_requerida
def exportar_usuarios_csv(request):
    qs = Usuario.objects.order_by("nombre_completo")

    q = request.GET.get("q", "").strip()
    rol = request.GET.get("rol", "")
    tipo_doc = request.GET.get("tipo_doc", "")

    if q:
        qs = qs.filter(
            Q(nombre_completo__icontains=q)
            | Q(numero_documento__icontains=q)
            | Q(correo__icontains=q)
        )
    if rol:
        qs = qs.filter(rol=rol)
    if tipo_doc:
        qs = qs.filter(tipo_documento=tipo_doc)

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="usuarios.csv"'
    response.write("\ufeff")

    writer = csv.writer(response)
    writer.writerow(
        [
            "Número de Documento",
            "Tipo de Documento",
            "Nombre Completo",
            "Correo",
            "Teléfono",
            "Ficha",
            "Programa",
            "Rol",
        ]
    )
    for u in qs:
        writer.writerow(
            [
                u.numero_documento,
                u.get_tipo_documento_display(),
                u.nombre_completo,
                u.correo,
                u.telefono,
                u.numero_ficha,
                u.nombre_programa,
                u.rol,
            ]
        )
    return response


# ─────────────────────────────────────────────────────────────
#  PERFIL
# ─────────────────────────────────────────────────────────────
@sesion_requerida
def perfil_view(request):
    doc = request.session.get("usuario_documento")
    usuario = get_object_or_404(Usuario, numero_documento=doc)
    errores = {}
    accion_activa = ""

    if request.method == "POST":
        accion_activa = request.POST.get("accion", "")

        if accion_activa == "editar_perfil":
            nombre = request.POST.get("nombre_completo", "").strip()
            correo = request.POST.get("correo", "").strip().lower()
            telefono = request.POST.get("telefono", "").strip()
            numero_ficha = request.POST.get("numero_ficha", "").strip()
            nombre_programa = request.POST.get("nombre_programa", "").strip()

            if not nombre:
                errores["nombre_completo"] = "El nombre no puede estar vacío."
            if not correo or "@" not in correo:
                errores["correo"] = "Ingresa un correo válido."
            if telefono and not telefono.isdigit():
                errores["telefono"] = "El teléfono solo debe contener dígitos."
            if not errores.get("correo"):
                if (
                    Usuario.objects.filter(correo=correo)
                    .exclude(numero_documento=doc)
                    .exists()
                ):
                    errores["correo"] = (
                        "Este correo ya está en uso por " "otro usuario."
                    )

            if not errores:
                usuario.nombre_completo = nombre
                usuario.correo = correo
                usuario.telefono = telefono
                # usuario.numero_ficha = numero_ficha
                # usuario.nombre_programa = nombre_programa
                usuario.save(
                    update_fields=[
                        "nombre_completo",
                        "correo",
                        "telefono",
                        "numero_ficha",
                        "nombre_programa",
                    ]
                )
                request.session["usuario_nombre"] = nombre
                messages.success(request, "Perfil actualizado correctamente.")
                return redirect("perfil")

        elif accion_activa == "cambiar_password":
            actual = request.POST.get("password_actual", "")
            nueva = request.POST.get("password_nueva", "")
            confirma = request.POST.get("password_confirma", "")

            if not check_password(actual, usuario.user.password):
                errores["password_actual"] = "La contraseña actual es incorrecta."
            if len(nueva) < 8:
                errores["password_nueva"] = (
                    "La nueva contraseña debe tener al menos 8 caracteres."
                )
            if nueva != confirma:
                errores["password_confirma"] = "Las contraseñas no coinciden."

            if not errores:
                usuario.user.set_password(nueva)
                usuario.user.save()
                messages.success(
                    request,
                    "Contraseña actualizada correctamente.",
                )
                return redirect("perfil")

        elif accion_activa == "guardar_config":
            request.session["cfg_notif_prestamos"] = "notif_prestamos" in request.POST
            request.session["cfg_notif_vencimientos"] = (
                "notif_vencimientos" in request.POST
            )
            request.session["cfg_notif_devoluciones"] = (
                "notif_devoluciones" in request.POST
            )
            messages.success(request, "Configuración guardada.")
            return redirect("perfil")

    cfg_notif_prestamos = request.session.get("cfg_notif_prestamos", True)
    cfg_notif_vencimientos = request.session.get("cfg_notif_vencimientos", True)
    cfg_notif_devoluciones = request.session.get("cfg_notif_devoluciones", True)

    context = {
        "usuario": usuario,
        "errores": errores,
        "accion_activa": accion_activa,
        "tab_list": [
            ("tab-datos", "Datos personales", ""),
            ("tab-password", "Contraseña", ""),
            ("tab-config", "Notificaciones", ""),
        ],
        "notificaciones_lista": [
            (
                "notif_prestamos",
                "Nuevos préstamos asignados",
                "Recibir alerta cuando se te asigne un préstamo.",
                cfg_notif_prestamos,
            ),
            (
                "notif_vencimientos",
                "Próximos a vencer",
                "Alerta 3 días antes de que venza un préstamo activo.",
                cfg_notif_vencimientos,
            ),
            (
                "notif_devoluciones",
                "Devoluciones pendientes",
                "Recordatorio de devoluciones en estado pendiente.",
                cfg_notif_devoluciones,
            ),
        ],
        "cfg_notif_prestamos": cfg_notif_prestamos,
        "cfg_notif_vencimientos": cfg_notif_vencimientos,
        "cfg_notif_devoluciones": cfg_notif_devoluciones,
    }

    return render(request, "perfil.html", context)


def registro_qr_pdf(request):
    pass
