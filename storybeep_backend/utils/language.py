from django.utils.translation import LANGUAGE_SESSION_KEY
from django.utils.translation.trans_real import get_supported_language_variant

def set_language_in_session(language, session):
    try:
        language = get_supported_language_variant(language)
        session[LANGUAGE_SESSION_KEY] = language
    except LookupError:
        pass
