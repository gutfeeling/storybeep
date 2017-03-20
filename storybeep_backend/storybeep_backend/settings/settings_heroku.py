from .settings_base import *

import dj_database_url

db_from_env = dj_database_url.config(conn_max_age=500)
DATABASES['default'].update(db_from_env)

DEBUG = False
try:
    heroku_debug = get_environment_variable("DEBUG")
    if heroku_debug == "True":
        DEBUG = True
except ImproperlyConfigured:
    pass


SECRET_KEY = get_environment_variable('DJANGO_SECRET_KEY')
ALLOWED_HOSTS = ["storybeep.herokuapp.com", ".storybeep.com"]

SITE_ID = 5
