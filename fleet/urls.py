from django.urls import path
from . import views

app_name = "fleet"

urlpatterns = [
    path("", views.liste_vehicules, name="liste"),
    path("nouveau/", views.creer_vehicule, name="creer"),
    path("<int:pk>/", views.detail_vehicule, name="detail"),
    path("<int:pk>/modifier/", views.modifier_vehicule, name="modifier"),
    path("<int:pk>/supprimer/", views.supprimer_vehicule, name="supprimer"),
]
