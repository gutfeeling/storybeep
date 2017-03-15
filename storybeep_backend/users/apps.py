from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = "users"

    def ready(self):

        # import signal handlers
        import users.signals.handlers
