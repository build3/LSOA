web: gunicorn wsgi --log-file -
worker: celery worker --beat --app=taskapp --loglevel=info
release: python manage.py migrate
