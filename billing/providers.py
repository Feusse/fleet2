"""
Integration CinetPay : agregateur qui gere Orange Money ET MTN MoMo derriere
une seule API, bien plus simple que d'integrer chaque operateur separement.

Documentation : https://docs.cinetpay.com

Si CINETPAY_API_KEY n'est pas configuree (.env vide), initier_paiement()
retourne un lien de simulation et marque_paye peut etre utilise manuellement
depuis l'interface (comportement V1 conserve) : rien ne casse en mode demo.
"""
import logging
import requests
from django.conf import settings
from django.urls import reverse

logger = logging.getLogger("fleetcm.cinetpay")

CINETPAY_INIT_URL = "https://api-checkout.cinetpay.com/v2/payment"


def cinetpay_configure():
    return bool(settings.CINETPAY_API_KEY and settings.CINETPAY_SITE_ID)


def initier_paiement(paiement, request):
    """
    Demande a CinetPay un lien de paiement pour ce Paiement.
    Retourne (succes: bool, url_paiement_ou_erreur: str).
    """
    if not cinetpay_configure():
        logger.info("[MODE DEMO - CinetPay non configure] Paiement simule pour %s", paiement)
        return False, (
            "CinetPay n'est pas encore configure. Renseignez CINETPAY_API_KEY et "
            "CINETPAY_SITE_ID dans le fichier .env (voir .env.example), ou marquez "
            "ce paiement comme paye manuellement une fois l'argent recu."
        )

    transaction_id = f"FLEETCM-{paiement.pk}-{paiement.tenant_id}"
    payload = {
        "apikey": settings.CINETPAY_API_KEY,
        "site_id": settings.CINETPAY_SITE_ID,
        "transaction_id": transaction_id,
        "amount": int(paiement.montant),
        "currency": "XAF",
        "description": f"{paiement.get_type_paiement_display()} - {paiement.reservation}",
        "notify_url": settings.SITE_URL + reverse("billing:notification_cinetpay"),
        "return_url": settings.SITE_URL + reverse(
            "reservations:detail", args=[paiement.reservation_id]
        ),
        "channels": "ALL",  # laisse le client choisir Orange Money ou MTN MoMo
        "customer_name": paiement.reservation.client.nom,
        "customer_phone_number": paiement.reservation.client.telephone_whatsapp,
    }

    try:
        response = requests.post(CINETPAY_INIT_URL, json=payload, timeout=15)
        data = response.json()
        if data.get("code") == "201":
            paiement.reference_transaction = transaction_id
            paiement.save(update_fields=["reference_transaction"])
            return True, data["data"]["payment_url"]
        logger.error("Erreur CinetPay : %s", data)
        return False, data.get("message", "Erreur inconnue de CinetPay.")
    except requests.RequestException as e:
        logger.error("Erreur reseau CinetPay : %s", e)
        return False, "Impossible de contacter CinetPay pour le moment. Reessayez plus tard."


def verifier_statut_paiement(transaction_id):
    """Interroge CinetPay pour confirmer le statut reel d'une transaction (securite anti-fraude)."""
    if not cinetpay_configure():
        return None
    try:
        response = requests.post(
            "https://api-checkout.cinetpay.com/v2/payment/check",
            json={
                "apikey": settings.CINETPAY_API_KEY,
                "site_id": settings.CINETPAY_SITE_ID,
                "transaction_id": transaction_id,
            },
            timeout=15,
        )
        data = response.json()
        return data.get("data", {}).get("status")  # "ACCEPTED" / "REFUSED" / ...
    except requests.RequestException as e:
        logger.error("Erreur verification CinetPay : %s", e)
        return None
