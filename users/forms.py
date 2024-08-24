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
        self.trainer_user = kwargs.pop('user', None)
        super(StudentCourseMappingForm, self).__init__(*args, **kwargs)
        
        if self.tenant and self.trainer_user:
            trainee_ids = TrainerLogDetail.objects.filter(trainer_name=self.trainer_user, tenant=self.tenant).first()
            client_name = trainee_ids.onboarded_by
            self.fields['user'] = forms.ModelChoiceField(
                queryset=StudentLogDetail.objects.filter(added_by=client_name, tenant=self.tenant),
                initial=self.instance.user if self.instance.pk else None
            )
            self.fields['students_added_to_courses'] = forms.ModelMultipleChoiceField(
                queryset=CourseDetails.objects.filter(user=self.trainer_user, tenant=self.tenant),
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
        self.user = kwargs.pop('user', None)
        super(CourseCreationForm, self).__init__(*args, **kwargs)

        if self.tenant and self.user:
            self.fields['asanas_by_trainer'] = forms.ModelMultipleChoiceField(
                queryset=Asana.objects.filter(created_by=self.user, tenant=self.tenant),
                widget=forms.CheckboxSelectMultiple
            )
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












