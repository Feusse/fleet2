from django.urls import path
from . import views

app_name = "reservations"

urlpatterns = [
    path("", views.liste_reservations, name="liste"),
    path("nouvelle/", views.creer_reservation, name="creer"),
    path("<int:pk>/", views.detail_reservation, name="detail"),
    path("<int:pk>/confirmer/", views.confirmer_reservation, name="confirmer"),
    path("<int:pk>/demarrer/", views.demarrer_location, name="demarrer"),
    path("<int:pk>/retour/", views.retour_vehicule, name="retour"),
    path("<int:pk>/contrat/", views.generer_contrat, name="contrat"),
    path("clients/", views.liste_clients, name="clients"),
    path("clients/nouveau/", views.creer_client, name="creer_client"),
]
