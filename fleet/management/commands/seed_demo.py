"""
Commande : python manage.py seed_demo
Cree un Tenant de demo "Prestige Auto Douala" avec 5 vehicules, 3 clients,
et 2 reservations (dont 1 qui chevauche volontairement, pour tester le blocage).
"""
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from tenants.models import Tenant, User
from fleet.models import Vehicule
from reservations.models import Client, Reservation


class Command(BaseCommand):
    help = "Cree des donnees de demonstration pour Fleet.cm"

    @transaction.atomic
    def handle(self, *args, **options):
        if Tenant.objects.filter(slug_unique="prestige-auto-douala").exists():
            self.stdout.write(self.style.WARNING("Le tenant de demo existe deja. Suppression et recreation..."))
            Tenant.objects.filter(slug_unique="prestige-auto-douala").delete()

        tenant = Tenant.objects.create(
            nom_agence="Prestige Auto Douala",
            slug_unique="prestige-auto-douala",
            telephone="+237690000000",
            ville="Douala",
            plan_abonnement="essai",
        )

        patron = User.objects.create_user(
            username="patron",
            email="patron@prestigeauto.cm",
            password="demo1234",
            tenant=tenant,
            role="patron",
            is_staff=True,
        )

        vehicules_data = [
            ("Toyota", "Yaris", "berline", "CE-123-AB", 25000, 5000, 120000),
            ("Toyota", "RAV4", "suv", "CE-456-CD", 40000, 12000, 180000),
            ("Toyota", "Hilux", "pickup", "CE-789-EF", 60000, 9000, 220000),
            ("Hyundai", "Elantra", "berline", "CE-321-GH", 30000, 2000, 110000),
            ("Kia", "Sportage", "suv", "CE-654-IJ", 50000, 8000, 170000),
        ]
        vehicules = []
        for marque, modele, cat, immat, km, km_entretien, prix in vehicules_data:
            v = Vehicule.objects.create(
                tenant=tenant,
                marque=marque,
                modele=modele,
                categorie=cat,
                immatriculation=immat,
                kilometrage_actuel=km,
                kilometrage_dernier_entretien=km_entretien,
                statut="disponible",
                prix_journalier=prix,
                caution=prix * 3,
                date_expiration_assurance=date.today() + timedelta(days=10),
            )
            vehicules.append(v)

        clients_data = [
            ("Jean Mbarga", "+237677000001", "CNI001"),
            ("Aicha Fouda", "+237677000002", "CNI002"),
            ("Paul Ngoe", "+237677000003", "CNI003"),
        ]
        clients = [Client.objects.create(tenant=tenant, nom=n, telephone_whatsapp=t, cni=c) for n, t, c in clients_data]

        aujourdhui = date.today()

        # Reservation 1 : confirmee, vehicule 0 (Yaris)
        r1 = Reservation(
            tenant=tenant, client=clients[0], vehicule=vehicules[0],
            date_depart=aujourdhui + timedelta(days=1),
            date_retour=aujourdhui + timedelta(days=4),
            statut="confirmee",
        )
        r1.save()
        vehicules[0].statut = "loue"
        vehicules[0].save()

        # Reservation 2 : devis, sur le MEME vehicule, dates qui chevauchent r1
        # -> reste en "devis" expres pour ne pas declencher le blocage (le blocage
        #    ne s'applique qu'aux statuts confirmee/en_cours), afin de pouvoir tester
        #    manuellement l'erreur en essayant de la confirmer depuis l'interface.
        r2 = Reservation(
            tenant=tenant, client=clients[1], vehicule=vehicules[0],
            date_depart=aujourdhui + timedelta(days=2),
            date_retour=aujourdhui + timedelta(days=6),
            statut="devis",
        )
        r2.save()

        self.stdout.write(self.style.SUCCESS("Donnees de demo creees avec succes."))
        self.stdout.write(f"Agence : {tenant.nom_agence} (slug: {tenant.slug_unique})")
        self.stdout.write("Connexion -> username: patron / mot de passe: demo1234")
        self.stdout.write(
            f"Page publique : /r/{tenant.slug_unique}/"
        )
        self.stdout.write(
            self.style.WARNING(
                f"Pour tester le blocage anti-double-reservation : essayez de confirmer "
                f"la reservation de {clients[1].nom} sur le Yaris (devis) -> doit etre refusee "
                f"car {clients[0].nom} a deja confirme sur une periode qui chevauche."
            )
        )
