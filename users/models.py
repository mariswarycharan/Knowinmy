
from email.policy import default
import secrets
from tabnanny import verbose
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _ 
from django.db.models.signals import post_save

# from *cons import PaymentStatus

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
class CourseDetails(models.Model):
    course_name = models.CharField(verbose_name="Course Name", max_length=100)
    description = models.TextField(max_length=200)
    user= models.ForeignKey(User, verbose_name="Trainee Name", on_delete=models.CASCADE, related_name="trainee_name",null=True,blank=True)
    # added_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="courses_added",null=True,blank=True)
    asanas_by_trainer=models.ForeignKey(Asana,on_delete=models.CASCADE,related_name="asanas_created_by_trainee",null=True,blank=True)
    trainee_status= models.CharField(max_length=10, choices=status_choices, default='PENDING')
    no_of_asanas_created=models.PositiveIntegerField(null=True,blank=True,default=0)
    created_at=models.DateTimeField(verbose_name='Created at',null=True)
    updated_at= models.DateTimeField(verbose_name='Last modified at',null=True)
    # adding_student_to_course=models.ManyToManyField(User)
    
class EnrollmentDetails(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="enrolled_courses", verbose_name="Student Name", null=True, blank=True)
    added_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="enrollments_added", null=True, blank=True)
    # trainer = models.ForeignKey(CourseDetails, on_delete=models.SET_NULL, related_name="trainer_enrollments", null=True, blank=True, verbose_name="name")
    student_status=models.CharField(max_length=10, choices=status_choices, default='PENDING')
    created_at=models.DateTimeField(verbose_name='Created at',null=True)
    updated_at= models.DateTimeField(verbose_name='Last modified at',null=True)
    students_added_to_courses=models.ManyToManyField(CourseDetails,related_name="course_asanas", blank=True)



class Activity(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    activity_type = models.CharField(max_length =100)
    description = models.TextField()
    timestamp= models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}-{self.activity_type} at {self.timestamp}"



class Subscription(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=100)
    permitted_asanas = models.PositiveIntegerField(default=None)
    no_of_persons_onboard =models.PositiveIntegerField(default=None)
    price =  models.FloatField(default= None)
    highlight_status = models.BooleanField(default=False)
    created_at=models.DateTimeField(verbose_name='Created at',null=True)
    updated_at= models.DateTimeField(verbose_name='Last modified at',null=True)


class Order(models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='orders')
    name = models.CharField(_("Customer Name"), max_length=254, blank=False, null=False)
    amount = models.FloatField(_("Amount"), null=False, blank=False)
    status = models.CharField(_("Payment Status"), max_length=10, choices=status_choices, default='PENDING')
    provider_order_id = models.CharField(_("Order ID"), max_length=40, null=False, blank=False)
    payment_id = models.CharField(_("Payment ID"), max_length=36, null=False, blank=False)
    signature_id = models.CharField(_("Signature ID"), max_length=128, null=False, blank=False)
    created_at=models.DateTimeField(verbose_name='Created at',null=True)
    updated_at= models.DateTimeField(verbose_name='Last modified at',null=True)

    def __str__(self):
        return f"{self.id}-{self.name}-{self.status}"
    



# class NumberOfAsana(models.Model):
#     asanas_created_by_user=models.ForeignKey(User,on_delete=models.CASCADE)
#     no_of_asanas_created=models.PositiveIntegerField(null=True,blank=True,default=0)



class PostureAccuracy(models.Model):
    asana_for_accuracy = models.ForeignKey(Asana, related_name='postures', on_delete=models.CASCADE)
    user_to_calculate = models.ForeignKey(User, related_name='posture_accuracies', on_delete=models.CASCADE)

    accuracy = models.FloatField(null=True,blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)


class CouponCodeForNegeotiation(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='coupon_code_for_client')
    subscription_for_coupon_code=models.ForeignKey(Subscription,on_delete=models.CASCADE)
    discount_percentage=models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, default=0)
    code=models.CharField(max_length=8, blank=True, null=True, unique=True)




    @classmethod
    def post_create(cls, sender, instance, created, *args, **kwargs):
        """
        Connected to the post_save signal of the UniqueCodes model. This is used to set the
        code once we have created the db instance and have access to the primary key (ID Field)
        """
        # If new database record
        if created:
            # We have the primary key (ID Field) now so let's grab it
            id_string = str(instance.id)
            # Define our random string alphabet (notice I've omitted I,O,etc. as they can be confused for other characters)
            upper_alpha = "ABCDEFGHJKLMNPQRSTVWXYZ"
            # Create an 8 char random string from our alphabet
            random_str = "".join(secrets.choice(upper_alpha) for i in range(8))
            # Append the ID to the end of the random string
            instance.code = (random_str + id_string)[-8:]
            # Save the class instance
            instance.save()

    def __str__(self):
        return "%s" % (self.code,)
post_save.connect(CouponCodeForNegeotiation.post_create, sender=CouponCodeForNegeotiation)