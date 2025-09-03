from django.core.mail import send_mail
import random

def send_otp_email(to_email):
    otp = str(random.randint(100000, 999999))
    subject = 'Your OTP Code'
    message = f'Your OTP code is {otp}. It is valid for 10 minutes.'

    send_mail(
        subject,
        message,
        'Danish@Bussines.com', 
        [to_email],         
        fail_silently=False,
    )

    return otp

def send_password_setup_email(to_email , set_password_url):
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