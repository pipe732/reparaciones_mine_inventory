from django import forms
from django.contrib.auth.models import User

from .models import Usuario


# ──────────────────────────────────────────────────────────────
#  REGISTRO DE USUARIO (con creación de User de Django)
# ──────────────────────────────────────────────────────────────
class RegistroUsuarioForm(forms.Form):
    """
    Formulario de registro completo.
    Crea tanto el User de Django como el perfil Usuario.
    """

    username = forms.CharField(
        max_length=150,
        label="Nombre de usuario",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nombre de usuario único",
                "required": True,
                "autocomplete": "username",
            }
        ),
    )
    nombre_completo = forms.CharField(
        max_length=200,
        label="Nombre completo",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nombre y apellidos completos",
                "required": True,
            }
        ),
    )
    correo = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "correo@ejemplo.com",
                "required": True,
                "autocomplete": "email",
            }
        ),
    )
    telefono = forms.CharField(
        max_length=30,
        label="Teléfono",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ej. 3001234567",
                "required": True,
            }
        ),
    )
    tipo_documento = forms.ChoiceField(
        choices=Usuario.TipoDocumento.choices,
        label="Tipo de documento",
        widget=forms.Select(attrs={"class": "form-select", "required": True}),
    )
    numero_documento = forms.CharField(
        max_length=20,
        label="Número de documento",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Número sin puntos ni guiones",
                "required": True,
            }
        ),
    )
    id_rol = forms.ChoiceField(
        choices=Usuario.Rol.choices,
        label="Rol",
        widget=forms.Select(attrs={"class": "form-select", "required": True}),
    )
    password1 = forms.CharField(
        label="Contraseña",
        min_length=8,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Mínimo 8 caracteres",
                "required": True,
                "autocomplete": "new-password",
            }
        ),
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        min_length=8,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Repite la contraseña",
                "required": True,
                "autocomplete": "new-password",
            }
        ),
    )

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Ese nombre de usuario ya está en uso.")
        return username

    def clean_correo(self):
        correo = self.cleaned_data.get("correo", "").strip().lower()
        if Usuario.objects.filter(correo=correo).exists():
            raise forms.ValidationError("Ese correo ya está registrado.")
        return correo

    def clean_numero_documento(self):
        documento = self.cleaned_data.get("numero_documento", "").strip()
        if Usuario.objects.filter(numero_documento=documento).exists():
            raise forms.ValidationError("Ya existe un usuario con ese número de documento.")
        return documento

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Las contraseñas no coinciden.")
        return cleaned_data


# ──────────────────────────────────────────────────────────────
#  EDICIÓN DE PERFIL
# ──────────────────────────────────────────────────────────────
class EditarPerfilForm(forms.ModelForm):
    """Permite al usuario editar sus datos básicos de perfil."""

    class Meta:
        model = Usuario
        fields = ["nombre_completo", "correo", "telefono"]
        labels = {
            "nombre_completo": "Nombre completo",
            "correo": "Correo electrónico",
            "telefono": "Teléfono",
        }
        widgets = {
            "nombre_completo": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nombre y apellidos",
                    "required": True,
                }
            ),
            "correo": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "correo@ejemplo.com",
                    "required": True,
                }
            ),
            "telefono": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Número de teléfono",
                    "required": True,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        # Aceptamos la instancia del usuario actual para validar unicidad de correo
        self.usuario_actual = kwargs.pop("usuario_actual", None)
        super().__init__(*args, **kwargs)

    def clean_correo(self):
        correo = self.cleaned_data.get("correo", "").strip().lower()
        qs = Usuario.objects.filter(correo=correo)
        if self.usuario_actual:
            qs = qs.exclude(numero_documento=self.usuario_actual.numero_documento)
        if qs.exists():
            raise forms.ValidationError("Ese correo ya está en uso por otro usuario.")
        return correo


# ──────────────────────────────────────────────────────────────
#  EDICIÓN ADMIN DE USUARIO (incluye rol)
# ──────────────────────────────────────────────────────────────
class EditarUsuarioAdminForm(forms.ModelForm):
    """Formulario para que el administrador edite cualquier usuario."""

    nueva_password = forms.CharField(
        required=False,
        label="Nueva contraseña (dejar vacío para no cambiar)",
        min_length=8,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nueva contraseña (opcional)",
                "autocomplete": "new-password",
            }
        ),
    )

    class Meta:
        model = Usuario
        fields = ["nombre_completo", "correo", "telefono", "id_rol"]
        labels = {
            "nombre_completo": "Nombre completo",
            "correo": "Correo electrónico",
            "telefono": "Teléfono",
            "id_rol": "Rol",
        }
        widgets = {
            "nombre_completo": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nombre y apellidos",
                    "required": True,
                }
            ),
            "correo": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "correo@ejemplo.com",
                    "required": True,
                }
            ),
            "telefono": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Número de teléfono",
                    "required": True,
                }
            ),
            "id_rol": forms.Select(attrs={"class": "form-select", "required": True}),
        }

    def __init__(self, *args, **kwargs):
        self.usuario_actual = kwargs.pop("usuario_actual", None)
        super().__init__(*args, **kwargs)

    def clean_correo(self):
        correo = self.cleaned_data.get("correo", "").strip().lower()
        qs = Usuario.objects.filter(correo=correo)
        if self.usuario_actual:
            qs = qs.exclude(numero_documento=self.usuario_actual.numero_documento)
        if qs.exists():
            raise forms.ValidationError("Ese correo ya está en uso por otro usuario.")
        return correo


# ──────────────────────────────────────────────────────────────
#  CAMBIO DE CONTRASEÑA
# ──────────────────────────────────────────────────────────────
class CambiarPasswordForm(forms.Form):
    password_actual = forms.CharField(
        label="Contraseña actual",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Contraseña actual",
                "required": True,
                "autocomplete": "current-password",
            }
        ),
    )
    password_nueva = forms.CharField(
        label="Nueva contraseña",
        min_length=8,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Mínimo 8 caracteres",
                "required": True,
                "autocomplete": "new-password",
            }
        ),
    )
    password_confirmar = forms.CharField(
        label="Confirmar nueva contraseña",
        min_length=8,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Repite la nueva contraseña",
                "required": True,
                "autocomplete": "new-password",
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        nueva = cleaned_data.get("password_nueva")
        confirmar = cleaned_data.get("password_confirmar")
        if nueva and confirmar and nueva != confirmar:
            self.add_error("password_confirmar", "Las contraseñas no coinciden.")
        return cleaned_data


# ──────────────────────────────────────────────────────────────
#  LOGIN
# ──────────────────────────────────────────────────────────────
class LoginForm(forms.Form):
    tipo_documento = forms.ChoiceField(
        choices=Usuario.TipoDocumento.choices,
        label="Tipo de documento",
        widget=forms.Select(attrs={"class": "form-select", "required": True}),
    )
    numero_documento = forms.CharField(
        max_length=20,
        label="Número de documento",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Número de documento",
                "required": True,
                "autocomplete": "username",
            }
        ),
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Contraseña",
                "required": True,
                "autocomplete": "current-password",
            }
        ),
    )
