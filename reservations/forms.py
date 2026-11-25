from django import forms
from .models import Client, Reservation


def _css(field):
    field.widget.attrs.setdefault(
        "class",
        "w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500",
    )


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        exclude = ["tenant", "date_ajout"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            _css(f)


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ["client", "vehicule", "date_depart", "date_retour", "statut"]
        widgets = {
            "date_depart": forms.DateInput(attrs={"type": "date"}),
            "date_retour": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["client"].queryset = Client.objects.filter(tenant=tenant)
            self.fields["vehicule"].queryset = self.fields["vehicule"].queryset.model.objects.filter(tenant=tenant)
        for f in self.fields.values():
            _css(f)


class RetourForm(forms.Form):
    kilometrage_retour = forms.IntegerField(label="Nouveau kilométrage", min_value=0)
    etat_retour = forms.CharField(label="État du véhicule au retour", widget=forms.Textarea(attrs={"rows": 3}), required=False)
    frais_supplementaires = forms.DecimalField(label="Frais supplémentaires (retard, carburant...)", max_digits=10, decimal_places=0, required=False, initial=0)
    envoyer_en_maintenance = forms.BooleanField(label="Envoyer le véhicule en maintenance", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            if not isinstance(f.widget, forms.CheckboxInput):
                _css(f)
