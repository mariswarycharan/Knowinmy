from distutils.command.upload import upload
from email.policy import default
from tabnanny import verbose
from django.db import models
from django.contrib.auth.models import User

#enable disable
class Asana(models.Model):
    name = models.CharField(max_length=100,verbose_name="Asana Name")
    no_of_postures = models.PositiveIntegerField(verbose_name="Number of Postures")
    created_by = models.ForeignKey(User,related_name="teaching_asans",on_delete=models.CASCADE,verbose_name="Created By")
    created_at = models.DateTimeField(verbose_name="Created At")
    last_modified_at = models.DateTimeField(verbose_name="Last Modified At")
    is_active = models.BooleanField(default=True)



#to add : created_by, created_at, is_active last modified, last_modified by, question bank
class Posture(models.Model):
    step_no = models.PositiveIntegerField(verbose_name="Step No")
    name = models.CharField(max_length=100,verbose_name="Posture Name")
    dataset = models.FileField(null=True,blank=True,upload_to="")
    asana = models.ForeignKey(Asana,related_name="related_postures",on_delete=models.CASCADE)
    # order = models.PositiveIntegerField(verbose_name="Posture Order")
    snap_shot = models.ImageField(verbose_name="Snap Shot", upload_to="images/", null=True, blank=True)
    last_modified_at = models.DateTimeField(verbose_name="Last Modified At",null=True)
    first_trained_at = models.DateTimeField(verbose_name="First Trained At",null=True)
    # last_modified_by = models.ForeignKey(User,related_name="trained_postures",on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)


status_choices = (
        (
            'PENDING','PENDING'
        ),
        (
            'ACCEPT','ACCEPT'
        ),
        (
            'REJECT','REJECT'
        ),
    )

# user data model
class Trainer_access_model(models.Model):
    user = models.ForeignKey(User,related_name="related_user_data",on_delete=models.CASCADE)
    trainer_status = models.CharField(null=True,max_length=30,blank=True,choices = status_choices,default='PENDING')
  

class Student_data_model(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    trainer = models.ForeignKey(Trainer_access_model,on_delete=models.CASCADE,null=True,default=None)
    student_status = models.CharField(null=True,max_length=30,blank=True,choices = status_choices,default='PENDING')

