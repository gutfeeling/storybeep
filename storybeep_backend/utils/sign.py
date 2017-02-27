from django.core import signing
from django.conf import settings

salt = getattr(settings, "SALT", "salt")
max_age_in_days = getattr(settings, "MAX_AGE_IN_DAYS", 30)

def get_hmac_code(email):

    """https://django-registration.readthedocs.io/en/2.2/hmac.html
    Also see the GitHub repo.
    """

    hmac_code = signing.dumps(obj = email, salt = salt)

    return hmac_code


def validate_code(code):

    try:
        data = signing.loads(code, salt = salt, max_age = max_age_in_days*86400)
        return data
    except signing.BadSignature:
        return None
