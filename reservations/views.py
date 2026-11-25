from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from tenants.decorators import tenant_required
from fleet.models import Vehicule
from .models import Client, Reservation
from .forms import ClientForm, ReservationForm, RetourForm
from .pdf import generer_contrat_pdf
from notifications.whatsapp import notifier_reservation_confirmee


@tenant_required
def liste_clients(request):
    clients = Client.objects.filter(tenant=request.tenant)
    return render(request, "reservations/clients_liste.html", {"clients": clients})


@tenant_required
def creer_client(request):
    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.tenant = request.tenant
            client.save()
            messages.success(request, "Client ajoute.")
            return redirect("reservations:clients")
    else:
        form = ClientForm()
    return render(request, "reservations/client_formulaire.html", {"form": form})


@tenant_required
def liste_reservations(request):
    reservations = Reservation.objects.filter(tenant=request.tenant).select_related("client", "vehicule")
    statut = request.GET.get("statut")
    if statut:
        reservations = reservations.filter(statut=statut)
    return render(request, "reservations/liste.html", {"reservations": reservations, "statut_actif": statut})


@tenant_required
def creer_reservation(request):
    if request.method == "POST":
        form = ReservationForm(request.POST, tenant=request.tenant)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.tenant = request.tenant
            try:
                with transaction.atomic():
                    Vehicule.objects.select_for_update().get(pk=reservation.vehicule_id)
                    reservation.save()
                messages.success(request, "Reservation creee.")
                return redirect("reservations:detail", pk=reservation.pk)
            except ValidationError as e:
                form.add_error(None, e.message if hasattr(e, "message") else str(e))
    else:
        form = ReservationForm(tenant=request.tenant)
    return render(request, "reservations/formulaire.html", {"form": form, "mode": "creer"})


@tenant_required
def detail_reservation(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk, tenant=request.tenant)
    from billing.models import solde_restant
    from billing.providers import cinetpay_configure
    return render(request, "reservations/detail.html", {
        "reservation": reservation,
        "paiements": reservation.paiements.all(),
        "solde_restant": solde_restant(reservation),
        "cinetpay_actif": cinetpay_configure(),
    })


@tenant_required
def confirmer_reservation(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk, tenant=request.tenant)
    if request.method == "POST":
        try:
            with transaction.atomic():
                Vehicule.objects.select_for_update().get(pk=reservation.vehicule_id)
                reservation.statut = "confirmee"
                reservation.save()
                reservation.vehicule.statut = "loue"
                reservation.vehicule.save()
            notifier_reservation_confirmee(reservation)
            messages.success(request, "Reservation confirmee, vehicule marque loue.")
        except ValidationError as e:
            messages.error(request, str(e))
    return redirect("reservations:detail", pk=pk)


@tenant_required
def demarrer_location(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk, tenant=request.tenant)
    if request.method == "POST" and reservation.statut == "confirmee":
        reservation.statut = "en_cours"
        reservation.save()
        messages.success(request, "Location demarree.")
    return redirect("reservations:detail", pk=pk)


@tenant_required
def retour_vehicule(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk, tenant=request.tenant)
    if request.method == "POST":
        form = RetourForm(request.POST)
        if form.is_valid():
            reservation.kilometrage_retour = form.cleaned_data["kilometrage_retour"]
            reservation.etat_retour = form.cleaned_data["etat_retour"]
            reservation.frais_supplementaires = form.cleaned_data["frais_supplementaires"] or 0
            reservation.statut = "terminee"
            reservation.save()

            vehicule = reservation.vehicule
            vehicule.kilometrage_actuel = form.cleaned_data["kilometrage_retour"]
            vehicule.statut = "maintenance" if form.cleaned_data["envoyer_en_maintenance"] else "disponible"
            vehicule.save()

            messages.success(request, "Retour enregistre. Vehicule mis a jour.")
            return redirect("reservations:detail", pk=pk)
    else:
        form = RetourForm(initial={"kilometrage_retour": reservation.vehicule.kilometrage_actuel})
    return render(request, "reservations/retour.html", {"form": form, "reservation": reservation})


@tenant_required
def generer_contrat(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk, tenant=request.tenant)
    buffer = generer_contrat_pdf(reservation)
    nom_fichier = f"contrat_{reservation.client.nom}_{reservation.vehicule.immatriculation}.pdf".replace(" ", "_")
    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{nom_fichier}"'
    return response
