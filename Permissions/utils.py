from django.core.mail import send_mail
import random

def send_otp_email(to_email):
    otp = str(random.randint(100000, 999999))
    subject = 'Your OTP Code'
    message = f'Your OTP code is {otp}. It is valid for 10 minutes.'

    send_mail(
        subject,
        message,
        'Danish@Bussines.com',  # from email
        [to_email],          # recipient
        fail_silently=False,
    )

    return otp