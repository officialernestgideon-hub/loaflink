import random
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


def generate_otp():
    """Return a random numeric OTP as a string."""
    length = getattr(settings, 'OTP_LENGTH', 6)
    return ''.join(str(random.randint(0, 9)) for _ in range(length))


def send_otp_sms(phone, code):
    """
    SMS stub — prints the OTP to the Django console.
    Swap this out for Termii / Twilio / Africa's Talking later.
    """
    border = '=' * 50
    print(f'\n{border}')
    print(f'  📱  OTP for {phone}')
    print(f'  🔑  Code: {code}')
    print(f'  ⏱   Expires in {getattr(settings, "OTP_EXPIRY_MINUTES", 5)} minutes')
    print(f'{border}\n')
    return True


def otp_is_valid(user, submitted_code):
    """Check the submitted OTP against the user's stored OTP + expiry."""
    if not user.otp_code or not user.otp_created_at:
        return False, 'No OTP was requested. Please try again.'

    if user.otp_code != submitted_code.strip():
        return False, 'Incorrect code. Please check and try again.'

    expiry_minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 5)
    age = timezone.now() - user.otp_created_at
    if age > timedelta(minutes=expiry_minutes):
        return False, 'This code has expired. Please request a new one.'

    return True, ''