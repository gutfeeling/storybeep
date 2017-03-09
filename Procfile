web: sh -c 'cd storybeep_backend && gunicorn storybeep_backend.wsgi.wsgi_heroku --log-file -'
worker: python storybeep_backend/manage.py rqworker default
