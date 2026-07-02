from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from usuario.decorators import login_required
from .forms import (
    MantenimientoForm,
    DetalleMantenimientoForm,
    BitacoraEstadoForm,
    TipoEstadoForm,
    TipoMantenimientoForm,
)
from .models import Mantenimiento, DetalleMantenimiento, BitacoraEstado, TipoEstado, TipoMantenimiento
from inventario.models import Herramienta


# ──────────────────────────────────────────────────────────────────────────────
#  1. ESTADO ACTUAL DE HERRAMIENTAS
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def estado_actual_lista_view(request):
    """
    Vista que muestra la lista de herramientas del inventario y su estado actual
    de mantenimiento, basado en el historial y bitácoras.
    """
    herramientas = Herramienta.objects.all().order_by("nombre")
    
    # Enriquecer cada herramienta con su estado de mantenimiento
    for h in herramientas:
        mantenimiento_activo = h.mantenimientos.filter(fecha_salida__isnull=True).order_by("-fecha_ingreso").first()
        if mantenimiento_activo:
            h.en_mantenimiento = True
            h.mantenimiento_id = mantenimiento_activo.id_mantenimiento
            h.tipo_mantenimiento = mantenimiento_activo.tipo_mantenimiento
            
            # Obtener el último estado registrado en la bitácora de este mantenimiento
            ultimo_estado = mantenimiento_activo.bitacoras.order_by("-id_bitacora_estado").first()
            h.estado_mantenimiento = ultimo_estado.estado if ultimo_estado else "Ingresado"
            h.estado_nivel = ultimo_estado.nivel_estado if ultimo_estado else "warning"
        else:
            h.en_mantenimiento = False
            h.estado_mantenimiento = "Disponible"
            h.estado_nivel = "success"

    context = {
        "herramientas": herramientas,
    }
    return render(request, "mantenimiento/estado_actual.html", context)


# ──────────────────────────────────────────────────────────────────────────────
#  2. CATÁLOGO: TIPOS DE ESTADO
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def tipo_estado_lista_view(request):
    """
    Listar los tipos de estado disponibles.
    """
    estados = TipoEstado.objects.all().order_by("nombre")
    form = TipoEstadoForm()
    
    if request.method == "POST":
        accion = request.POST.get("accion")
        if accion == "eliminar":
            estado_id = request.POST.get("estado_id")
            estado = get_object_or_404(TipoEstado, pk=estado_id)
            estado.delete()
            messages.success(request, "Tipo de estado eliminado correctamente.")
            return redirect("mantenimiento:tipo_estado_lista")

    context = {
        "estados": estados,
        "form": form,
    }
    return render(request, "mantenimiento/tipos_estado.html", context)


@login_required
def tipo_estado_nuevo_view(request):
    """
    Crear un nuevo tipo de estado.
    """
    if request.method == "POST":
        form = TipoEstadoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Tipo de estado creado exitosamente.")
            return redirect("mantenimiento:tipo_estado_lista")
        else:
            messages.error(request, "Error al crear el tipo de estado. Verifique los datos.")
            estados = TipoEstado.objects.all().order_by("nombre")
            context = {
                "estados": estados,
                "form": form,
                "show_modal": True,
            }
            return render(request, "mantenimiento/tipos_estado.html", context)
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
            messages.success(request, "Tipo de estado modificado correctamente.")
            return redirect("mantenimiento:tipo_estado_lista")
        else:
            messages.error(request, "Error al modificar el estado.")
    else:
        form = TipoEstadoForm(instance=estado)

    context = {
        "estado": estado,
        "form": form,
    }
    return render(request, "mantenimiento/tipo_estado_form.html", context)


# ──────────────────────────────────────────────────────────────────────────────
#  3. CATÁLOGO: TIPOS DE MANTENIMIENTO
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def tipo_mantenimiento_lista_view(request):
    """
    Listar los tipos de mantenimiento.
    """
    tipos = TipoMantenimiento.objects.all().order_by("nombre")
    form = TipoMantenimientoForm()
    
    if request.method == "POST":
        accion = request.POST.get("accion")
        if accion == "eliminar":
            tipo_id = request.POST.get("tipo_id")
            tipo = get_object_or_404(TipoMantenimiento, pk=tipo_id)
            tipo.delete()
            messages.success(request, "Tipo de mantenimiento eliminado.")
            return redirect("mantenimiento:tipo_mantenimiento_lista")

    context = {
        "tipos": tipos,
        "form": form,
    }
    return render(request, "mantenimiento/tipos_mantenimiento.html", context)


@login_required
def tipo_mantenimiento_crear_view(request):
    """
    Crear un tipo de mantenimiento.
    """
    if request.method == "POST":
        form = TipoMantenimientoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Tipo de mantenimiento creado.")
            return redirect("mantenimiento:tipo_mantenimiento_lista")
        else:
            messages.error(request, "Error al crear el tipo de mantenimiento.")
            tipos = TipoMantenimiento.objects.all().order_by("nombre")
            context = {
                "tipos": tipos,
                "form": form,
                "show_modal": True,
            }
            return render(request, "mantenimiento/tipos_mantenimiento.html", context)
    return redirect("mantenimiento:tipo_mantenimiento_lista")


