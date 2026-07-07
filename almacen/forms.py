from django import forms
from .models import Almacen, Estante


class AlmacenForm(forms.ModelForm):
    class Meta:
        model = Almacen
        fields = ["nombre", "detalles", "capacidad"]
        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ingrese el nombre del almacén",
                    "required": True,
                }
            ),
            "detalles": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Descripción o detalles del almacén",
                    "rows": 3,
                }
            ),
            "capacidad": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Capacidad máxima (opcional)",
                    "min": 0,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nombre"].help_text = "Nombre descriptivo y único para el almacén."


class EstanteForm(forms.ModelForm):
    class Meta:
        model = Estante
        fields = ["almacen", "codigo", "detalles", "capacidad"]
        widgets = {
            "almacen": forms.Select(
                attrs={
                    "class": "form-select",
                    "required": True,
                }
            ),
            "codigo": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Código del estante (ej. E-01)",
                    "required": True,
                }
            ),
            "detalles": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Descripción o detalles del estante",
                    "rows": 3,
                }
            ),
            "capacidad": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Capacidad máxima (opcional)",
                    "min": 0,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Almacen

        self.fields["almacen"].queryset = Almacen.objects.all().order_by("nombre")
        self.fields["almacen"].empty_label = "Seleccione un almacén..."
