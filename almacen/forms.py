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
