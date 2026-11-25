from django import forms
from .models import Paiement


class PaiementForm(forms.ModelForm):
    class Meta:
        model = Paiement
        fields = ["montant", "type_paiement", "methode", "reference_transaction"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs.setdefault(
                "class",
                "w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500",
            )
