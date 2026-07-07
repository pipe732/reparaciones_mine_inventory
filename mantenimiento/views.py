from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from usuario.decorators import login_required

from .forms import (
    BitacoraEstadoForm,
    DetalleMantenimientoForm,
    MantenimientoForm,
    TipoEstadoForm,
    TipoMantenimientoForm,
)
from .models import (
    BitacoraEstado,
    Mantenimiento,
    TipoEstado,
    TipoMantenimiento,
)
from inventario.models import Herramienta


# ──────────────────────────────────────────────────────────────────────────────
#  1. ESTADO ACTUAL DE HERRAMIENTAS
# ──────────────────────────────────────────────────────────────────────────────


@login_required
def estado_actual_lista_view(request):
    """
    Muestra cada herramienta del inventario con su estado de mantenimiento
    actual (si tiene uno activo) o 'Disponible' en caso contrario.
    """
    herramientas = Herramienta.objects.all().order_by("nombre")

    for h in herramientas:
        mant_activo = (
            h.mantenimientos.filter(fecha_salida__isnull=True)
            .order_by("-fecha_ingreso")
            .first()
        )
        if mant_activo:
            h.en_mantenimiento = True
            h.mantenimiento_id = mant_activo.id_mantenimiento
            h.tipo_mantenimiento_str = mant_activo.tipo_mantenimiento
            ultimo = (
                mant_activo.bitacoras
                .order_by("-id_bitacora_estado")
                .first()
            )
            h.estado_mantenimiento = ultimo.estado if ultimo else "Ingresado"
            h.estado_nivel = ultimo.nivel_estado if ultimo else "warning"
        else:
            h.en_mantenimiento = False
            h.estado_mantenimiento = "Disponible"
            h.estado_nivel = "success"

    context = {
        "herramientas": herramientas,
        "titulo": "Estado Actual de Herramientas",
        "subtitulo": "Resumen del estado de mantenimiento por herramienta",
    }
    return render(request, "mantenimiento/estado_actual.html", context)


# ──────────────────────────────────────────────────────────────────────────────
#  2. HISTORIAL POR HERRAMIENTA / PRODUCTO
# ──────────────────────────────────────────────────────────────────────────────


@login_required
def historial_producto_view(request, pk):
    """
    Historial completo de mantenimientos de una herramienta específica.
    Contexto compatible con el template historial_producto.html.
    """
    herramienta = get_object_or_404(Herramienta, pk=pk)
    registros = Mantenimiento.objects.filter(herramienta=herramienta).order_by(
        "-fecha_ingreso"
    )

    # Enriquecer con último estado de bitácora
    for r in registros:
        ultimo = r.bitacoras.order_by("-id_bitacora_estado").first()
        r.estado_actual = ultimo.estado if ultimo else "Ingresado"
        r.nivel_actual = ultimo.nivel_estado if ultimo else "warning"
        r.finalizado = r.fecha_salida is not None

    context = {
        "producto": herramienta,  # el template usa "producto"
        "registros": registros,
        "total_registros": registros.count(),
        "titulo": f"Historial — {herramienta.nombre}",
        "subtitulo": herramienta.nombre,
        "url_accion": None,
        "label_accion": None,
    }
    return render(request, "mantenimiento/historial_producto.html", context)


# ──────────────────────────────────────────────────────────────────────────────
#  3. CATÁLOGO: TIPOS DE ESTADO
# ──────────────────────────────────────────────────────────────────────────────


