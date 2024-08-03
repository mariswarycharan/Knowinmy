from dataclasses import field
from pyexpat import model
from django.forms import Form,ModelForm,Textarea
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


    def __init__(self,*args,**kwargs):
        self.user=kwargs.pop('user',None)
        super(StudentCourseMappingForm,self).__init__(*args,**kwargs)
        if self.user:
            self.fields['students_added_to_courses'].queryset=CourseDetails.objects.filter(user=self.user)
            
    




class CourseCreationForm(forms.ModelForm):
    class Meta:
        model = CourseDetails
        fields = ['course_name', 'description']



    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        print(self.user)
        
        super(CourseCreationForm,self).__init__(*args, **kwargs)

        if self.user:
            # Filter the queryset based on the asanas created by the current_user
            self.fields['asanas_by_trainer  '] = forms.ModelChoiceField(
            queryset=Asana.objects.filter(created_by=self.user))
        self.fields['description'].widget = forms.Textarea(attrs={'rows': 4})






