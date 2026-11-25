from django.contrib import admin
from .models import Client, Reservation


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ["nom", "telephone_whatsapp", "tenant"]
    search_fields = ["nom", "telephone_whatsapp"]


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ["client", "vehicule", "date_depart", "date_retour", "statut", "tenant"]
    list_filter = ["statut", "tenant"]
