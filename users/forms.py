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


class StudentCourseMappingForm(ModelForm):
    # user = forms.ModelChoiceField(queryset=User.objects.none())
    # students_added_to_courses = forms.ModelMultipleChoiceField(queryset=CourseDetails.objects.none(), widget=forms.CheckboxSelectMultiple)

    class Meta:
        model=EnrollmentDetails
        fields=['user','students_added_to_courses']



    def __init__(self,*args,**kwargs):
        self.trainer_user=kwargs.pop('user',None)
        super(StudentCourseMappingForm,self).__init__(*args,**kwargs)
        if self.trainer_user:
            
            trainee_ids = TrainerLogDetail.objects.filter(trainer_name=self.trainer_user).first()
            client_name=trainee_ids.onboarded_by
            print(client_name,"print sts in fors.py")
            self.fields['user']=forms.ModelChoiceField(queryset=StudentLogDetail.objects.filter(added_by=client_name))
            print("hello world ", self.fields['user'].queryset)
            # print("Trainees: ", trainees)  # Debug: Check trainee list

            # Get courses added by these trainees
            self.fields['students_added_to_courses']=forms.ModelMultipleChoiceField(queryset= CourseDetails.objects.filter(user=self.trainer_user),widget=forms.CheckboxSelectMultiple)
            # self.fields['enrollment_created_by'].queryset=User.objects.filter(username=self.client_user)
            # print("Courses queryset: ", self.fields['students_added_to_courses'].queryset)  # Debug: Check courses queryset
          
        #    self.fields['trainee'].queryset=User.objects.filter(id__in=trainees)


    def clean_user(self):
        user = self.cleaned_data.get('user')
        if isinstance(user, StudentLogDetail):
            return user.student_name 
        return user
           
            
    



class CourseCreationForm(forms.ModelForm):
    class Meta:
        model = CourseDetails
        fields = ['course_name', 'description','asanas_by_trainer']



    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        print(self.user)
        
        super(CourseCreationForm,self).__init__(*args, **kwargs)

        if self.user:
            # Filter the queryset based on the asanas created by the current_user
            self.fields['asanas_by_trainer'] = forms.ModelMultipleChoiceField(
            queryset=Asana.objects.filter(created_by=self.user),widget=forms.CheckboxSelectMultiple)
        self.fields['description'].widget = forms.Textarea(attrs={'rows': 4})








