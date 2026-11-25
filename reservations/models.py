"""
Modèles Client et Réservation.
LOGIQUE CRITIQUE : impossible d'avoir deux réservations actives qui se chevauchent
sur le même véhicule. Vérifié dans clean() (niveau code) et dans la vue
(transaction + select_for_update) pour éviter les races conditions.
"""
from django.db import models
from django.core.exceptions import ValidationError
from tenants.models import Tenant
from fleet.models import Vehicule


class Client(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="clients")
    nom = models.CharField(max_length=150)
    telephone_whatsapp = models.CharField(max_length=30)
    cni = models.CharField(max_length=50, blank=True)
    date_ajout = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class Reservation(models.Model):
    STATUT_CHOICES = [
        ("devis", "Devis"),
        ("confirmee", "Confirmée"),
        ("en_cours", "En cours"),
        ("terminee", "Terminée"),
        ("annulee", "Annulée"),
    ]
    STATUTS_BLOQUANTS = ["confirmee", "en_cours"]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="reservations")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="reservations")
    vehicule = models.ForeignKey(Vehicule, on_delete=models.CASCADE, related_name="reservations")
    date_depart = models.DateField()
    date_retour = models.DateField()
    prix_total = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="devis")
    kilometrage_retour = models.PositiveIntegerField(blank=True, null=True)
    etat_retour = models.TextField(blank=True)
    frais_supplementaires = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_depart"]

    def __str__(self):
        return f"{self.client} - {self.vehicule} ({self.date_depart} -> {self.date_retour})"

    def clean(self):
        if self.date_depart and self.date_retour and self.date_depart >= self.date_retour:
            raise ValidationError("La date de retour doit être après la date de départ.")
        if self.statut in self.STATUTS_BLOQUANTS:
            chevauchement = self.chevauchement_existant()
            if chevauchement:
                raise ValidationError(
                    f"Véhicule déjà réservé du {chevauchement.date_depart} "
                    f"au {chevauchement.date_retour}."
                )

    def chevauchement_existant(self):
        qs = Reservation.objects.filter(
            vehicule=self.vehicule,
            statut__in=self.STATUTS_BLOQUANTS,
            date_depart__lt=self.date_retour,
            date_retour__gt=self.date_depart,
        ).exclude(pk=self.pk)
        return qs.first()

    def calculer_prix(self):
        nb_jours = (self.date_retour - self.date_depart).days
        return nb_jours * self.vehicule.prix_journalier

    def save(self, *args, **kwargs):
        if not self.prix_total:
            self.prix_total = self.calculer_prix()
        self.full_clean()
        super().save(*args, **kwargs)
