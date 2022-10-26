from dataclasses import field
from pyexpat import model
from django.forms import Form,ModelForm
from .models import *

class AsanaCreationForm(ModelForm):
    class Meta:
        model = Asana
        fields = ['name','no_of_postures']


class EditPostureForm(ModelForm):
    class Meta:
        model = Posture
        fields = ['name','snap_shot']