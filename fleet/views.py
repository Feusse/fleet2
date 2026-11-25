from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from tenants.decorators import tenant_required, patron_required
from .models import Vehicule
from .forms import VehiculeForm


@tenant_required
def liste_vehicules(request):
    vehicules = Vehicule.objects.filter(tenant=request.tenant)
    statut = request.GET.get("statut")
    if statut:
        vehicules = vehicules.filter(statut=statut)
    return render(request, "fleet/liste.html", {"vehicules": vehicules, "statut_actif": statut})


@tenant_required
def creer_vehicule(request):
    if request.method == "POST":
        form = VehiculeForm(request.POST, request.FILES, tenant=request.tenant)
        if form.is_valid():
            vehicule = form.save(commit=False)
            vehicule.tenant = request.tenant
            vehicule.save()
            messages.success(request, "Véhicule ajouté avec succès.")
            return redirect("fleet:liste")
    else:
        form = VehiculeForm(tenant=request.tenant)
    return render(request, "fleet/formulaire.html", {"form": form, "mode": "creer"})


@tenant_required
def modifier_vehicule(request, pk):
    vehicule = get_object_or_404(Vehicule, pk=pk, tenant=request.tenant)
    if request.method == "POST":
        form = VehiculeForm(request.POST, request.FILES, instance=vehicule, tenant=request.tenant)
        if form.is_valid():
            form.save()
            messages.success(request, "Véhicule mis à jour.")
            return redirect("fleet:liste")
    else:
        form = VehiculeForm(instance=vehicule, tenant=request.tenant)
    return render(request, "fleet/formulaire.html", {"form": form, "mode": "modifier", "vehicule": vehicule})


@patron_required
def supprimer_vehicule(request, pk):
    vehicule = get_object_or_404(Vehicule, pk=pk, tenant=request.tenant)
    if request.method == "POST":
        vehicule.delete()
        messages.success(request, "Véhicule supprimé.")
        return redirect("fleet:liste")
    return render(request, "fleet/confirmer_suppression.html", {"vehicule": vehicule})


@tenant_required
def detail_vehicule(request, pk):
    vehicule = get_object_or_404(Vehicule, pk=pk, tenant=request.tenant)
    return render(request, "fleet/detail.html", {"vehicule": vehicule})