@login_required
def tipo_mantenimiento_editar_view(request, pk):
    """
    Editar un tipo de mantenimiento.
    """
    tipo = get_object_or_404(TipoMantenimiento, pk=pk)
    if request.method == "POST":
        form = TipoMantenimientoForm(request.POST, instance=tipo)
        if form.is_valid():
            form.save()
            messages.success(request, "Tipo de mantenimiento modificado.")
            return redirect("mantenimiento:tipo_mantenimiento_lista")
        else:
            messages.error(request, "Error al modificar el tipo de mantenimiento.")
    else:
        form = TipoMantenimientoForm(instance=tipo)

    context = {
        "tipo": tipo,
        "form": form,
    }
    return render(request, "mantenimiento/tipo_mantenimiento_form.html", context)


# ──────────────────────────────────────────────────────────────────────────────
#  4. GESTIÓN DE MANTENIMIENTOS
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def mantenimiento_lista_view(request):
    """
    Lista de mantenimientos y registro de nuevos.
    """
    mantenimientos = Mantenimiento.objects.select_related("herramienta").all().order_by("-fecha_ingreso")
    form = MantenimientoForm()
    
    total_activos = Mantenimiento.objects.filter(fecha_salida__isnull=True).count()
    total_finalizados = Mantenimiento.objects.filter(fecha_salida__isnull=False).count()

    if request.method == "POST":
        accion = request.POST.get("accion")
        
        if accion == "crear":
            form = MantenimientoForm(request.POST)
            if form.is_valid():
                mantenimiento = form.save()
                
                # Crear automáticamente una entrada inicial en la bitácora del estado
                BitacoraEstado.objects.create(
                    mantenimiento=mantenimiento,
                    estado="Ingresado",
                    nivel_estado="warning",
                    descripcion="Ingreso inicial al módulo de mantenimiento."
                )
                
                messages.success(request, "Mantenimiento registrado correctamente.")
                return redirect("mantenimiento:mantenimiento_lista")
            else:
                messages.error(request, "Error al registrar el mantenimiento.")
                context = {
                    "mantenimientos": mantenimientos,
                    "form": form,
                    "total_activos": total_activos,
                    "total_finalizados": total_finalizados,
                    "show_modal": True,
                }
                return render(request, "mantenimiento/mantenimientos.html", context)
                
        elif accion == "eliminar":
            mantenimiento_id = request.POST.get("mantenimiento_id")
            mantenimiento = get_object_or_404(Mantenimiento, pk=mantenimiento_id)
            mantenimiento.delete()
            messages.success(request, "Registro de mantenimiento eliminado.")
            return redirect("mantenimiento:mantenimiento_lista")

    context = {
        "mantenimientos": mantenimientos,
        "form": form,
        "total_activos": total_activos,
        "total_finalizados": total_finalizados,
    }
    return render(request, "mantenimiento/mantenimientos.html", context)


@login_required
def mantenimiento_detalle_view(request, pk):
    """
    Detalle de un mantenimiento, agregando notas y actualizando estados.
    """
    mantenimiento = get_object_or_404(Mantenimiento, pk=pk)
    detalles = mantenimiento.detalles.all().order_by("-creado_en")
    bitacoras = mantenimiento.bitacoras.all().order_by("-id_bitacora_estado")
    
    detalle_form = DetalleMantenimientoForm()
    estado_form = BitacoraEstadoForm()

    if request.method == "POST":
        accion = request.POST.get("accion")
        
        if accion == "agregar_detalle":
            form = DetalleMantenimientoForm(request.POST)
            if form.is_valid():
                det = form.save(commit=False)
                det.mantenimiento = mantenimiento
                det.save()
                messages.success(request, "Bitácora de acción agregada.")
                return redirect("mantenimiento:mantenimiento_detalle", pk=mantenimiento.pk)
            else:
                messages.error(request, "Error al agregar acción.")
                
        elif accion == "actualizar_estado":
            form = BitacoraEstadoForm(request.POST)
            if form.is_valid():
                bit = form.save(commit=False)
                bit.mantenimiento = mantenimiento
                
                # Obtener el nivel de gravedad desde el catálogo TipoEstado
                tipo = TipoEstado.objects.filter(nombre=bit.estado).first()
                bit.nivel_estado = tipo.nivel if tipo else "warning"
                
                bit.save()
                messages.success(request, "Estado de mantenimiento actualizado.")
                return redirect("mantenimiento:mantenimiento_detalle", pk=mantenimiento.pk)
            else:
                messages.error(request, "Error al actualizar estado.")
                
        elif accion == "finalizar":
            mantenimiento.fecha_salida = timezone.now()
            mantenimiento.save()
            
            # Registrar estado finalizado en la bitácora
            BitacoraEstado.objects.create(
                mantenimiento=mantenimiento,
                estado="Finalizado / Disponible",
                nivel_estado="success",
                descripcion="Mantenimiento concluido. Herramienta devuelta al inventario."
            )
            messages.success(request, "Mantenimiento finalizado con éxito.")
            return redirect("mantenimiento:mantenimiento_detalle", pk=mantenimiento.pk)

    context = {
        "mantenimiento": mantenimiento,
        "detalles": detalles,
        "bitacoras": bitacoras,
        "detalle_form": detalle_form,
        "estado_form": estado_form,
    }
    return render(request, "mantenimiento/detalle_mantenimiento.html", context)
