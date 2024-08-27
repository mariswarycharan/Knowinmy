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
        fields = ['name', 'no_of_postures']

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)  # Extract tenant from kwargs
        super(AsanaCreationForm, self).__init__(*args, **kwargs)
        
    def save(self, commit=True):
        instance = super(AsanaCreationForm, self).save(commit=False)
        if self.tenant:
            instance.tenant = self.tenant  # Assign the tenant to the instance
        if commit:
            instance.save()
        return instance

class EditPostureForm(ModelForm):
    class Meta:
        model = Posture
        fields = ['name', 'snap_shot']

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super(EditPostureForm, self).__init__(*args, **kwargs)
        
    def save(self, commit=True):
        instance = super(EditPostureForm, self).save(commit=False)
        if self.tenant:
            instance.tenant = self.tenant  # Assign the tenant
        if commit:
            instance.save()
        return instance

        
# class CouponCodeForm(ModelForm):
#     class Meta:
#         model=
#         fields=[]


class StudentCourseMappingForm(ModelForm):
    class Meta:
        model = EnrollmentDetails
        fields = ['user', 'students_added_to_courses']

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        print(self.tenant,"line 57jhdk")
        self.trainer_user = kwargs.pop('user', None)
        print(self.trainer_user,"line 58  kjghskj")
        super(StudentCourseMappingForm, self).__init__(*args, **kwargs)
        
        if self.tenant and self.trainer_user:
            trainee_ids = TrainerLogDetail.objects.filter(tenant=self.tenant,trainer_name=self.trainer_user).first()
            print(trainee_ids,"loesfjkesjh")
            client_name = trainee_ids.onboarded_by
            print(client_name,"line no 66 in forms s")
            self.fields['user'] = forms.ModelChoiceField(
                queryset=StudentLogDetail.objects.filter(added_by=client_name, tenant=self.tenant),
                initial=self.instance.user if self.instance.pk else None
            )
            print("shgkjdhgggggggggggggggg",self.fields['user'])
            print(self.fields['user'],"line no 67 in forms ")
            self.fields['students_added_to_courses'] = forms.ModelMultipleChoiceField(
                queryset=CourseDetails.objects.filter(tenant=self.tenant,user=self.trainer_user),
                widget=forms.CheckboxSelectMultiple
            )



    def clean_user(self):
        user = self.cleaned_data.get('user')
        if isinstance(user, StudentLogDetail):
            print(user,"line no 60 in forms.py")
            return user.student_name 
        return user
           
            
    



class CourseCreationForm(forms.ModelForm):
    class Meta:
        model = CourseDetails
        fields = ['course_name', 'description', 'asanas_by_trainer']

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        print(kwargs,"line 93")
        print(args,"line 94")
        print(self.tenant,"line 93 forms.py")
        self.user = kwargs.pop('user', None)
        print(self.user,"line 94")
        super(CourseCreationForm, self).__init__(*args, **kwargs)

        if self.tenant and self.user:
            print(self.tenant,"line no 102 ")
            self.fields['asanas_by_trainer'] = forms.ModelMultipleChoiceField(
                queryset=Asana.objects.filter( tenant=self.tenant,created_by=self.user,),
                widget=forms.CheckboxSelectMultiple
            )
            print(self.user,"line 105 in forms.py")
            print(self.fields['asanas_by_trainer'] ,"line no 102 in forms.py ")
        self.fields['description'].widget = forms.Textarea(attrs={'rows': 2})

    def save(self, commit=True):
        instance = super(CourseCreationForm, self).save(commit=False)
        if self.tenant:
            instance.tenant = self.tenant  # Assign the tenant
        if commit:
            instance.save()
        return instance




class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['subscription', 'name', 'amount', 'status']

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super(OrderForm, self).__init__(*args, **kwargs)
        
    def save(self, commit=True):
        instance = super(OrderForm, self).save(commit=False)
        if self.tenant:
            instance.tenant = self.tenant  # Assign the tenant
        if commit:
            instance.save()
        return instance


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ['name', 'description', 'permitted_asanas', 'no_of_persons_onboard', 'price', 'highlight_status', 'created_at', 'updated_at']

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super(SubscriptionForm, self).__init__(*args, **kwargs)
        
    def save(self, commit=True):
        instance = super(SubscriptionForm, self).save(commit=False)
        if self.tenant:
            instance.tenant = self.tenant  # Assign the tenant
        if commit:
            instance.save()
        return instance




class OrganisationForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ['client_name', 'organization_name', 'domain_name', 'organization_email']

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super(OrganisationForm, self).__init__(*args, **kwargs)
        
    def save(self, commit=True):
        instance = super(OrganisationForm, self).save(commit=False)
        if self.tenant:
            instance.tenant = self.tenant  # Assign the tenant
        if commit:
            instance.save()
        return instance











class UserOnboardingForm(forms.ModelForm):
    ROLE_CHOICES = [
        ('trainer', 'Trainer'),
        ('student', 'Student')
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES)

    class Meta:
        model = User
        fields = ['username','first_name', 'last_name', 'email', 'role']
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)  # Extract tenant from kwargs
        super(UserOnboardingForm, self).__init__(*args, **kwargs)
        
    def save(self, commit=True):
        instance = super(UserOnboardingForm, self).save(commit=False)
        if self.tenant:
            instance.tenant = self.tenant  # Assign the tenant to the instance
        if commit:
            instance.save()
        return instance
