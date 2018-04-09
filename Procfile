web: newrelic-admin run-program gunicorn wsgi --log-file -
worker: newrelic-admin run-program celery worker --beat --app=taskapp --loglevel=info --scheduler=django
release: newrelic-admin run-program python manage.py migrate
