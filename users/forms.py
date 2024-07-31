from dataclasses import field
from pyexpat import model
from django.forms import Form,ModelForm
from .models import *
# import the standard Django Forms
# from built-in library
from django import forms 

class AsanaCreationForm(ModelForm):
    class Meta:
        model = Asana
        fields = ['name','no_of_postures']


class EditPostureForm(ModelForm):
    class Meta:
        model = Posture
        fields = ['name','snap_shot']
        
# class CouponCodeForm(ModelForm):
#     class Meta:
#         model=
#         fields=[]


class StudentCourseMappingForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.filter(groups__name='Student'))
    students_added_to_courses = forms.ModelMultipleChoiceField(queryset=CourseDetails.objects.all(), widget=forms.CheckboxSelectMultiple)