@login_required
def tipo_estado_lista_view(request):
    """
    Lista de tipos de estado con formulario de alta en modal.
    """
    estados = TipoEstado.objects.all().order_by("nombre")
    form = TipoEstadoForm()
    show_modal = False

    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "eliminar":
            estado_id = request.POST.get("estado_id")
            estado = get_object_or_404(TipoEstado, pk=estado_id)
            estado.delete()
            messages.success(
                request, "Tipo de estado eliminado correctamente."
            )
            return redirect("mantenimiento:tipo_estado_lista")

        elif accion == "crear":
            form = TipoEstadoForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(
                    request, "Tipo de estado creado exitosamente."
                )
                return redirect("mantenimiento:tipo_estado_lista")
            else:
                messages.error(
                    request,
                    "Error al crear el tipo de estado. Verifique los datos.",
                )
                show_modal = True

    context = {
        "estados": estados,
        "form": form,
        "tipo_estado_form": form,
        "show_modal": show_modal,
        "titulo": "Tipos de Estado",
        "subtitulo": "Catálogo de estados de mantenimiento",
    }
    return render(request, "mantenimiento/tipo_estado_list.html", context)


@login_required
def tipo_estado_nuevo_view(request):
    """
    Crear un nuevo tipo de estado desde el modal POST.
    """
    if request.method == "POST":
        form = TipoEstadoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Tipo de estado creado exitosamente.")
            return redirect("mantenimiento:tipo_estado_lista")
        else:
            messages.error(
                request,
                "Error al crear el tipo de estado. Verifique los datos.",
            )
            estados = TipoEstado.objects.all().order_by("nombre")
            context = {
                "estados": estados,
                "form": form,
                "tipo_estado_form": form,
                "show_modal": True,
                "titulo": "Tipos de Estado",
                "subtitulo": "Catálogo de estados de mantenimiento",
            }
            return render(
                request, "mantenimiento/tipo_estado_list.html", context
            )
    return redirect("mantenimiento:tipo_estado_lista")


@login_required
def tipo_estado_editar_view(request, pk):
    """
    Editar un tipo de estado existente.
    """
    estado = get_object_or_404(TipoEstado, pk=pk)

    if request.method == "POST":
        form = TipoEstadoForm(request.POST, instance=estado)
        if form.is_valid():
            form.save()
            messages.success(
                request, "Tipo de estado modificado correctamente."
            )
            return redirect("mantenimiento:tipo_estado_lista")
        else:
            messages.error(request, "Error al modificar el estado.")
    else:
        form = TipoEstadoForm(instance=estado)

    context = {
        "estado": estado,
        "form": form,
        "titulo": f"Editar Estado: {estado.nombre}",
        "subtitulo": "Modificar tipo de estado",
        "url_cancelar": "mantenimiento:tipo_estado_lista",
    }
    return render(request, "mantenimiento/tipo_estado_editar.html", context)


# ──────────────────────────────────────────────────────────────────────────────
#  4. CATÁLOGO: TIPOS DE MANTENIMIENTO
# ──────────────────────────────────────────────────────────────────────────────


@login_required
def tipo_mantenimiento_lista_view(request):
    """
    Lista de tipos de mantenimiento con formulario de alta en modal.
    """
    tipos = TipoMantenimiento.objects.all().order_by("nombre")
    form = TipoMantenimientoForm()
    show_modal = False

    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "eliminar":
            tipo_id = request.POST.get("tipo_id")
            tipo = get_object_or_404(TipoMantenimiento, pk=tipo_id)
            tipo.delete()
            messages.success(request, "Tipo de mantenimiento eliminado.")
            return redirect("mantenimiento:tipo_mantenimiento_lista")

        elif accion == "crear":
            form = TipoMantenimientoForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Tipo de mantenimiento creado.")
                return redirect("mantenimiento:tipo_mantenimiento_lista")
            else:
                messages.error(
                    request,
                    "Error al crear el tipo de mantenimiento.",
                )
                show_modal = True

    context = {
        "tipos": tipos,
        "form": form,
        "tipo_mantenimiento_form": form,
        "show_modal": show_modal,
        "titulo": "Tipos de Mantenimiento",
        "subtitulo": "Catálogo de categorías de mantenimiento",
    }
    return render(
        request,
        "mantenimiento/tipo_mantenimiento_lista.html",
        context,
    )


