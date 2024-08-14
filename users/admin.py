from django.apps import apps
from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .resources import PersonResource
from django_celery_results.models import TaskResult


class ListAdminMixin(object):
    def __init__(self, model, admin_site):
        self.list_display = [field.name for field in model._meta.fields]
        self.search_fields = [field.name for field in model._meta.fields]
        super(ListAdminMixin, self).__init__(model, admin_site)


models = apps.get_models()
for model in models:
    admin_class = type('AdminClass', (ListAdminMixin, admin.ModelAdmin), {})
    try:
        admin.site.register(model, admin_class)
    except admin.sites.AlreadyRegistered:
        pass







class PersonAdmin(ImportExportModelAdmin):
    resource_class = PersonResource
