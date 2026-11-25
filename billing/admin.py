from django.contrib import admin
from .models import Paiement


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ["reservation", "type_paiement", "methode", "montant", "statut", "tenant"]
    list_filter = ["statut", "methode", "tenant"]
