import os

from celery import Celery


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lpg_app.settings")

app = Celery("lpg_app")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
