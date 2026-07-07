from django import forms

from .models import Prestamo, DetallePrestamo, DevolucionHerramienta
from inventario.models import Herramienta
from usuario.models import Usuario


# ──────────────────────────────────────────────────────────────
#  PRÉSTAMO
# ──────────────────────────────────────────────────────────────
class PrestamoForm(forms.ModelForm):
    class Meta:
        model = Prestamo
        fields = ["herramienta", "usuario", "observaciones"]
        labels = {
            "herramienta": "Herramienta",
            "usuario": "Solicitante",
            "observaciones": "Observaciones",
        }
        widgets = {
            "herramienta": forms.Select(
                attrs={"class": "form-select", "required": True}
            ),
            "usuario": forms.Select(
                attrs={"class": "form-select", "required": True}
            ),
            "observaciones": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": (
                        "Motivo del préstamo u observaciones" " (opcional)"
                    ),
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo herramientas disponibles
        self.fields["herramienta"].queryset = Herramienta.objects.filter(
            disponibilidad=True
        ).order_by("nombre_herramienta")
        self.fields["herramienta"].empty_label = (
            "Seleccione una herramienta..."
        )
        self.fields["usuario"].queryset = Usuario.objects.all().order_by(
            "nombre_completo"
        )
        self.fields["usuario"].empty_label = "Seleccione un usuario..."


# ──────────────────────────────────────────────────────────────
#  CAMBIO DE ESTADO DEL PRÉSTAMO (aprobar / rechazar / devolver)
# ──────────────────────────────────────────────────────────────
class CambiarEstadoPrestamoForm(forms.ModelForm):
    class Meta:
        model = Prestamo
        fields = ["id_estado", "observaciones"]
        labels = {
            "id_estado": "Nuevo estado",
            "observaciones": "Observaciones",
        }
        widgets = {
            "id_estado": forms.Select(
                attrs={"class": "form-select", "required": True}
            ),
            "observaciones": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Motivo del cambio de estado (opcional)",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["id_estado"].help_text = (
            "Seleccione el nuevo estado del préstamo."
        )
        self.fields["observaciones"].help_text = (
            "Motivo u observaciones del cambio de estado."
        )


# ──────────────────────────────────────────────────────────────
#  DETALLE DE PRÉSTAMO
# ──────────────────────────────────────────────────────────────
class DetallePrestamoForm(forms.ModelForm):
    class Meta:
        model = DetallePrestamo
        fields = ["herramienta", "cantidad"]
        labels = {
            "herramienta": "Herramienta",
            "cantidad": "Cantidad",
        }
        widgets = {
            "herramienta": forms.Select(
                attrs={"class": "form-select", "required": True}
            ),
            "cantidad": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                    "value": 1,
                    "required": True,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["herramienta"].queryset = Herramienta.objects.filter(
            disponibilidad=True
        ).order_by("nombre_herramienta")
        self.fields["herramienta"].empty_label = (
            "Seleccione una herramienta..."
        )


# ──────────────────────────────────────────────────────────────
#  DEVOLUCIÓN DE HERRAMIENTA
# ──────────────────────────────────────────────────────────────
class DevolucionHerramientaForm(forms.ModelForm):
    class Meta:
        model = DevolucionHerramienta
        fields = ["detalle_prestamo", "herramienta", "observaciones"]
        labels = {
            "detalle_prestamo": "Detalle de préstamo",
            "herramienta": "Herramienta devuelta",
            "observaciones": "Observaciones",
        }
        widgets = {
            "detalle_prestamo": forms.Select(
                attrs={"class": "form-select", "required": True}
            ),
            "herramienta": forms.Select(
                attrs={"class": "form-select", "required": True}
            ),
            "observaciones": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": (
                        "Estado de la herramienta al devolver" " (opcional)"
                    ),
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["detalle_prestamo"].queryset = (
            DetallePrestamo.objects.select_related(
                "prestamo__usuario", "herramienta"
            ).order_by("-prestamo__fecha_solicitud")
        )
        self.fields["detalle_prestamo"].empty_label = (
            "Seleccione un detalle..."
        )
        self.fields["herramienta"].queryset = (
            Herramienta.objects.all().order_by("nombre_herramienta")
        )
        self.fields["herramienta"].empty_label = (
            "Seleccione una herramienta..."
        )
