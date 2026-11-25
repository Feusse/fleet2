"""
Commande a lancer une fois par jour (via cron ou tache planifiee de
l'hebergeur) : previent chaque patron par WhatsApp si un de ses vehicules
a une assurance qui expire bientot, une vidange a faire, ou un retard
de retour en cours.

Exemple de cron (tous les jours a 7h) :
    0 7 * * * cd /chemin/vers/fleetcm && venv/bin/python manage.py envoyer_alertes_whatsapp
"""
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from tenants.models import Tenant
from fleet.models import Vehicule
from reservations.models import Reservation
from notifications.whatsapp import notifier_patron_alerte


class Command(BaseCommand):
    help = "Envoie les alertes du jour (assurance, vidange, retards) par WhatsApp a chaque patron."

    def handle(self, *args, **options):
        aujourdhui = date.today()
        dans_15_jours = aujourdhui + timedelta(days=15)
        total_envoyes = 0

        for tenant in Tenant.objects.all():
            messages = []

            assurances = Vehicule.objects.filter(
                tenant=tenant,
                date_expiration_assurance__isnull=False,
                date_expiration_assurance__lte=dans_15_jours,
                date_expiration_assurance__gte=aujourdhui,
            )
            for v in assurances:
                messages.append(
                    f"Assurance de {v.marque} {v.modele} ({v.immatriculation}) "
                    f"expire le {v.date_expiration_assurance}."
                )

            for v in Vehicule.objects.filter(tenant=tenant):
                if v.vidange_necessaire:
                    messages.append(
                        f"Vidange necessaire pour {v.marque} {v.modele} "
                        f"({v.kilometrage_actuel} km)."
                    )

            retards = Reservation.objects.filter(
                tenant=tenant, statut="en_cours", date_retour__lt=aujourdhui
            ).select_related("client", "vehicule")
            for r in retards:
                messages.append(
                    f"Retard de retour : {r.vehicule.marque} {r.vehicule.modele} "
                    f"loue par {r.client.nom}, retour prevu le {r.date_retour}."
                )

            if messages:
                texte = "Alertes du jour :\n- " + "\n- ".join(messages)
                ok = notifier_patron_alerte(tenant, texte)
                if ok:
                    total_envoyes += 1
                    self.stdout.write(self.style.SUCCESS(f"Alerte envoyee a {tenant.nom_agence}"))
            else:
                self.stdout.write(f"{tenant.nom_agence} : rien a signaler aujourd'hui.")

        self.stdout.write(self.style.SUCCESS(f"Termine. {total_envoyes} agence(s) notifiee(s)."))
