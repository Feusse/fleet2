from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Tenant, User


class AjoutGestionnaireForm(UserCreationForm):
    """Le patron cree un compte 'gestionnaire' rattache a SA propre agence."""

    email = forms.EmailField(label="Email")
    telephone = forms.CharField(label="Telephone", required=False)

    class Meta:
        model = User
        fields = ["username", "email", "telephone", "password1", "password2"]

    def save(self, tenant, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.telephone = self.cleaned_data.get("telephone", "")
        user.role = "gestionnaire"
        user.tenant = tenant
        if commit:
            user.save()
        return user


class InscriptionAgenceForm(UserCreationForm):
    """Formulaire d'inscription : crée le Tenant (agence) + le User (patron) en une fois."""

    nom_agence = forms.CharField(label="Nom de l'agence", max_length=150)
    ville = forms.CharField(label="Ville", max_length=100, required=False)
    telephone_agence = forms.CharField(label="Téléphone de l'agence", max_length=30, required=False)
    email = forms.EmailField(label="Email du patron")

    class Meta:
        model = User
        fields = ["email", "username", "password1", "password2"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.role = "patron"
        if commit:
            tenant = Tenant.objects.create(
                nom_agence=self.cleaned_data["nom_agence"],
                ville=self.cleaned_data.get("ville", ""),
                telephone=self.cleaned_data.get("telephone_agence", ""),
            )
            user.tenant = tenant
            user.save()
        return user
