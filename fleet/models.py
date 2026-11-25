"""Modèles pour la gestion de la flotte de véhicules."""
from django.db import models
from tenants.models import Tenant


class Vehicule(models.Model):
    CATEGORIE_CHOICES = [
        ("berline", "Berline"),
        ("suv", "SUV"),
        ("pickup", "Pick-up"),
        ("minibus", "Minibus"),
        ("autre", "Autre"),
    ]
    STATUT_CHOICES = [
        ("disponible", "Disponible"),
        ("loue", "Loué"),
        ("maintenance", "Maintenance"),
        ("indisponible", "Indisponible"),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="vehicules")
    immatriculation = models.CharField(max_length=30)
    marque = models.CharField(max_length=60)
    modele = models.CharField(max_length=60)
    categorie = models.CharField(max_length=20, choices=CATEGORIE_CHOICES, default="berline")
    kilometrage_actuel = models.PositiveIntegerField(default=0)
    kilometrage_dernier_entretien = models.PositiveIntegerField(default=0)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="disponible")
    photo = models.ImageField(upload_to="vehicules/", blank=True, null=True)
    prix_journalier = models.DecimalField(max_digits=10, decimal_places=0)
    caution = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    date_expiration_assurance = models.DateField(blank=True, null=True)
    date_ajout = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("tenant", "immatriculation")
        ordering = ["-date_ajout"]

    def __str__(self):
        return f"{self.marque} {self.modele} ({self.immatriculation})"

    @property
    def badge_couleur(self):
        return {
            "disponible": "green",
            "loue": "red",
            "maintenance": "orange",
            "indisponible": "gray",
        }.get(self.statut, "gray")

    @property
    def vidange_necessaire(self):
        return (self.kilometrage_actuel - self.kilometrage_dernier_entretien) > 5000
