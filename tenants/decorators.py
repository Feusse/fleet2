"""Décorateur à utiliser sur TOUTES les vues internes (jamais sur la page publique /r/<slug>)."""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages


def tenant_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.tenant is None:
            messages.error(request, "Votre compte n'est rattaché à aucune agence.")
            return redirect("tenants:connexion")
        return view_func(request, *args, **kwargs)
    return wrapper


def patron_required(view_func):
    """
    A utiliser EN PLUS de @tenant_required (toujours apres lui dans l'ordre des
    decorateurs) pour les actions reservees au patron : finances, suppression
    de vehicule, export de rapports. Un gestionnaire qui tente d'y acceder est
    redirige avec un message clair, pas une erreur technique.
    """
    @wraps(view_func)
    @tenant_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != "patron":
            messages.error(request, "Cette action est reservee au patron de l'agence.")
            return redirect("dashboard:accueil")
        return view_func(request, *args, **kwargs)
    return wrapper
