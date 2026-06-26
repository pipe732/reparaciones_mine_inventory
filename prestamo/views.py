import json
import logging
from datetime import date, timedelta

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from common.mixins import sesion_requerida
from inventario.models import Herramienta
from usuario.models import Usuario

from .models import Devolucion, DetalleDevolucion, DetallePrestamo, Prestamo

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def _urgencia(prestamo):
    """Devuelve ('vencido'|'proximo'|'normal', dias_restantes|None)."""
    if not prestamo.fecha_vencimiento:
        return "normal", None
    hoy = date.today()
    delta = (prestamo.fecha_vencimiento - hoy).days
    if delta < 0:
        return "vencido", delta
    if delta <= 3:
        return "proximo", delta
    return "normal", delta


def _enriquecer_prestamos(qs):
    """Añade atributos urgencia, dias_restantes y nombre_usuario a cada préstamo."""
    resultado = []
    for p in qs.select_related("usuario").prefetch_related("items__producto"):
        p.urgencia, p.dias_restantes = _urgencia(p)
        p.nombre_usuario = p.usuario.nombre_completo if p.usuario else ""
        resultado.append(p)
    return resultado


# ──────────────────────────────────────────────────────────────────────────────
#  VISTA ADMIN — Gestión de préstamos  (prestamo.html)
# ──────────────────────────────────────────────────────────────────────────────

