from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UsuarioManager(BaseUserManager):
    # crea usuarios identificados por correo
    def create_user(self, correo, password=None, **extra):
        usuario = self.model(correo=correo.lower(), **extra)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, correo, password=None, **extra):
        return self.create_user(correo, password, is_staff=True, is_superuser=True, **extra)


class Usuario(AbstractBaseUser, PermissionsMixin):
    correo = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "correo"
    objects = UsuarioManager()

    def __str__(self):
        return self.correo
