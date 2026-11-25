from django import forms
from .models import Vehicule


class VehiculeForm(forms.ModelForm):
    class Meta:
        model = Vehicule
        exclude = ["tenant", "date_ajout"]
        widgets = {
            "date_expiration_assurance": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        self.tenant = tenant
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = "w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            field.widget.attrs.setdefault("class", css)

    def clean_immatriculation(self):
        immat = self.cleaned_data["immatriculation"]
        qs = Vehicule.objects.filter(tenant=self.tenant, immatriculation=immat)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Un véhicule avec cette immatriculation existe déjà.")
        return immat
