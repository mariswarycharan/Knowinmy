from django.forms import Form,ModelForm
from .models import *

class AsanaCreationForm(ModelForm):
    class Meta:
        model = Asana
        fields = ['name','no_of_postures']
