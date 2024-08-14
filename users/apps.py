from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    # def ready(self):
    #     # Import celery app now that Django is mostly ready.
    #     # This initializes Celery and autodiscovers tasks
    #     import users.celery
