from django import forms

from .models import ConfiguracionSistema


# ──────────────────────────────────────────────────────────────
#  CONFIGURACIÓN DEL SISTEMA
# ──────────────────────────────────────────────────────────────
class ConfiguracionSistemaForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionSistema
        fields = ["almacenamiento", "database_url"]
        labels = {
            "almacenamiento": "Tipo de almacenamiento",
            "database_url": "URL de conexión (Neon / PostgreSQL)",
        }
        widgets = {
            "almacenamiento": forms.Select(
                attrs={"class": "form-select", "required": True}
            ),
            "database_url": forms.Textarea(
                attrs={
                    "class": "form-control font-monospace",
                    "rows": 3,
                    "placeholder": (
                        "postgresql://usuario:contraseña@host/base_de_datos"
                        " (requerido solo si elige Nube)"
                    ),
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["almacenamiento"].help_text = "Seleccione dónde se almacenarán los datos del sistema."
        self.fields["database_url"].help_text = "Requerido únicamente si elige almacenamiento en la Nube."

    def clean(self):
        cleaned_data = super().clean()
        almacenamiento = cleaned_data.get("almacenamiento")
        database_url = cleaned_data.get("database_url", "").strip()

        if almacenamiento == "nube" and not database_url:
            self.add_error(
                "database_url",
                "Debes ingresar la URL de conexión cuando el almacenamiento "
                "es 'Nube (PostgreSQL Neon)'.",
            )
        return cleaned_data
