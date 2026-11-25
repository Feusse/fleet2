"""
Vues publiques, accessibles SANS login : page de reservation par agence.
IMPORTANT : ici on ne peut pas utiliser request.tenant (personne n'est connecte).
Le tenant est trouve via le slug dans l'URL, et TOUT est filtre dessus.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django import forms
from .models import Tenant
from fleet.models import Vehicule
from reservations.models import Client, Reservation


class ReservationPubliqueForm(forms.Form):
    nom = forms.CharField(label="Votre nom")
    telephone_whatsapp = forms.CharField(label="Votre numero WhatsApp")
    cni = forms.CharField(label="Numero CNI (optionnel)", required=False)
    date_depart = forms.DateField(label="Date de depart", widget=forms.DateInput(attrs={"type": "date"}))
    date_retour = forms.DateField(label="Date de retour", widget=forms.DateInput(attrs={"type": "date"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs.setdefault(
                "class",
                "w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500",
            )


def page_agence(request, slug):
    """Page publique /r/<slug>/ : liste des vehicules disponibles de cette agence."""
    tenant = get_object_or_404(Tenant, slug_unique=slug)
    vehicules = Vehicule.objects.filter(tenant=tenant, statut="disponible")
    return render(request, "public/agence.html", {"tenant": tenant, "vehicules": vehicules})


def reserver_vehicule(request, slug, vehicule_id):
    """Formulaire public de demande de reservation (cree un devis, pas de login requis)."""
    tenant = get_object_or_404(Tenant, slug_unique=slug)
    vehicule = get_object_or_404(Vehicule, pk=vehicule_id, tenant=tenant)

    if request.method == "POST":
        form = ReservationPubliqueForm(request.POST)
        if form.is_valid():
            client = Client.objects.create(
                tenant=tenant,
                nom=form.cleaned_data["nom"],
                telephone_whatsapp=form.cleaned_data["telephone_whatsapp"],
                cni=form.cleaned_data["cni"],
            )
            reservation = Reservation(
                tenant=tenant,
                client=client,
                vehicule=vehicule,
                date_depart=form.cleaned_data["date_depart"],
                date_retour=form.cleaned_data["date_retour"],
                statut="devis",
            )
            try:
                reservation.save()
                return render(request, "public/confirmation.html", {"tenant": tenant, "reservation": reservation})
            except Exception as e:
                form.add_error(None, str(e))
    else:
        form = ReservationPubliqueForm()

    return render(request, "public/reserver.html", {"tenant": tenant, "vehicule": vehicule, "form": form})
