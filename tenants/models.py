"""
Modèles pour la gestion des agences (tenants) et des utilisateurs.
Chaque agence = 1 tenant isolé. Un tenant ne voit jamais les données d'un autre.
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify


class Tenant(models.Model):
    """Une agence de location = un tenant isolé."""

    PLAN_CHOICES = [
        ("essai", "Essai gratuit"),
        ("standard", "Standard"),
        ("premium", "Premium"),
    ]

    nom_agence = models.CharField(max_length=150)
    slug_unique = models.SlugField(max_length=160, unique=True, blank=True)
    logo = models.ImageField(upload_to="logos/", blank=True, null=True)
    telephone = models.CharField(max_length=30, blank=True)
    ville = models.CharField(max_length=100, blank=True)
    plan_abonnement = models.CharField(max_length=20, choices=PLAN_CHOICES, default="essai")
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Agence (Tenant)"
        verbose_name_plural = "Agences (Tenants)"

    def save(self, *args, **kwargs):
        if not self.slug_unique:
            base_slug = slugify(self.nom_agence)
            slug = base_slug
            i = 1
            while Tenant.objects.filter(slug_unique=slug).exists():
                slug = f"{base_slug}-{i}"
                i += 1
            self.slug_unique = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nom_agence


class User(AbstractUser):
    """Utilisateur lié obligatoirement à un tenant (sauf superuser Django admin)."""

    ROLE_CHOICES = [
        ("patron", "Patron"),
        ("gestionnaire", "Gestionnaire"),
    ]

    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="users", null=True, blank=True
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="gestionnaire")
    telephone = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return f"{self.username} ({self.tenant.nom_agence if self.tenant else 'sans agence'})"
