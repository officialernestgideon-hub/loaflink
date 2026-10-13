from django import forms
from orders.models import Product, Bakery
from datetime import time

class BakerySetupForm(forms.ModelForm):
    """
    First-time setup — collects business details for a new bakery.
    Fields: name, phone, address, cutoff_time.
    """
    class Meta:
        model = Bakery
        fields = ['name', 'phone', 'address', 'state', 'cutoff_time']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'bk-input',
                'placeholder': 'e.g. Sunrise Bakery',
                'autofocus': True,
            }),
            
            'phone': forms.TextInput(attrs={
                'class': 'bk-input',
                'placeholder': '+234 801 234 5678',
                'inputmode': 'tel',
            }),
            
            'state': forms.Select (attrs = {'class': 'bk-input'}),
            
            'address': forms.Textarea(attrs={
                'class': 'bk-input',
                'rows': 3,
                'placeholder': 'Street, city, landmark',
            }),
            'cutoff_time': forms.TimeInput(attrs={
                'class': 'bk-input',
                'type': 'time',
            }),
        }
        labels = {
            'name': 'Bakery name',
            'phone': 'Business phone',
            'state': 'State',
            'address': 'Bakery address',
            'cutoff_time': 'Daily order cutoff time',
        }
        help_texts = {
            'name': 'This is what retailers will see when they order from you.',
            'cutoff_time': 'Retailers must place tomorrow\'s order before this time. Default: 8:00 PM.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cutoff_time'].initial = time(20, 0)  # 8:00 PM
        self.fields['state'].empty_label = '— Choose your state —'


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'unit', 'image', 'is_available']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'bk-input',
                'placeholder': 'e.g. White Loaf',
                'autofocus': True,
            }),
            'description': forms.TextInput(attrs={
                'class': 'bk-input',
                'placeholder': 'Short description (optional)',
            }),
            'price': forms.NumberInput(attrs={
                'class': 'bk-input',
                'placeholder': '800',
                'step': '0.01',
                'min': '0',
            }),
            'unit': forms.Select(attrs={'class': 'bk-input'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'bk-checkbox'}),
            
            'image': forms.ClearableFileInput(attrs={
                'class': 'bk-input',
                'accept': 'image/*',
            }),
        }
        labels = {
            'image': 'Product photo',
            'is_available': 'Available for ordering',
        }
        help_texts = {
            'image': 'Optional. JPG, PNG, or WebP. Max 5MB. Shown to retailers.',
        }
        
    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image and image.size > 5 * 1024 * 1024:
            raise forms.ValidationError('Image must be smaller than 5MB.')
        return image


class BakerySettingsForm(forms.ModelForm):
    class Meta:
        model = Bakery
        fields = ['name', 'phone', 'address', 'state', 'cutoff_time', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'bk-input'}),
            'phone': forms.TextInput(attrs={'class': 'bk-input'}),
            'address': forms.Textarea(attrs={
                'class': 'bk-input',
                'rows': 3,
                'placeholder': 'Street, city',
            }),
            'state': forms.Select(attrs={'class': 'bk-input'}),
            'cutoff_time': forms.TimeInput(attrs={
                'class': 'bk-input',
                'type': 'time',
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'bk-checkbox'}),
        }
        labels = {
            'cutoff_time': 'Daily order cutoff time',
            'is_active': 'Accepting orders',
        }