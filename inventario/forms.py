from django import forms

from .models import (
    CategoriaHerramienta,
    Herramienta,
    Inventario,
    Proveedor,
    Movimiento,
    DetalleMovimiento,
)
from almacen.models import Estante


# ──────────────────────────────────────────────────────────────
#  CATEGORÍA DE HERRAMIENTA
# ──────────────────────────────────────────────────────────────
class CategoriaHerramientaForm(forms.ModelForm):
    class Meta:
        model = CategoriaHerramienta
        fields = ["descripcion", "tipo_herramienta"]
        labels = {
            "descripcion": "Descripción",
            "tipo_herramienta": "Tipo de herramienta",
        }
        widgets = {
            "descripcion": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ej. Herramientas de corte",
                    "required": True,
                }
            ),
            "tipo_herramienta": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ej. Manual, Eléctrica",
                    "required": True,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["descripcion"].help_text = "Descripción breve y única de la categoría."


# ──────────────────────────────────────────────────────────────
#  HERRAMIENTA
# ──────────────────────────────────────────────────────────────
class HerramientaForm(forms.ModelForm):
    class Meta:
        model = Herramienta
        fields = [
            "codigo_sku",
            "nombre_herramienta",
            "categoria_herramienta",
            "descripcion",
            "disponibilidad",
        ]
        labels = {
            "codigo_sku": "Código SKU",
            "nombre_herramienta": "Nombre",
            "categoria_herramienta": "Categoría",
            "descripcion": "Descripción",
            "disponibilidad": "Disponible",
        }
        widgets = {
            "codigo_sku": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ej. TOOL-001",
                    "required": True,
                }
            ),
            "nombre_herramienta": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nombre de la herramienta",
                    "required": True,
                }
            ),
            "categoria_herramienta": forms.Select(
                attrs={"class": "form-select", "required": True}
            ),
            "descripcion": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Descripción detallada de la herramienta",
                    "required": True,
                }
            ),
            "disponibilidad": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categoria_herramienta"].queryset = (
            CategoriaHerramienta.objects.all().order_by("descripcion")
        )
        self.fields["categoria_herramienta"].empty_label = "Seleccione una categoría..."


# ──────────────────────────────────────────────────────────────
#  INVENTARIO
# ──────────────────────────────────────────────────────────────
class InventarioForm(forms.ModelForm):
    class Meta:
        model = Inventario
        fields = ["herramienta", "estante", "cantidad", "responsable", "observaciones"]
        labels = {
            "herramienta": "Herramienta",
            "estante": "Estante / Ubicación",
            "cantidad": "Cantidad",
            "responsable": "Responsable",
            "observaciones": "Observaciones",
        }
        widgets = {
            "herramienta": forms.Select(
                attrs={"class": "form-select", "required": True}
            ),
            "estante": forms.Select(
                attrs={"class": "form-select", "required": True}
            ),
            "cantidad": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "placeholder": "0",
                    "required": True,
                }
            ),
            "responsable": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nombre del responsable",
                    "required": True,
                }
            ),
            "observaciones": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Observaciones adicionales (opcional)",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["herramienta"].queryset = Herramienta.objects.all().order_by(
            "nombre_herramienta"
        )
        self.fields["herramienta"].empty_label = "Seleccione una herramienta..."
        self.fields["estante"].queryset = Estante.objects.select_related(
            "almacen"
        ).order_by("almacen__nombre", "codigo")
        self.fields["estante"].empty_label = "Seleccione un estante..."


# ──────────────────────────────────────────────────────────────
#  PROVEEDOR
# ──────────────────────────────────────────────────────────────
class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = [
            "nit_proveedor",
            "telefono_contacto",
            "correo_proveedor",
            "descripcion",
        ]
        labels = {
            "nit_proveedor": "NIT / RUT",
            "telefono_contacto": "Teléfono de contacto",
            "correo_proveedor": "Correo electrónico",
            "descripcion": "Descripción",
        }
        widgets = {
            "nit_proveedor": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ej. 900123456-1",
                    "required": True,
                }
            ),
            "telefono_contacto": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ej. 3001234567",
                    "required": True,
                }
            ),
            "correo_proveedor": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "proveedor@empresa.com",
                    "required": True,
                }
            ),
            "descripcion": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Información adicional del proveedor (opcional)",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nit_proveedor"].help_text = "NIT o RUT del proveedor (sin espacios)."
        self.fields["correo_proveedor"].help_text = "Correo de contacto principal."


# ──────────────────────────────────────────────────────────────
#  MOVIMIENTO
# ──────────────────────────────────────────────────────────────
TIPO_MOVIMIENTO_CHOICES = [
    ("", "Seleccione un tipo..."),
    ("ENTRADA", "Entrada"),
    ("SALIDA", "Salida"),
    ("AJUSTE", "Ajuste"),
    ("TRANSFERENCIA", "Transferencia"),
]


class MovimientoForm(forms.ModelForm):
    tipo_de_movimiento = forms.ChoiceField(
        choices=TIPO_MOVIMIENTO_CHOICES,
        widget=forms.Select(attrs={"class": "form-select", "required": True}),
        label="Tipo de movimiento",
    )

    class Meta:
        model = Movimiento
        fields = ["inventario", "proveedor", "cantidad", "tipo_de_movimiento"]
        labels = {
            "inventario": "Inventario",
            "proveedor": "Proveedor (opcional)",
            "cantidad": "Cantidad",
        }
        widgets = {
            "inventario": forms.Select(
                attrs={"class": "form-select", "required": True}
            ),
            "proveedor": forms.Select(attrs={"class": "form-select"}),
            "cantidad": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                    "placeholder": "Cantidad de unidades",
                    "required": True,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["inventario"].queryset = Inventario.objects.select_related(
            "herramienta"
        ).order_by("herramienta__nombre_herramienta")
        self.fields["inventario"].empty_label = "Seleccione un inventario..."
        self.fields["proveedor"].queryset = Proveedor.objects.all().order_by(
            "nit_proveedor"
        )
        self.fields["proveedor"].empty_label = "Sin proveedor"
        self.fields["proveedor"].required = False


# ──────────────────────────────────────────────────────────────
#  DETALLE DE MOVIMIENTO
# ──────────────────────────────────────────────────────────────
class DetalleMovimientoForm(forms.ModelForm):
    class Meta:
        model = DetalleMovimiento
        fields = ["inventario", "descripcion"]
        labels = {
            "inventario": "Inventario relacionado",
            "descripcion": "Descripción del detalle",
        }
        widgets = {
            "inventario": forms.Select(
                attrs={"class": "form-select", "required": True}
            ),
            "descripcion": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Detalle adicional del movimiento (opcional)",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["inventario"].queryset = Inventario.objects.select_related(
            "herramienta"
        ).order_by("herramienta__nombre_herramienta")
        self.fields["inventario"].empty_label = "Seleccione un inventario..."
