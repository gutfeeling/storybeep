from django.contrib.auth.signals import user_logged_in
from django.utils.translation import LANGUAGE_SESSION_KEY

@receiver(user_logged_in)
def set_language(sender, user, request, **kwargs):
    language = user.settings.language
    request.session[LANGUAGE_SESSION_KEY] = language