@login_required
def tipo_mantenimiento_crear_view(request):
    """
    Crear un tipo de mantenimiento desde el modal POST.
    """
    if request.method == "POST":
        form = TipoMantenimientoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Tipo de mantenimiento creado.")
            return redirect("mantenimiento:tipo_mantenimiento_lista")
        else:
            messages.error(
                request, "Error al crear el tipo de mantenimiento."
            )
            tipos = TipoMantenimiento.objects.all().order_by("nombre")
            context = {
                "tipos": tipos,
                "form": form,
                "tipo_mantenimiento_form": form,
                "show_modal": True,
                "titulo": "Tipos de Mantenimiento",
                "subtitulo": "Catálogo de categorías de mantenimiento",
            }
            return render(
                request,
                "mantenimiento/tipo_mantenimiento_lista.html",
                context,
            )
    return redirect("mantenimiento:tipo_mantenimiento_lista")


@login_required
def tipo_mantenimiento_inactivar_view(request, pk):
    """
    Inactivar un tipo de mantenimiento (redirige con mensaje de aviso).
    """
    tipo = get_object_or_404(TipoMantenimiento, pk=pk)
    messages.info(
        request,
        f'El tipo de mantenimiento "{tipo.nombre}" no se puede inactivar.',
    )
    return redirect("mantenimiento:tipo_mantenimiento_lista")


@login_required
def tipo_mantenimiento_editar_view(request, pk):
    """
    Editar un tipo de mantenimiento existente.
    """
    tipo = get_object_or_404(TipoMantenimiento, pk=pk)

    if request.method == "POST":
        form = TipoMantenimientoForm(request.POST, instance=tipo)
        if form.is_valid():
            form.save()
            messages.success(request, "Tipo de mantenimiento modificado.")
            return redirect("mantenimiento:tipo_mantenimiento_lista")
        else:
            messages.error(
                request,
                "Error al modificar el tipo de mantenimiento.",
            )
    else:
        form = TipoMantenimientoForm(instance=tipo)

    context = {
        "tipo": tipo,
        "form": form,
        "titulo": f"Editar Tipo: {tipo.nombre}",
        "subtitulo": "Modificar tipo de mantenimiento",
        "url_cancelar": "mantenimiento:tipo_mantenimiento_lista",
    }
    return render(
        request,
        "mantenimiento/tipo_mantenimiento_form.html",
        context,
    )


@login_required
def tipo_mantenimiento_confirmar_view(request, pk):
    """
    Confirmación antes de eliminar un tipo de mantenimiento.
    """
    tipo = get_object_or_404(TipoMantenimiento, pk=pk)

    if request.method == "POST":
        tipo.delete()
        messages.success(
            request, f'Tipo "{tipo.nombre}" eliminado correctamente.'
        )
        return redirect("mantenimiento:tipo_mantenimiento_lista")

    context = {
        "tipo": tipo,
        "titulo": f"Eliminar Tipo: {tipo.nombre}",
        "subtitulo": "Confirmar eliminación",
    }
    return render(
        request,
        "mantenimiento/tipo_mantenimiento_confirmar.html",
        context,
    )


# ──────────────────────────────────────────────────────────────────────────────
#  5. GESTIÓN DE MANTENIMIENTOS
# ──────────────────────────────────────────────────────────────────────────────


