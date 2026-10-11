from django import forms
from orders.models import Bakery, NIGERIAN_STATES


class BakerySelectForm(forms.Form):
    """
    Used after registration to attach a retailer to a bakery.
    Shows only active bakeries.
    """

    bakery = forms.ModelChoiceField(
        queryset=Bakery.objects.filter(is_active=True).order_by('name'),
        empty_label="— Choose your bakery —",
        widget=forms.Select(attrs={
            'class': 'shop-input',
        }),
        help_text="The bakery you'll be buying bread from.",
    )
    
    state = forms.ChoiceField(              # ← NEW
        choices=[('', '— Choose your state —')] + [
            (v, l) for v, l in Bakery._meta.get_field('state').choices
        ],
        widget=forms.Select(attrs={'class': 'shop-input'}),
        help_text="Which state is your shop in?",
    )
    
    address = forms.CharField(
        max_length=300,
        widget=forms.Textarea(attrs={
            'class': 'shop-input',
            'rows': 3,
            'placeholder': 'e.g. 5 Broad Street, Lagos',
        }),
        help_text="Where your bread should be delivered.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If no active bakeries exist, disable the form gracefully
        if not self.fields['bakery'].queryset.exists():
            self.fields['bakery'].widget.attrs['disabled'] = True
            self.fields['bakery'].help_text = (
                "No bakeries are available on LoafLink yet. "
                "Please check back soon."
            )