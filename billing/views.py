from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from tenants.decorators import tenant_required
from reservations.models import Reservation
from .models import Paiement
from .forms import PaiementForm
from .providers import initier_paiement, verifier_statut_paiement, cinetpay_configure


@tenant_required
def ajouter_paiement(request, reservation_pk):
    reservation = get_object_or_404(Reservation, pk=reservation_pk, tenant=request.tenant)
    if request.method == "POST":
        form = PaiementForm(request.POST)
        if form.is_valid():
            paiement = form.save(commit=False)
            paiement.tenant = request.tenant
            paiement.reservation = reservation
            paiement.save()
            messages.success(request, "Paiement enregistre (en attente).")
            return redirect("reservations:detail", pk=reservation.pk)
    else:
        form = PaiementForm()
    return render(request, "billing/formulaire.html", {
        "form": form, "reservation": reservation, "cinetpay_actif": cinetpay_configure(),
    })


@tenant_required
def payer_en_ligne(request, pk):
    """Genere un lien CinetPay (Orange Money / MTN MoMo) pour ce paiement et y redirige le client."""
    paiement = get_object_or_404(Paiement, pk=pk, tenant=request.tenant)
    succes, resultat = initier_paiement(paiement, request)
    if succes:
        return redirect(resultat)
    messages.warning(request, resultat)
    return redirect("reservations:detail", pk=paiement.reservation_id)


@csrf_exempt
@require_POST
def notification_cinetpay(request):
    """
    Webhook appele par CinetPay (serveur a serveur) quand un paiement change de statut.
    PAS de @tenant_required ici : CinetPay n'est pas un utilisateur connecte.
    On revalide TOUJOURS le statut aupres de CinetPay (jamais confiance aveugle
    dans les donnees POST, qui pourraient etre falsifiees) avant de marquer paye.
    """
    transaction_id = request.POST.get("cpm_trans_id") or request.POST.get("transaction_id")
    if not transaction_id:
        return HttpResponse(status=400)

    try:
        paiement = Paiement.objects.get(reference_transaction=transaction_id)
    except Paiement.DoesNotExist:
        return HttpResponse(status=404)

    statut_reel = verifier_statut_paiement(transaction_id)
    if statut_reel == "ACCEPTED":
        paiement.statut = "paye"
        paiement.save()

    return HttpResponse(status=200)


@tenant_required
def marquer_paye(request, pk):
    paiement = get_object_or_404(Paiement, pk=pk, tenant=request.tenant)
    if request.method == "POST":
        paiement.statut = "paye"
        paiement.save()
        messages.success(request, "Paiement marque comme paye.")
    return redirect("reservations:detail", pk=paiement.reservation_id)