@login_required
def mantenimiento_lista_view(request):
    """
    Lista de mantenimientos con modal para registrar uno nuevo.
    Contexto compatible con mantenimiento_lista.html.
    """
    mantenimientos = (
        Mantenimiento.objects.select_related("herramienta")
        .all()
        .order_by("-fecha_ingreso")
    )
    form = MantenimientoForm()
    show_modal = False

    total_activos = Mantenimiento.objects.filter(
        fecha_salida__isnull=True
    ).count()
    total_finalizados = Mantenimiento.objects.filter(
        fecha_salida__isnull=False
    ).count()

    # Enriquecer con estado de bitácora para la tabla
    registros = list(mantenimientos)
    for r in registros:
        ultimo = r.bitacoras.order_by("-id_bitacora_estado").first()
        r.estado_actual = ultimo.estado if ultimo else "Ingresado"
        r.nivel_actual = ultimo.nivel_estado if ultimo else "warning"
        r.finalizado = r.fecha_salida is not None
        # Alias compatible con el template (usa r.producto)
        r.producto = r.herramienta

    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "crear":
            form = MantenimientoForm(request.POST)
            if form.is_valid():
                mantenimiento = form.save()
                # Bitácora inicial automática
                BitacoraEstado.objects.create(
                    mantenimiento=mantenimiento,
                    estado="Ingresado",
                    nivel_estado="warning",
                    descripcion=(
                        "Ingreso inicial al módulo de mantenimiento."
                    ),
                )
                messages.success(
                    request,
                    "Mantenimiento registrado correctamente.",
                )
                return redirect("mantenimiento:mantenimiento_lista")
            else:
                messages.error(
                    request,
                    "Error al registrar el mantenimiento.",
                )
                show_modal = True

        elif accion == "eliminar":
            mant_id = request.POST.get("mantenimiento_id")
            mant = get_object_or_404(Mantenimiento, pk=mant_id)
            mant.delete()
            messages.success(
                request, "Registro de mantenimiento eliminado."
            )
            return redirect("mantenimiento:mantenimiento_lista")

    context = {
        "registros": registros,  # el template usa "registros"
        "mantenimientos": mantenimientos,
        "form": form,
        "show_modal": show_modal,
        "total_activos": total_activos,
        "total_finalizados": total_finalizados,
        "titulo": "Todos los Mantenimientos",
        "subtitulo": ("Listado completo de registros de mantenimiento"),
        "url_accion": None,
        "label_accion": None,
        "editable_ids": set(
            Mantenimiento.objects
            .filter(fecha_salida__isnull=True)
            .values_list("id_mantenimiento", flat=True)
        ),
    }
    return render(request, "mantenimiento/mantenimiento_lista.html", context)


@login_required
def mantenimiento_detalle_view(request, pk):
    """
    Detalle de un mantenimiento: agregar acciones, cambiar estado,
    finalizar el mantenimiento. Contexto compatible con
    mantenimiento_detalle.html (que usa la variable 'm').
    """
    mantenimiento = get_object_or_404(Mantenimiento, pk=pk)
    detalles = mantenimiento.detalles.all().order_by("-creado_en")
    bitacoras = mantenimiento.bitacoras.all().order_by("-id_bitacora_estado")

    detalle_form = DetalleMantenimientoForm()
    estado_form = BitacoraEstadoForm()

    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "agregar_detalle":
            detalle_form = DetalleMantenimientoForm(request.POST)
            if detalle_form.is_valid():
                det = detalle_form.save(commit=False)
                det.mantenimiento = mantenimiento
                det.save()
                messages.success(request, "Detalle de acción agregado.")
                return redirect(
                    "mantenimiento:mantenimiento_detalle",
                    pk=mantenimiento.pk,
                )
            else:
                messages.error(request, "Error al agregar el detalle.")

        elif accion == "actualizar_estado":
            estado_form = BitacoraEstadoForm(request.POST)
            if estado_form.is_valid():
                bit = estado_form.save(commit=False)
                bit.mantenimiento = mantenimiento
                # Nivel de gravedad desde catálogo TipoEstado
                tipo = TipoEstado.objects.filter(nombre=bit.estado).first()
                bit.nivel_estado = tipo.nivel if tipo else "warning"
                bit.save()
                messages.success(
                    request,
                    "Estado de mantenimiento actualizado.",
                )
                return redirect(
                    "mantenimiento:mantenimiento_detalle",
                    pk=mantenimiento.pk,
                )
            else:
                messages.error(request, "Error al actualizar el estado.")

        elif accion == "finalizar":
            mantenimiento.fecha_salida = timezone.now()
            mantenimiento.save()
            BitacoraEstado.objects.create(
                mantenimiento=mantenimiento,
                estado="Finalizado / Disponible",
                nivel_estado="success",
                descripcion=(
                    "Mantenimiento concluido. "
                    "Herramienta devuelta al inventario."
                ),
            )
            messages.success(
                request, "Mantenimiento finalizado con éxito."
            )
            return redirect(
                "mantenimiento:mantenimiento_detalle",
                pk=mantenimiento.pk,
            )

    context = {
        "m": mantenimiento,  # el template usa "m"
        "mantenimiento": mantenimiento,
        "detalles": detalles,
        "bitacoras": bitacoras,
        "detalle_form": detalle_form,
        "estado_form": estado_form,
        "puede_editar": mantenimiento.fecha_salida is None,
        "url_cancelar": "mantenimiento:mantenimiento_lista",
        "cambios_auditoria": [],  # placeholder para auditoría futura
    }
    return render(
        request,
        "mantenimiento/mantenimiento_detalle.html",
        context,
    )


