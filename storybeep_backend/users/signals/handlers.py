from django.contrib.auth.signals import user_logged_in
from django.utils.translation import LANGUAGE_SESSION_KEY
from django.dispatch import receiver

from utils.language import set_language_in_session

@receiver(user_logged_in)
def set_language(sender, user, request, **kwargs):
    language = user.settings.language
    set_language_in_session(language, request.session)
