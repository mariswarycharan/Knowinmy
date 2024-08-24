import os
from celery import Celery,signals
import sentry_sdk

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "yoga.settings")
app = Celery("yoga")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@signals.celeryd_init.connect
def init_sentry(**_kwargs):
    sentry_sdk.init(...)  # same as above
