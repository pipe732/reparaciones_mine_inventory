from django.conf import settings
from django.db import models


class Usuario(models.Model):
    class TipoDocumento(models.TextChoices):
        CC = "CC", "Cédula de ciudadanía"
        CE = "CE", "Cédula de extranjería"
        TI = "TI", "Tarjeta de identidad"
        PA = "PA", "Pasaporte"

    class Rol(models.TextChoices):
        ADMIN = "ADMIN", "Administrador"
        INSTRUCTOR = "INSTRUCTOR", "Instructor"
        APRENDIZ = "APRENDIZ", "Aprendiz"
        ALMACENISTA = "ALMACENISTA", "Almacenista"

    numero_documento = models.CharField(max_length=20, primary_key=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil_usuario",
    )
    # id_rol(fk) en el MER: se deja como choices simples. Si más adelante
    # necesitas roles administrables desde BD, se cambia a FK a un
    # modelo Rol aparte.
    id_rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.APRENDIZ,
    )
    nombre_completo = models.CharField(max_length=200)
    correo = models.EmailField(unique=True)
    telefono = models.CharField(max_length=30)
    tipo_documento = models.CharField(
        max_length=2,
        choices=TipoDocumento.choices,
    )

    class Meta:
        db_table = "usuario"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return f"{self.nombre_completo} ({self.numero_documento})"
