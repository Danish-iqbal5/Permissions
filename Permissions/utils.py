


import random
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone

# Generate OTP, hash it, send email
def generate_and_send_otp(to_email):
    otp = str(random.randint(100000, 999999))
    otp_hash = make_password(otp)  # store hash, not raw code
    subject = 'Your OTP Code'
    message = f'Your OTP code is {otp}. It is valid for 10 minutes.'

    send_mail(
        subject,
        message,
        'Danish@Bussines.com',
        [to_email],
        fail_silently=False,
    )

    return otp_hash, timezone.now()  # store these in UserProfile


# Check OTP validity
def verify_otp(otp_input, otp_hash, otp_created_at, validity_minutes=10):
    """
    Compare input OTP with stored hash and check expiry.
    Returns True if valid, False otherwise.
    """
    if not otp_hash or not otp_created_at:
        return False

    # Expiry check
    if timezone.now() - otp_created_at > timezone.timedelta(minutes=validity_minutes):
        return False

    # Hash check
    if not check_password(otp_input, otp_hash):
        return False

    return True


# Send password setup email
def send_password_setup_email(to_email, set_password_url):
    subject = 'Set Up Your Password'
    message = f'Please set up your password by clicking the following link: {set_password_url}'

    send_mail(
        subject,
        message,
        'Danish@Bussines.com',
        [to_email],
        fail_silently=False,
    )
    return True
