from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .forms import AlmacenForm, EstanteForm
from .models import Almacen, Estante


@login_required
def almacenes_view(request):
    """
    Vista para listar, crear, editar y eliminar almacenes.
    """
    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "crear":
            form = AlmacenForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Almacén creado exitosamente.")
                return redirect("almacenes")
            else:
                messages.error(
                    request, "Error al crear el almacén. Verifique los datos."
                )
                almacenes = Almacen.objects.all().order_by("id_almacen")
                total_almacenes = Almacen.objects.count()
                total_estantes = Estante.objects.count()
                return render(
                    request,
                    "almacenes.html",
                    {
                        "almacenes": almacenes,
                        "total_almacenes": total_almacenes,
                        "total_estantes": total_estantes,
                        "form": form,
                        "show_modal": True,
                    },
                )

        elif accion == "editar":
            almacen_id = request.POST.get("almacen_id")
            almacen = get_object_or_404(Almacen, pk=almacen_id)
            form_editar = AlmacenForm(request.POST, instance=almacen)
            if form_editar.is_valid():
                form_editar.save()
                messages.success(request, "Almacén modificado exitosamente.")
                return redirect("almacenes")
            else:
                messages.error(
                    request, "Error al modificar el almacén. Verifique los datos."
                )
                almacenes = Almacen.objects.all().order_by("id_almacen")
                total_almacenes = Almacen.objects.count()
                total_estantes = Estante.objects.count()
                return render(
                    request,
                    "almacenes.html",
                    {
                        "almacenes": almacenes,
                        "total_almacenes": total_almacenes,
                        "total_estantes": total_estantes,
                        "form": AlmacenForm(),
                        "form_editar": form_editar,
                        "show_modal_editar": True,
                    },
                )

        elif accion == "eliminar":
            almacen_id = request.POST.get("almacen_id")
            almacen = get_object_or_404(Almacen, pk=almacen_id)
            almacen.delete()
            messages.success(request, "Almacén eliminado exitosamente.")
            return redirect("almacenes")

    # GET request
    almacenes = Almacen.objects.all().order_by("id_almacen")
    total_almacenes = Almacen.objects.count()
    total_estantes = Estante.objects.count()
    form = AlmacenForm()

    return render(
        request,
        "almacenes.html",
        {
            "almacenes": almacenes,
            "total_almacenes": total_almacenes,
            "total_estantes": total_estantes,
            "form": form,
        },
    )


@login_required
def detalle_almacen_view(request, pk):
    """
    Vista de detalle de un almacén que muestra información y sus estantes.
    """
    almacen = get_object_or_404(Almacen, pk=pk)
    estantes = almacen.estantes.all().order_by("id_estante")
    return render(
        request,
        "detalle_almacen.html",
        {
            "almacen": almacen,
            "estantes": estantes,
        },
    )


@login_required
def estantes_view(request):
    """
    Vista para listar, crear, editar y eliminar estantes.
    """
    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "crear":
            form = EstanteForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Estante creado exitosamente.")
                return redirect("estantes")
            else:
                messages.error(
                    request, "Error al crear el estante. Verifique los datos."
                )
                estantes = Estante.objects.select_related("almacen").all().order_by("id_estante")
                almacenes = Almacen.objects.all()
                total_estantes = Estante.objects.count()
                total_almacenes = Almacen.objects.count()
                return render(
                    request,
                    "estantes.html",
                    {
                        "estantes": estantes,
                        "almacenes": almacenes,
                        "total_estantes": total_estantes,
                        "total_almacenes": total_almacenes,
                        "form": form,
                        "show_modal": True,
                    },
                )

        elif accion == "editar":
            estante_id = request.POST.get("estante_id")
            estante = get_object_or_404(Estante, pk=estante_id)
            form_editar = EstanteForm(request.POST, instance=estante)
            if form_editar.is_valid():
                form_editar.save()
                messages.success(request, "Estante modificado exitosamente.")
                return redirect("estantes")
            else:
                messages.error(
                    request, "Error al modificar el estante. Verifique los datos."
                )
                estantes = Estante.objects.select_related("almacen").all().order_by("id_estante")
                almacenes = Almacen.objects.all()
                total_estantes = Estante.objects.count()
                total_almacenes = Almacen.objects.count()
                return render(
                    request,
                    "estantes.html",
                    {
                        "estantes": estantes,
                        "almacenes": almacenes,
                        "total_estantes": total_estantes,
                        "total_almacenes": total_almacenes,
                        "form": EstanteForm(),
                        "form_editar": form_editar,
                        "show_modal_editar": True,
                    },
                )

        elif accion == "eliminar":
            estante_id = request.POST.get("estante_id")
            estante = get_object_or_404(Estante, pk=estante_id)
            estante.delete()
            messages.success(request, "Estante eliminado exitosamente.")
            return redirect("estantes")

    # GET request
    estantes = Estante.objects.select_related("almacen").all().order_by("id_estante")
    almacenes = Almacen.objects.all()
    total_estantes = Estante.objects.count()
    total_almacenes = Almacen.objects.count()
    form = EstanteForm()

    return render(
        request,
        "estantes.html",
        {
            "estantes": estantes,
            "almacenes": almacenes,
            "total_estantes": total_estantes,
            "total_almacenes": total_almacenes,
            "form": form,
        },
    )
