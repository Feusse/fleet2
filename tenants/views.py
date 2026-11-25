from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import InscriptionAgenceForm, AjoutGestionnaireForm
from .models import User
from .decorators import patron_required


class ConnexionView(LoginView):
    template_name = "tenants/connexion.html"
    redirect_authenticated_user = True


def inscription(request):
    if request.method == "POST":
        form = InscriptionAgenceForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Bienvenue sur Fleet.cm, {user.tenant.nom_agence} !")
            return redirect("dashboard:accueil")
    else:
        form = InscriptionAgenceForm()
    return render(request, "tenants/inscription.html", {"form": form})


def deconnexion(request):
    logout(request)
    return redirect("tenants:connexion")


@patron_required
def equipe(request):
    membres = User.objects.filter(tenant=request.tenant).order_by("role", "username")
    return render(request, "tenants/equipe.html", {"membres": membres})


@patron_required
def ajouter_gestionnaire(request):
    if request.method == "POST":
        form = AjoutGestionnaireForm(request.POST)
        if form.is_valid():
            form.save(tenant=request.tenant)
            messages.success(request, "Compte gestionnaire cree.")
            return redirect("tenants:equipe")
    else:
        form = AjoutGestionnaireForm()
    return render(request, "tenants/ajouter_gestionnaire.html", {"form": form})


@patron_required
def desactiver_membre(request, pk):
    membre = get_object_or_404(User, pk=pk, tenant=request.tenant, role="gestionnaire")
    if request.method == "POST":
        membre.is_active = not membre.is_active
        membre.save()
        etat = "reactive" if membre.is_active else "desactive"
        messages.success(request, f"Compte {membre.username} {etat}.")
    return redirect("tenants:equipe")


def accueil_redirect(request):
    from django.shortcuts import redirect
    if request.user.is_authenticated and getattr(request.user, "tenant_id", None):
        return redirect("dashboard:accueil")
    return redirect("tenants:connexion")
