web: gunicorn wsgi --log-file -
worker: celery worker --beat --app=taskapp --loglevel=info --scheduler=django
release: python manage.py migrate