@sesion_requerida
def prestamo_view(request):
    """
    Vista principal para administradores/instructores/almacenistas.
    Maneja: crear préstamo, aprobar, rechazar, devolver ítem, editar observaciones.
    """

    # ── POST: acciones ──────────────────────────────────────────────────────
    if request.method == "POST":
        accion = request.POST.get("accion", "")

        # Crear préstamo nuevo (wizard 4 pasos del modal)
        if accion == "crear_prestamo":
            usuario_doc   = request.POST.get("usuario_documento", "").strip()
            productos_ids = request.POST.getlist("producto[]")
            cantidades    = request.POST.getlist("cantidad[]")
            fecha_venc    = request.POST.get("fecha_vencimiento") or None
            observaciones = request.POST.get("observaciones", "").strip()
            motivo        = request.POST.get("motivo_solicitud", "").strip()

            try:
                usuario = Usuario.objects.get(numero_documento=usuario_doc)
            except Usuario.DoesNotExist:
                messages.error(request, "El usuario indicado no existe.")
                return redirect("prestamo")

            if not productos_ids:
                messages.error(request, "Debes agregar al menos una herramienta.")
                return redirect("prestamo")

            prestamo = Prestamo.objects.create(
                usuario=usuario,
                estado="activo",
                fecha_vencimiento=fecha_venc or None,
                observaciones=observaciones,
                motivo_solicitud=motivo,
            )

            for prod_id, cant in zip(productos_ids, cantidades):
                try:
                    herramienta = Herramienta.objects.get(pk=prod_id)
                    cantidad    = max(1, int(cant))
                    if herramienta.stock < cantidad:
                        messages.warning(
                            request,
                            f"Stock insuficiente para «{herramienta.nombre}». "
                            f"Se omitió del préstamo.",
                        )
                        continue
                    DetallePrestamo.objects.create(
                        prestamo=prestamo,
                        producto=herramienta,
                        cantidad=cantidad,
                    )
                    herramienta.stock -= cantidad
                    herramienta.save(update_fields=["stock"])
                except (Herramienta.DoesNotExist, ValueError):
                    continue

            if not prestamo.items.exists():
                prestamo.delete()
                messages.error(request, "No se pudo crear el préstamo: sin herramientas válidas.")
            else:
                messages.success(request, f"Préstamo #{prestamo.pk} creado correctamente.")

            return redirect("prestamo")

        # Aprobar solicitud pendiente
        elif accion == "aprobar_prestamo":
            pk = request.POST.get("pk")
            prestamo = get_object_or_404(Prestamo, pk=pk)
            productos_ids = request.POST.getlist("producto[]")
            cantidades    = request.POST.getlist("cantidad[]")
            seriales      = request.POST.getlist("serial[]")

            if prestamo.estado != "pendiente":
                messages.warning(request, "Este préstamo ya no está pendiente.")
                return redirect("prestamo")

            # Actualizar ítems con seriales si vienen del modal de aprobación
            for item, serial in zip(prestamo.items.all(), seriales):
                if serial:
                    item.serial_entregado = serial
                    item.save(update_fields=["serial_entregado"])
                # Descontar stock al aprobar
                item.producto.stock -= item.cantidad
                item.producto.save(update_fields=["stock"])

            prestamo.estado = "activo"
            prestamo.save(update_fields=["estado"])
            messages.success(request, f"Préstamo #{prestamo.pk} aprobado.")
            return redirect("prestamo")

        # Rechazar solicitud pendiente
        elif accion == "rechazar_prestamo":
            pk            = request.POST.get("pk")
            motivo_rechazo = request.POST.get("motivo_rechazo", "").strip()
            prestamo = get_object_or_404(Prestamo, pk=pk)

            if prestamo.estado != "pendiente":
                messages.warning(request, "Este préstamo ya no está pendiente.")
                return redirect("prestamo")

            prestamo.estado         = "rechazado"
            prestamo.motivo_rechazo = motivo_rechazo
            prestamo.save(update_fields=["estado", "motivo_rechazo"])
            messages.success(request, f"Solicitud #{prestamo.pk} rechazada.")
            return redirect("prestamo")

        # Devolver un ítem individual desde la fila de detalle
        elif accion == "devolver_item":
            item_pk = request.POST.get("item_pk")
            item    = get_object_or_404(DetallePrestamo, pk=item_pk)
            if not item.devuelto:
                item.devuelto = True
                item.save(update_fields=["devuelto"])
                # Reponer stock
                item.producto.stock += item.cantidad
                item.producto.save(update_fields=["stock"])
                # Actualizar estado del préstamo
                prestamo = item.prestamo
                pendientes = prestamo.items.filter(devuelto=False).count()
                prestamo.estado = "devuelto" if pendientes == 0 else "parcial"
                prestamo.save(update_fields=["estado"])
                messages.success(request, f"«{item.producto.nombre}» devuelto.")
            return redirect("prestamo")

        # Editar observaciones
        elif accion == "editar_prestamo":
            pk            = request.POST.get("pk")
            observaciones = request.POST.get("observaciones", "").strip()
            prestamo = get_object_or_404(Prestamo, pk=pk)
            prestamo.observaciones = observaciones
            prestamo.save(update_fields=["observaciones"])
            messages.success(request, "Observaciones actualizadas.")
            return redirect("prestamo")

    # ── GET: listar préstamos ───────────────────────────────────────────────
    hoy        = date.today()
    tres_dias  = hoy + timedelta(days=3)
    filtro_q       = request.GET.get("q",       "").strip()
    filtro_estado  = request.GET.get("estado",  "").strip().lower()
    filtro_vencidos = request.GET.get("vencidos", "").strip()

    qs = Prestamo.objects.select_related("usuario").prefetch_related(
        "items__producto"
    ).order_by("-fecha_prestamo")

    if filtro_q:
        qs = qs.filter(
            usuario__nombre_completo__icontains=filtro_q
        ) | qs.filter(
            usuario__numero_documento__icontains=filtro_q
        )

    if filtro_estado:
        qs = qs.filter(estado=filtro_estado)

    if filtro_vencidos == "1":
        qs = qs.filter(estado="vencido")

    prestamos = _enriquecer_prestamos(qs)

    # KPIs
    todos        = Prestamo.objects.all()
    total        = todos.count()
    activos      = todos.filter(estado="activo").count()
    pendientes   = todos.filter(estado="pendiente").count()
    devueltos    = todos.filter(estado="devuelto").count()
    vencidos     = todos.filter(estado="vencido").count()
    prox_vencer  = todos.filter(
        estado__in=["activo", "parcial"],
        fecha_vencimiento__range=[hoy, tres_dias],
    ).count()

    # JSON para el modal de crear préstamo
    usuarios_qs = Usuario.objects.all().values(
        "numero_documento", "nombre_completo", "tipo_documento"
    )
    productos_qs = Herramienta.objects.filter(stock__gt=0).values(
        "pk", "nombre", "codigo_sku", "stock"
    )

    context = {
        "prestamos":          prestamos,
        "total_prestamos":    total,
        "prestamos_activos":  activos,
        "prestamos_pendientes": pendientes,
        "prestamos_devueltos":  devueltos,
        "prestamos_vencidos":   vencidos,
        "proximos_vencer":      prox_vencer,
        "filtro_q":       filtro_q,
        "filtro_estado":  filtro_estado,
        "filtro_vencidos": filtro_vencidos,
        "usuarios_json":  json.dumps(list(usuarios_qs)),
        "productos_json": json.dumps(list(productos_qs)),
    }
    return render(request, "prestamo.html", context)


