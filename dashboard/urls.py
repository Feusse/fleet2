from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.accueil, name="accueil"),
    path("alertes/", views.alertes, name="alertes"),
    path("export/", views.export_rapport, name="export"),
]
