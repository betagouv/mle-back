from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes


def build_password_reset_link(user, frontend_base_url: str) -> str:
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = PasswordResetTokenGenerator().make_token(user)

    return f"{frontend_base_url}/reinitialiser-son-mot-de-passe?uid={uid}&token={token}"
