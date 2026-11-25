"""Modeles pour les paiements (Orange Money / MTN MoMo / Cash, simules)."""
from django.db import models
from tenants.models import Tenant
from reservations.models import Reservation


class Paiement(models.Model):
    TYPE_CHOICES = [
        ("acompte", "Acompte"),
        ("solde", "Solde"),
        ("caution", "Caution"),
    ]
    METHODE_CHOICES = [
        ("om", "Orange Money"),
        ("momo", "MTN MoMo"),
        ("cash", "Especes"),
    ]
    STATUT_CHOICES = [
        ("en_attente", "En attente"),
        ("paye", "Paye"),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="paiements")
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name="paiements")
    montant = models.DecimalField(max_digits=10, decimal_places=0)
    type_paiement = models.CharField(max_length=20, choices=TYPE_CHOICES)
    methode = models.CharField(max_length=10, choices=METHODE_CHOICES, default="cash")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="en_attente")
    reference_transaction = models.CharField(max_length=100, blank=True)
    date_paiement = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_paiement"]

    def __str__(self):
        return f"{self.get_type_paiement_display()} - {self.montant} FCFA ({self.get_statut_display()})"


def solde_restant(reservation):
    paye = Paiement.objects.filter(
        reservation=reservation, statut="paye", type_paiement__in=["acompte", "solde"]
    ).aggregate(total=models.Sum("montant"))["total"] or 0
    total = reservation.prix_total or 0
    return total - paye
