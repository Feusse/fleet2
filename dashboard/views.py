import json
from datetime import date, timedelta
from django.shortcuts import render
from django.db.models import Sum, Q
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from tenants.decorators import tenant_required, patron_required
from fleet.models import Vehicule
from reservations.models import Reservation
from billing.models import Paiement
from .reports import generer_rapport_pdf, generer_rapport_excel


@tenant_required
def accueil(request):
    tenant = request.tenant
    aujourdhui = date.today()
    debut_mois = aujourdhui.replace(day=1)
    est_patron = request.user.role == "patron"

    locations_en_cours = Reservation.objects.filter(tenant=tenant, statut="en_cours").count()
    vehicules_dispo = Vehicule.objects.filter(tenant=tenant, statut="disponible").count()
    vehicules_maintenance = Vehicule.objects.filter(tenant=tenant, statut="maintenance")

    context = {
        "est_patron": est_patron,
        "locations_en_cours": locations_en_cours,
        "vehicules_dispo": vehicules_dispo,
        "vehicules_maintenance": vehicules_maintenance,
    }

    # Les chiffres financiers et de rentabilite sont reserves au patron :
    # un gestionnaire voit l'operationnel (vehicules, locations en cours,
    # maintenance) mais pas le chiffre d'affaires ni les impayes.
    if est_patron:
        ca_du_mois = Paiement.objects.filter(
            tenant=tenant, statut="paye", date_paiement__date__gte=debut_mois
        ).aggregate(total=Sum("montant"))["total"] or 0

        impayes = Paiement.objects.filter(tenant=tenant, statut="en_attente").aggregate(
            total=Sum("montant")
        )["total"] or 0

        il_y_a_6_mois = debut_mois - timedelta(days=180)
        ca_par_mois = (
            Paiement.objects.filter(tenant=tenant, statut="paye", date_paiement__date__gte=il_y_a_6_mois)
            .annotate(mois=TruncMonth("date_paiement"))
            .values("mois")
            .annotate(total=Sum("montant"))
            .order_by("mois")
        )
        labels_mois = [p["mois"].strftime("%b %Y") for p in ca_par_mois]
        valeurs_mois = [float(p["total"]) for p in ca_par_mois]

        top_rentables = (
            Vehicule.objects.filter(tenant=tenant)
            .annotate(revenu=Sum("reservations__prix_total", filter=Q(reservations__statut="terminee")))
            .order_by("-revenu")[:3]
        )
        top_couteux = (
            Vehicule.objects.filter(tenant=tenant)
            .annotate(frais=Sum("reservations__frais_supplementaires"))
            .order_by("-frais")[:3]
        )

        reservations_actives = (
            Reservation.objects.filter(tenant=tenant, statut__in=["confirmee", "en_cours", "terminee"])
            .select_related("client", "vehicule")
        )
        clients_endettes = []
        for r in reservations_actives:
            paye = Paiement.objects.filter(
                reservation=r, statut="paye", type_paiement__in=["acompte", "solde"]
            ).aggregate(total=Sum("montant"))["total"] or 0
            solde = (r.prix_total or 0) - paye
            if solde > 0:
                clients_endettes.append({"reservation": r, "solde": solde})

        context.update({
            "ca_du_mois": ca_du_mois,
            "impayes": impayes,
            "labels_mois": json.dumps(labels_mois),
            "valeurs_mois": json.dumps(valeurs_mois),
            "top_rentables": top_rentables,
            "top_couteux": top_couteux,
            "clients_endettes": clients_endettes,
        })

    return render(request, "dashboard/accueil.html", context)


@tenant_required
def alertes(request):
    tenant = request.tenant
    aujourdhui = date.today()
    dans_15_jours = aujourdhui + timedelta(days=15)

    assurances_expirant = Vehicule.objects.filter(
        tenant=tenant,
        date_expiration_assurance__isnull=False,
        date_expiration_assurance__lte=dans_15_jours,
        date_expiration_assurance__gte=aujourdhui,
    )

    vehicules_tous = Vehicule.objects.filter(tenant=tenant)
    vidanges_necessaires = [v for v in vehicules_tous if v.vidange_necessaire]

    retards = Reservation.objects.filter(
        tenant=tenant, statut="en_cours", date_retour__lt=aujourdhui
    ).select_related("client", "vehicule")

    context = {
        "assurances_expirant": assurances_expirant,
        "vidanges_necessaires": vidanges_necessaires,
        "retards": retards,
    }
    return render(request, "dashboard/alertes.html", context)


@patron_required
def export_rapport(request):
    """Export du rapport mensuel en PDF ou Excel. Reserve au patron (donnees financieres)."""
    aujourdhui = date.today()
    annee = int(request.GET.get("annee", aujourdhui.year))
    mois = int(request.GET.get("mois", aujourdhui.month))
    fmt = request.GET.get("format", "pdf")

    nom_fichier = f"rapport_{request.tenant.slug_unique}_{annee}_{mois:02d}"

    if fmt == "xlsx":
        buffer = generer_rapport_excel(request.tenant, annee, mois)
        response = HttpResponse(
            buffer,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{nom_fichier}.xlsx"'
    else:
        buffer = generer_rapport_pdf(request.tenant, annee, mois)
        response = HttpResponse(buffer, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{nom_fichier}.pdf"'

    return response
