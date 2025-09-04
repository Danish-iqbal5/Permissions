from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class LoginRateThrottle(UserRateThrottle):
 scope = 'login'


class OTPVerifyRateThrottle(UserRateThrottle):
 scope = 'otp'


class ResendOTPThrottle(UserRateThrottle):
 scope = 'resend_otp'