# ──────────────────────────────────────────────────────────────────────────────
#  VISTA USUARIO — Mis préstamos  (prestamo_usuario.html)
# ──────────────────────────────────────────────────────────────────────────────

@sesion_requerida
def prestamo_usuario_view(request):
    """Vista para que el aprendiz vea y solicite sus propios préstamos."""
    doc     = request.session.get("usuario_documento")
    usuario = get_object_or_404(Usuario, numero_documento=doc)

    if request.method == "POST":
        return _solicitar_prestamo(request, usuario)

    hoy       = date.today()
    tres_dias = hoy + timedelta(days=3)

    qs = Prestamo.objects.filter(usuario=usuario).prefetch_related(
        "items__producto"
    ).order_by("-fecha_prestamo")

    all_prestamos = _enriquecer_prestamos(qs)

    total_prestamos      = qs.count()
    total_activos        = qs.filter(estado="activo").count()
    pendientes_aprobacion = qs.filter(estado="pendiente").count()
    proximos_vencer      = qs.filter(
        estado__in=["activo", "parcial"],
        fecha_vencimiento__range=[hoy, tres_dias],
    ).count()
    vencidos_count = qs.filter(estado="vencido").count()

    productos_disponibles = Herramienta.objects.filter(stock__gt=0).order_by("nombre")

    context = {
        "usuario":             usuario,
        "all_prestamos":       all_prestamos,
        "total_prestamos":     total_prestamos,
        "total_activos":       total_activos,
        "pendientes_aprobacion": pendientes_aprobacion,
        "proximos_vencer":     proximos_vencer,
        "vencidos_count":      vencidos_count,
        "productos_disponibles": productos_disponibles,
    }
    return render(request, "prestamo_usuario.html", context)


def _solicitar_prestamo(request, usuario):
    """Crea una solicitud de préstamo en estado PENDIENTE desde la vista de usuario."""
    productos_ids = request.POST.getlist("producto[]")
    cantidades    = request.POST.getlist("cantidad[]")
    fecha_dev     = request.POST.get("fecha_devolucion_estimada") or None
    motivo        = request.POST.get("motivo", "").strip()

    if not motivo or len(motivo) < 10:
        messages.error(request, "El motivo debe tener al menos 10 caracteres.")
        return redirect("prestamo_usuario")

    if not productos_ids:
        messages.error(request, "Debes seleccionar al menos una herramienta.")
        return redirect("prestamo_usuario")

    prestamo = Prestamo.objects.create(
        usuario=usuario,
        estado="pendiente",
        fecha_vencimiento=fecha_dev,
        motivo_solicitud=motivo,
    )

    items_creados = 0
    for prod_id, cant in zip(productos_ids, cantidades):
        try:
            herramienta = Herramienta.objects.get(pk=prod_id, stock__gt=0)
            cantidad    = max(1, int(cant))
            DetallePrestamo.objects.create(
                prestamo=prestamo,
                producto=herramienta,
                cantidad=cantidad,
            )
            items_creados += 1
        except (Herramienta.DoesNotExist, ValueError):
            continue

    if items_creados == 0:
        prestamo.delete()
        messages.error(request, "No se pudo crear la solicitud: herramientas no disponibles.")
    else:
        messages.success(
            request,
            "Solicitud enviada. El administrador la revisará pronto.",
        )
    return redirect("prestamo_usuario")


