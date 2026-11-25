from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.core.mail import send_mail


def send_password_reset_email(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    reset_url = f'{settings.FRONTEND_BASE_URL}/password-reset/confirm?uid={uid}&token={token}'
    send_mail(
        'Reset your AIEMS Hub password',
        f'Use this secure link to reset your password: {reset_url}\n\nIf you did not request this, ignore this email.',
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
