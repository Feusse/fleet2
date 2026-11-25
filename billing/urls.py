from django.urls import path
from . import views

app_name = "billing"

urlpatterns = [
    path("reservation/<int:reservation_pk>/ajouter/", views.ajouter_paiement, name="ajouter"),
    path("<int:pk>/marquer-paye/", views.marquer_paye, name="marquer_paye"),
    path("<int:pk>/payer-en-ligne/", views.payer_en_ligne, name="payer_en_ligne"),
    path("notification-cinetpay/", views.notification_cinetpay, name="notification_cinetpay"),
]
