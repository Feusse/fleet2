"""Routage principal de Fleet.cm."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from tenants import views_public

urlpatterns = [
    path("admin/", admin.site.urls),

    # Auth / inscription agence
    path("", include("tenants.urls")),

    # Espace interne (necessite login + tenant)
    path("dashboard/", include("dashboard.urls")),
    path("vehicules/", include("fleet.urls")),
    path("reservations/", include("reservations.urls")),
    path("paiements/", include("billing.urls")),

    # Page publique de reservation par agence : /r/<slug>/
    path("r/<slug:slug>/", views_public.page_agence, name="page_agence"),
    path("r/<slug:slug>/vehicule/<int:vehicule_id>/reserver/", views_public.reserver_vehicule, name="reserver_vehicule"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / "static")