# ──────────────────────────────────────────────────────────────────────────────
#  VISTA INSTRUCTOR — Préstamos de su ficha  (prestamo_instructores.html)
# ──────────────────────────────────────────────────────────────────────────────

@sesion_requerida
def prestamo_instructores_view(request):
    """
    Vista para instructores: ve los préstamos de los aprendices de su ficha.
    Pendiente de implementar lógica de filtrado por ficha/instructor.
    """
    doc      = request.session.get("usuario_documento")
    instructor = get_object_or_404(Usuario, numero_documento=doc)

    hoy       = date.today()
    tres_dias = hoy + timedelta(days=3)

    # Filtra aprendices de la misma ficha que el instructor
    aprendices_qs = Usuario.objects.filter(
        numero_ficha=instructor.numero_ficha,
        id_rol=Usuario.Rol.APRENDIZ,
    )

    qs = Prestamo.objects.filter(
        usuario__in=aprendices_qs
    ).select_related("usuario").prefetch_related(
        "items__producto"
    ).order_by("-fecha_prestamo")

    prestamos = _enriquecer_prestamos(qs)

    total        = qs.count()
    activos      = qs.filter(estado="activo").count()
    pendientes   = qs.filter(estado="pendiente").count()
    vencidos     = qs.filter(estado="vencido").count()
    prox_vencer  = qs.filter(
        estado__in=["activo", "parcial"],
        fecha_vencimiento__range=[hoy, tres_dias],
    ).count()

    context = {
        "instructor":        instructor,
        "prestamos":         prestamos,
        "total_prestamos":   total,
        "prestamos_activos": activos,
        "prestamos_pendientes": pendientes,
        "prestamos_vencidos":   vencidos,
        "proximos_vencer":      prox_vencer,
    }
    return render(request, "prestamo_intructores.html", context)


# ──────────────────────────────────────────────────────────────────────────────
#  VISTA — Devoluciones  (devoluciones.html)
# ──────────────────────────────────────────────────────────────────────────────

