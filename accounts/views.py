from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .models import User
from .forms import LoginForm, OTPForm, RegisterForm
from .utils import generate_otp, send_otp_sms, otp_is_valid
from .decorators import role_required


SESSION_PHONE_KEY = 'pending_login_phone'


# ============================================================
# REGISTRATION
# ============================================================
@require_http_methods(['GET', 'POST'])
def register_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:redirect_by_role')

    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.is_active = True
        user.set_unusable_password()   # phone-based login — no password
        user.save()

        # Auto-create the Bakery or Retailer profile shell
        if user.role == 'bakery':
            # Do NOT auto-create the Bakery — the owner will fill in business
            # details on the setup page right after verification.
            # Retailers get their setup page in the shop app.
            pass
        elif user.role == 'retailer':
            # Retailer has no bakery yet — we'll prompt for that later
            # For MVP, they'll be assigned to a bakery by the admin after signup.
            # The retailer dashboard will block them until is_active=True.
            pass

        messages.success(
            request,
            "Account created. We've sent a code to your phone — enter it to log in."
        )
        # Immediately send OTP and go to verify
        code = generate_otp()
        user.otp_code = code
        user.otp_created_at = timezone.now()
        user.save(update_fields=['otp_code', 'otp_created_at'])
        send_otp_sms(user.phone, code)

        request.session[SESSION_PHONE_KEY] = user.phone
        return redirect('accounts:verify')

    return render(request, 'accounts/register.html', {'form': form})


# ============================================================
# LOGIN — STEP 1: enter phone
# ============================================================
@require_http_methods(['GET', 'POST'])
def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:redirect_by_role')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        phone = form.cleaned_data['phone']
        user = User.objects.get(phone=phone)

        code = generate_otp()
        user.otp_code = code
        user.otp_created_at = timezone.now()
        user.save(update_fields=['otp_code', 'otp_created_at'])
        send_otp_sms(user.phone, code)

        request.session[SESSION_PHONE_KEY] = phone
        messages.success(request, f"Code sent to {phone}.")
        return redirect('accounts:verify')

    return render(request, 'accounts/login.html', {'form': form})


# ============================================================
# LOGIN — STEP 2: enter OTP
# ============================================================
@require_http_methods(['GET', 'POST'])
def verify_view(request):
    phone = request.session.get(SESSION_PHONE_KEY)
    if not phone:
        messages.error(request, 'Please start by entering your phone number.')
        return redirect('accounts:login')

    try:
        user = User.objects.get(phone=phone, is_active=True)
    except User.DoesNotExist:
        messages.error(request, 'Account not found.')
        return redirect('accounts:login')

    form = OTPForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        ok, error = otp_is_valid(user, form.cleaned_data['code'])
        if ok:
            # Clear OTP and log the user in
            user.otp_code = ''
            user.otp_created_at = None
            user.save(update_fields=['otp_code', 'otp_created_at'])

            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            request.session.pop(SESSION_PHONE_KEY, None)

            messages.success(request, f"Welcome back, {user.full_name or user.phone}.")
            return redirect('accounts:redirect_by_role')
        else:
            form.add_error('code', error)

    return render(request, 'accounts/verify.html', {
        'form': form,
        'phone': phone,
    })


# ============================================================
# RESEND OTP
# ============================================================
@require_http_methods(['POST'])
def resend_otp_view(request):
    phone = request.session.get(SESSION_PHONE_KEY)
    if not phone:
        return redirect('accounts:login')

    user = User.objects.filter(phone=phone, is_active=True).first()
    if not user:
        messages.error(request, 'Account not found.')
        return redirect('accounts:login')

    code = generate_otp()
    user.otp_code = code
    user.otp_created_at = timezone.now()
    user.save(update_fields=['otp_code', 'otp_created_at'])
    send_otp_sms(user.phone, code)

    messages.success(request, f'New code sent to {phone}.')
    return redirect('accounts:verify')


# ============================================================
# LOGOUT
# ============================================================
def logout_view(request):
    auth_logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('accounts:login')


def redirect_by_role(request):
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    user = request.user

    if user.is_superuser or request.user.role == 'admin':
        return redirect('console:dashboard')
    
    if user.role == 'bakery':
        # If they have no Bakery profile yet, send them to setup
        if not hasattr(user, 'bakery'):
            return redirect('bakery:setup')
        return redirect('bakery:dashboard')
    if user.role == 'retailer':
        # If they have no Retailer profile yet, send them to setup
        if not hasattr(user, 'retailer'):
            return redirect('shop:setup')
        return redirect('shop:home')
    return redirect('account:login')

    