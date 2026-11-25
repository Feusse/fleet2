from django.contrib import admin
from .models import Vehicule


@admin.register(Vehicule)
class VehiculeAdmin(admin.ModelAdmin):
    list_display = ["immatriculation", "marque", "modele", "tenant", "statut", "prix_journalier"]
    list_filter = ["statut", "categorie", "tenant"]
    search_fields = ["immatriculation", "marque", "modele"]
