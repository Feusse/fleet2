from django.urls import path
from . import views

app_name = "tenants"

urlpatterns = [
    path("", views.accueil_redirect, name="accueil"),
    path("connexion/", views.ConnexionView.as_view(), name="connexion"),
    path("inscription/", views.inscription, name="inscription"),
    path("deconnexion/", views.deconnexion, name="deconnexion"),
    path("equipe/", views.equipe, name="equipe"),
    path("equipe/ajouter/", views.ajouter_gestionnaire, name="ajouter_gestionnaire"),
    path("equipe/<int:pk>/desactiver/", views.desactiver_membre, name="desactiver_membre"),
]
