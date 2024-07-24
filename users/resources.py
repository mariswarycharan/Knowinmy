from import_export import resources
from django.contrib.auth.models import User, Group

class PersonResource(resources.ModelResource):

    def __init__(self, *args, **kwargs):
        super(PersonResource, self).__init__(*args, **kwargs)
        self.context = {}

    def init_instance(self, row=None):
        instance = super(PersonResource, self).init_instance(row)
        if 'roles' in self.context:
            self._roles = self.context['roles']
        else:
            self._roles = {}
        return instance

    def before_save_instance(self, instance, using_transactions, dry_run):
        role = self._roles.get(instance.username)
        if role:
            group, created = Group.objects.get_or_create(name=role.capitalize())
            instance.groups.add(group)
        return super(PersonResource, self).before_save_instance(instance, using_transactions, dry_run)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'roles','password')
        import_id_fields = ('username',)
