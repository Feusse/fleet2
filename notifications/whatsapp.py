"""
Envoi de notifications WhatsApp via Twilio.

Fonctionne en mode "sandbox" gratuit de Twilio pour les tests : le numero
destinataire doit d'abord envoyer le code d'activation au numero Twilio
(une seule fois). En production, on passe sur un vrai numero WhatsApp
Business Twilio (payant, demande de verification Meta).

Si les cles TWILIO_* ne sont pas configurees (fichier .env vide), les
messages sont simplement journalises dans la console au lieu d'echouer :
utile pour developper/demontrer sans compte Twilio.
"""
import logging
from django.conf import settings

logger = logging.getLogger("fleetcm.whatsapp")


def _numero_whatsapp(numero_brut):
    """Met un numero au format whatsapp:+237XXXXXXXXX attendu par Twilio."""
    numero = numero_brut.strip().replace(" ", "")
    if not numero.startswith("+"):
        # Suppose un numero camerounais local si pas d'indicatif
        numero = "+237" + numero.lstrip("0")
    return f"whatsapp:{numero}"


def envoyer_whatsapp(numero_destinataire, message):
    """
    Envoie un message WhatsApp. Retourne True si envoye (ou simule), False si erreur.
    N'interrompt jamais le flux applicatif meme en cas d'echec (une notif
    manquee ne doit pas bloquer une reservation ou un paiement).
    """
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        logger.info("[MODE DEMO - pas de compte Twilio configure] WhatsApp a %s : %s",
                    numero_destinataire, message)
        return True

    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            from_=settings.TWILIO_WHATSAPP_FROM,
            to=_numero_whatsapp(numero_destinataire),
            body=message,
        )
        return True
    except Exception as e:
        logger.error("Echec envoi WhatsApp a %s : %s", numero_destinataire, e)
        return False


# --- Messages pre-formules pour les evenements cles de Fleet.cm ---

def notifier_reservation_confirmee(reservation):
    message = (
        f"Bonjour {reservation.client.nom}, votre reservation chez "
        f"{reservation.tenant.nom_agence} est confirmee : "
        f"{reservation.vehicule.marque} {reservation.vehicule.modele} "
        f"du {reservation.date_depart} au {reservation.date_retour}. "
        f"Montant total : {reservation.prix_total} FCFA."
    )
    return envoyer_whatsapp(reservation.client.telephone_whatsapp, message)


def notifier_rappel_retour(reservation):
    message = (
        f"Rappel : le vehicule {reservation.vehicule.marque} {reservation.vehicule.modele} "
        f"doit etre restitue le {reservation.date_retour} aupres de {reservation.tenant.nom_agence}."
    )
    return envoyer_whatsapp(reservation.client.telephone_whatsapp, message)


def notifier_patron_alerte(tenant, message):
    """Notifie le patron de l'agence (telephone enregistre sur le Tenant)."""
    if not tenant.telephone:
        logger.info("Pas de telephone enregistre pour %s, alerte non envoyee.", tenant.nom_agence)
        return False
    return envoyer_whatsapp(tenant.telephone, f"[Fleet.cm - {tenant.nom_agence}] {message}")