@sesion_requerida
def devoluciones_view(request):
    """
    Vista para gestionar devoluciones.
    Maneja: crear devolución, aceptar, rechazar.
    """

    if request.method == "POST":
        accion = request.POST.get("accion", "")

        # Crear devolución (wizard 3 pasos del modal)
        if accion == "crear_devolucion":
            prestamo_pk = request.POST.get("prestamo_pk")
            motivo      = request.POST.get("motivo", "").strip()
            item_pks    = request.POST.getlist("item_pk[]")
            cantidades  = request.POST.getlist("cantidad_dev[]")

            prestamo = get_object_or_404(Prestamo, pk=prestamo_pk)

            devolucion = Devolucion.objects.create(
                prestamo=prestamo,
                motivo=motivo,
            )

            items_devueltos = 0
            for item_pk, cant in zip(item_pks, cantidades):
                try:
                    item     = DetallePrestamo.objects.get(pk=item_pk, prestamo=prestamo)
                    cantidad = max(1, int(cant))
                    DetalleDevolucion.objects.create(
                        devolucion=devolucion,
                        producto=item.producto,
                        cantidad=cantidad,
                    )
                    items_devueltos += 1
                except (DetallePrestamo.DoesNotExist, ValueError):
                    continue

            if items_devueltos == 0:
                devolucion.delete()
                messages.error(request, "No se creó la devolución: sin ítems válidos.")
            else:
                # Determinar si es total o parcial
                total_items   = prestamo.items.count()
                devueltos_ahora = prestamo.items.filter(devuelto=True).count() + items_devueltos
                devolucion.devolucion_total = devueltos_ahora >= total_items
                devolucion.save(update_fields=["devolucion_total"])
                messages.success(request, f"Devolución #{devolucion.pk} registrada y pendiente de revisión.")

            return redirect("devoluciones")

        # Aceptar devolución
        elif accion == "aceptar_devolucion":
            dev_pk     = request.POST.get("dev_pk")
            devolucion = get_object_or_404(Devolucion, pk=dev_pk)

            for item_dev in devolucion.items.select_related("producto"):
                # Reponer stock
                item_dev.producto.stock += item_dev.cantidad
                item_dev.producto.save(update_fields=["stock"])

                # Marcar ítems del préstamo como devueltos
                DetallePrestamo.objects.filter(
                    prestamo=devolucion.prestamo,
                    producto=item_dev.producto,
                ).update(devuelto=True)

            # Actualizar estado del préstamo
            prestamo   = devolucion.prestamo
            pendientes = prestamo.items.filter(devuelto=False).count()
            prestamo.estado = "devuelto" if pendientes == 0 else "parcial"
            prestamo.save(update_fields=["estado"])

            devolucion.aceptada = True
            devolucion.save(update_fields=["aceptada"])
            messages.success(request, f"Devolución #{devolucion.pk} aceptada.")
            return redirect("devoluciones")

        # Rechazar devolución
        elif accion == "rechazar_devolucion":
            dev_pk         = request.POST.get("dev_pk")
            motivo_rechazo = request.POST.get("motivo_rechazo", "").strip()
            devolucion = get_object_or_404(Devolucion, pk=dev_pk)
            devolucion.aceptada       = False
            devolucion.motivo_rechazo = motivo_rechazo
            devolucion.save(update_fields=["aceptada", "motivo_rechazo"])
            messages.warning(request, f"Devolución #{devolucion.pk} rechazada.")
            return redirect("devoluciones")

    # ── GET ──────────────────────────────────────────────────────────────────
    devoluciones = Devolucion.objects.select_related(
        "prestamo__usuario"
    ).prefetch_related(
        "items__producto"
    ).order_by("-fecha_creacion")

    # Préstamos activos/parciales disponibles para nueva devolución
    prestamos_activos_qs = Prestamo.objects.filter(
        estado__in=["activo", "parcial"]
    ).select_related("usuario").prefetch_related("items__producto")

    prestamos_activos = _enriquecer_prestamos(prestamos_activos_qs)

    context = {
        "devoluciones":     devoluciones,
        "prestamos_activos": prestamos_activos,
    }
    return render(request, "devoluciones.html", context)


# ──────────────────────────────────────────────────────────────────────────────
#  ENDPOINT AJAX — Detalle de préstamo
# ──────────────────────────────────────────────────────────────────────────────

@sesion_requerida
def prestamo_detalle_json(request, pk):
    """Devuelve JSON con el detalle de un préstamo para el modal de aprobación."""
    prestamo = get_object_or_404(
        Prestamo.objects.select_related("usuario").prefetch_related("items__producto"),
        pk=pk,
    )
    items = [
        {
            "pk":       item.pk,
            "nombre":   item.producto.nombre,
            "sku":      item.producto.codigo_sku,
            "cantidad": item.cantidad,
            "stock":    item.producto.stock,
            "devuelto": item.devuelto,
            "serial":   item.serial_entregado or "",
        }
        for item in prestamo.items.all()
    ]
    data = {
        "pk":              prestamo.pk,
        "usuario":         prestamo.usuario.numero_documento,
        "nombre_usuario":  prestamo.usuario.nombre_completo,
        "estado":          prestamo.estado,
        "motivo_solicitud": prestamo.motivo_solicitud or "",
        "observaciones":   prestamo.observaciones or "",
        "fecha_prestamo":  prestamo.fecha_prestamo.strftime("%d/%m/%Y") if prestamo.fecha_prestamo else "",
        "fecha_vencimiento": prestamo.fecha_vencimiento.strftime("%d/%m/%Y") if prestamo.fecha_vencimiento else "",
        "items":           items,
    }
    return JsonResponse(data)