from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from inventario.models import Herramienta, PersonaRecaudo
from usuario.models import Usuario
from .forms import HerramientaForm, PersonaRecaudoForm


@login_required
def listado_herramientas(request):
    """
    Vista que muestra el listado de herramientas.
    Permite buscar por nombre o código de barras y filtrar por estado.
    """
    herramientas = (
        Herramienta.objects.select_related("recibida_por")
        .all()
        .order_by("codigo_barras")
    )
    query = request.GET.get("q", "")
    estado = request.GET.get("estado", "")
    instructor = request.GET.get("instructor", "")

    if query:
        herramientas = herramientas.filter(
            Q(nombre__icontains=query) | Q(codigo_barras__icontains=query)
        )

    if estado:
        herramientas = herramientas.filter(estado=estado)

    if instructor:
        herramientas = herramientas.filter(recibida_por__numero_documento=instructor)

    context = {
        "herramientas": herramientas,
        "query": query,
        "estado": estado,
        "instructor": instructor,
    }
    return render(request, "inventario/listado_herramientas.html", context)


@login_required
def detalle_herramienta(request, pk):
    """
    Vista que muestra los detalles de una herramienta específica.
    Incluye el historial de préstamos y recepciones.
    """
    herramienta = get_object_or_404(Herramienta, pk=pk)
    historial = herramienta.movimientos.select_related(
        "usuario_origen", "usuario_destino"
    ).order_by("-fecha_hora")
    context = {"herramienta": herramienta, "historial": historial}
    return render(request, "inventario/detalle_herramienta.html", context)


@login_required
def crear_herramienta(request):
    """
    Vista para crear una nueva herramienta.
    """
    if request.method == "POST":
        form = HerramientaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("inventario:listado_herramientas")
    else:
        form = HerramientaForm()
    context = {"form": form, "titulo": "Crear Herramienta"}
    return render(request, "inventario/herramienta_form.html", context)


@login_required
def editar_herramienta(request, pk):
    """
    Vista para editar una herramienta existente.
    """
    herramienta = get_object_or_404(Herramienta, pk=pk)
    if request.method == "POST":
        form = HerramientaForm(request.POST, request.FILES, instance=herramienta)
        if form.is_valid():
            form.save()
            return redirect("inventario:detalle_herramienta", pk=herramienta.pk)
    else:
        form = HerramientaForm(instance=herramienta)
    context = {
        "form": form,
        "herramienta": herramienta,
        "titulo": "Editar Herramienta",
    }
    return render(request, "inventario/herramienta_form.html", context)


@login_required
def eliminar_herramienta(request, pk):
    """
    Vista para eliminar una herramienta.
    """
    herramienta = get_object_or_404(Herramienta, pk=pk)
    herramienta.delete()
    return redirect("inventario:listado_herramientas")


@login_required
def listado_personas_recaudo(request):
    """
    Vista que muestra el listado de personas autorizadas para
    recibir herramientas.
    """
    personas = PersonaRecaudo.objects.all().order_by("nombre_completo")
    context = {"personas": personas}
    return render(request, "inventario/listado_personas.html", context)


@login_required
def crear_persona_recaudo(request):
    """
    Vista para crear una nueva persona autorizada.
    """
    if request.method == "POST":
        form = PersonaRecaudoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("inventario:listado_personas_recaudo")
    else:
        form = PersonaRecaudoForm()
    context = {"form": form, "titulo": "Crear Persona"}
    return render(request, "inventario/persona_form.html", context)


@login_required
def editar_persona_recaudo(request, pk):
    """
    Vista para editar una persona autorizada.
    """
    persona = get_object_or_404(PersonaRecaudo, pk=pk)
    if request.method == "POST":
        form = PersonaRecaudoForm(request.POST, request.FILES, instance=persona)
        if form.is_valid():
            form.save()
            return redirect("inventario:listado_personas_recaudo")
    else:
        form = PersonaRecaudoForm(instance=persona)
    context = {"form": form, "persona": persona, "titulo": "Editar Persona"}
    return render(request, "inventario/persona_form.html", context)


@login_required
def eliminar_persona_recaudo(request, pk):
    """
    Vista para eliminar una persona autorizada.
    """
    persona = get_object_or_404(PersonaRecaudo, pk=pk)
    persona.delete()
    return redirect("inventario:listado_personas_recaudo")


@login_required
def prestamo_herramienta(request):
    """
    Vista para prestar una herramienta.
    Permite seleccionar la herramienta, el usuario que la recibe
    y el instructor.
    """
    if request.method == "POST":
        herramienta_id = request.POST.get("herramienta")
        aprendiz_id = request.POST.get("aprendiz")
        instructor_id = request.POST.get("instructor")
        observaciones = request.POST.get("observaciones", "")

        herramienta = Herramienta.objects.get(pk=herramienta_id)
        aprendiz = Usuario.objects.get(numero_documento=aprendiz_id)
        instructor = Usuario.objects.get(numero_documento=instructor_id)

        herramienta.prestar(aprendiz, instructor, observaciones)

        return JsonResponse(
            {
                "success": True,
                "herramienta": {
                    "id": herramienta.id,
                    "codigo_barras": herramienta.codigo_barras,
                    "nombre": herramienta.nombre,
                    "estado": "PRESTADA",
                    "usuario_actual": aprendiz.nombre_completo,
                    "instructor_actual": instructor.nombre_completo,
                },
            }
        )

    return JsonResponse({"success": False, "error": "Método no permitido"})


@login_required
def recepcionar_herramienta(request):
    """
    Vista para recepcionar una herramienta prestada.
    """
    if request.method == "POST":
        herramienta_id = request.POST.get("herramienta")
        instructor_id = request.POST.get("instructor")
        observaciones = request.POST.get("observaciones", "")

        herramienta = Herramienta.objects.get(pk=herramienta_id)
        instructor = Usuario.objects.get(numero_documento=instructor_id)

        herramienta.recepcionar(instructor, observaciones)

        return JsonResponse(
            {
                "success": True,
                "herramienta": {
                    "id": herramienta.id,
                    "codigo_barras": herramienta.codigo_barras,
                    "nombre": herramienta.nombre,
                    "estado": herramienta.estado,
                    "usuario_actual": (
                        herramienta.usuario_actual.nombre_completo
                        if herramienta.usuario_actual
                        else ""
                    ),
                },
            }
        )

    return JsonResponse({"success": False, "error": "Método no permitido"})
