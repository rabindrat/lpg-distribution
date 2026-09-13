web: gunicorn lpg_app.wsgi --bind 0.0.0.0:$PORT --access-logfile -
worker: celery -A lpg_app worker --loglevel=INFO
beat: celery -A lpg_app beat --loglevel=INFO
