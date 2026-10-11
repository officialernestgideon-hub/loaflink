from django import forms
from django.core.exceptions import ValidationError
from .models import User


PHONE_WIDGET = forms.TextInput(attrs={
    'class': 'form-input',
    'placeholder': '+234 801 234 5678',
    'autocomplete': 'tel',
    'inputmode': 'tel',
})

CODE_WIDGET = forms.TextInput(attrs={
    'class': 'form-input form-input-otp',
    'placeholder': '••••••',
    'autocomplete': 'one-time-code',
    'inputmode': 'numeric',
    'maxlength': 6,
})


class LoginForm(forms.Form):
    """Step 1 — enter phone."""
    phone = forms.CharField(
        max_length=20,
        widget=PHONE_WIDGET,
        label='Phone number',
    )

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip().replace(' ', '')
        if not User.objects.filter(phone=phone, is_active=True).exists():
            raise ValidationError(
                "We don't recognise this phone number. "
                "Please check it, or create a new account."
            )
        return phone


class OTPForm(forms.Form):
    """Step 2 — enter the 6-digit code."""
    code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=CODE_WIDGET,
        label='Verification code',
    )


class RegisterForm(forms.ModelForm):
    """New user signup."""
    role = forms.ChoiceField(
        choices=[
            ('bakery', 'I run a bakery'),
            ('retailer', 'I run a retail shop'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'role-radio'}),
        initial='retailer',
    )

    class Meta:
        model = User
        fields = ['full_name', 'phone', 'role']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g. Mama Ngozi',
                'autocomplete': 'name',
            }),
            'phone': PHONE_WIDGET,
        }

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip().replace(' ', '')
        if User.objects.filter(phone=phone).exists():
            raise ValidationError(
                "This phone number is already registered. Try logging in instead."
            )
        return phone

    def clean_full_name(self):
        name = self.cleaned_data['full_name'].strip()
        if len(name) < 2:
            raise ValidationError("Please enter your full name.")
        return name
