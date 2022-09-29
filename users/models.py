from distutils.command.upload import upload
from tabnanny import verbose
from django.db import models
from django.contrib.auth.models import User


class Asana(models.Model):
    name = models.CharField(max_length=100,verbose_name="Asana Name")
    no_of_postures = models.PositiveIntegerField(verbose_name="Number of Postures")
    created_by = models.ForeignKey(User,related_name="teaching_asans",on_delete=models.CASCADE,verbose_name="Created By")
    created_at = models.DateTimeField(verbose_name="Created At")
    last_modified_at = models.DateTimeField(verbose_name="Last Modified At")


#to add : created_by, created_at, is_active
class Posture(models.Model):
    name = models.CharField(max_length=100,verbose_name="Posture Name")
    dataset = models.FileField(null=True,blank=True,upload_to="media/")
    asana = models.ForeignKey(Asana,related_name="related_postures",on_delete=models.CASCADE)
    order = models.PositiveIntegerField(verbose_name="Posture Order")