@login_required
def mantenimiento_crear_view(request):
    """
    Formulario dedicado para crear un nuevo mantenimiento
    (compatible con mantenimiento_form.html).
    """
    form = MantenimientoForm()

    if request.method == "POST":
        form = MantenimientoForm(request.POST)
        if form.is_valid():
            mantenimiento = form.save()
            BitacoraEstado.objects.create(
                mantenimiento=mantenimiento,
                estado="Ingresado",
                nivel_estado="warning",
                descripcion=("Ingreso inicial al módulo de mantenimiento."),
            )
            messages.success(
                request, "Mantenimiento registrado correctamente."
            )
            return redirect(
                "mantenimiento:mantenimiento_detalle",
                pk=mantenimiento.pk,
            )
        else:
            messages.error(request, "Error al registrar el mantenimiento.")

    context = {
        "form": form,
        "mantenimiento": None,
        "titulo": "Nuevo Mantenimiento",
        "subtitulo": "Registrar ingreso de herramienta a mantenimiento",
        "url_cancelar": "mantenimiento:mantenimiento_lista",
    }
    return render(request, "mantenimiento/mantenimiento_form.html", context)


@login_required
def mantenimiento_editar_view(request, pk):
    """
    Editar un mantenimiento activo (sin fecha de salida).
    Compatible con mantenimiento_form.html.
    """
    mantenimiento = get_object_or_404(Mantenimiento, pk=pk)

    if request.method == "POST":
        form = MantenimientoForm(request.POST, instance=mantenimiento)
        if form.is_valid():
            form.save()
            messages.success(
                request, "Mantenimiento actualizado correctamente."
            )
            return redirect(
                "mantenimiento:mantenimiento_detalle",
                pk=mantenimiento.pk,
            )
        else:
            messages.error(request, "Error al actualizar el mantenimiento.")
    else:
        form = MantenimientoForm(instance=mantenimiento)

    context = {
        "form": form,
        "mantenimiento": mantenimiento,
        "titulo": (f"Editar Mantenimiento #{mantenimiento.id_mantenimiento}"),
        "subtitulo": str(mantenimiento.herramienta),
        "url_cancelar": "mantenimiento:mantenimiento_lista",
    }
    return render(request, "mantenimiento/mantenimiento_form.html", context)


@login_required
def detalle_mantenimiento_crear_view(request, pk):
    """
    Agrega un detalle (acción realizada) a un mantenimiento.
    Acción POST enviada desde el template mantenimiento_detalle.html.
    """
    mantenimiento = get_object_or_404(Mantenimiento, pk=pk)

    if request.method == "POST":
        form = DetalleMantenimientoForm(request.POST)
        if form.is_valid():
            det = form.save(commit=False)
            det.mantenimiento = mantenimiento
            det.save()
            messages.success(request, "Detalle de acción agregado.")
        else:
            messages.error(request, "Error al guardar el detalle.")

    return redirect("mantenimiento:mantenimiento_detalle", pk=mantenimiento.pk)
