from django import forms
from .models import (
    Mantenimiento,
    DetalleMantenimiento,
    BitacoraEstado,
    TipoEstado,
    TipoMantenimiento,
)
from inventario.models import Herramienta


class MantenimientoForm(forms.ModelForm):
    tipo_mantenimiento = forms.ModelChoiceField(
        queryset=TipoMantenimiento.objects.all(),
        to_field_name="nombre",
        empty_label="Seleccione un tipo...",
        widget=forms.Select(attrs={"class": "form-select", "required": True}),
        label="Tipo de Mantenimiento",
    )

    class Meta:
        model = Mantenimiento
        fields = ["herramienta", "tipo_mantenimiento", "descripcion", "fecha_ingreso"]
        widgets = {
            "herramienta": forms.Select(
                attrs={"class": "form-select", "required": True}
            ),
            "descripcion": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Describa el motivo del ingreso",
                }
            ),
            "fecha_ingreso": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                    "required": True,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo permitir herramientas que existan en el sistema
        self.fields["herramienta"].queryset = Herramienta.objects.all().order_by(
            "nombre"
        )


class DetalleMantenimientoForm(forms.ModelForm):
    class Meta:
        model = DetalleMantenimiento
        fields = ["accion_realizada", "materiales_usados"]
        widgets = {
            "accion_realizada": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Acciones tomadas...",
                    "required": True,
                }
            ),
            "materiales_usados": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Materiales o repuestos usados (opcional)",
                }
            ),
        }


class BitacoraEstadoForm(forms.ModelForm):
    estado = forms.ModelChoiceField(
        queryset=TipoEstado.objects.all(),
        to_field_name="nombre",
        empty_label="Seleccione un estado...",
        widget=forms.Select(attrs={"class": "form-select", "required": True}),
        label="Nuevo Estado",
    )

    class Meta:
        model = BitacoraEstado
        fields = ["estado", "descripcion"]
        widgets = {
            "descripcion": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Observaciones sobre el estado actual...",
                    "required": True,
                }
            ),
        }


class TipoEstadoForm(forms.ModelForm):
    NIVEL_CHOICES = [
        ("success", "Normal / Bueno"),
        ("warning", "Atención / En mantenimiento"),
        ("danger", "Crítico / Dañado"),
    ]
    nivel = forms.ChoiceField(
        choices=NIVEL_CHOICES,
        widget=forms.Select(attrs={"class": "form-select", "required": True}),
        label="Nivel de Gravedad",
    )

    class Meta:
        model = TipoEstado
        fields = ["nombre", "nivel"]
        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nombre del estado (ej. Excelente, Dañado)",
                    "required": True,
                }
            ),
        }


class TipoMantenimientoForm(forms.ModelForm):
    class Meta:
        model = TipoMantenimiento
        fields = ["nombre", "descripcion"]
        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nombre del tipo (ej. Preventivo)",
                    "required": True,
                }
            ),
            "descripcion": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Descripción breve",
                }
            ),
        }
