from decimal import Decimal
import json
import os
import time
from django.contrib.auth import authenticate, update_session_auth_hash
from django.http import HttpResponseRedirect
from .forms import ResetForm
from django.contrib.auth.hashers import make_password
from .tasks import *
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetView
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import *
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import  logout
from sentry_sdk import capture_exception
from django.views import View
# from bulkmodel.models import BulkModel

from django.db import transaction
from django.utils.decorators import method_decorator

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Avg
from django.views.decorators.csrf import csrf_exempt
from django.forms import formset_factory
from pyexpat.errors import messages
from django.contrib.auth.models import Group
from django.conf import settings
from django.shortcuts import get_object_or_404, render,redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from .models import *
from .forms import *
from django.contrib.auth import authenticate,login
from django.contrib import auth
from django.utils import timezone
from django.contrib.auth.decorators import login_required,user_passes_test
from .permissions import *
from django.contrib.auth.models import User, Group
from import_export.formats.base_formats import XLSX
from tablib import Dataset
import ast
from django.db import IntegrityError, transaction
import razorpay
import pandas as pd
import base64
from django.shortcuts import render
from openpyxl import load_workbook
import sweetify
from django.dispatch import receiver
from .models import Activity
from .utils import  calculate_asana_overall_accuracy, calculate_user_overall_accuracy
from django.views.decorators.http import require_http_methods


# for all the views need to handle permission denied ,viewsDoesNotExist,FieldError,ValidationError

def register(request):
    

    if request.method == "POST":

        email = request.POST.get("email")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        password = request.POST.get("password")
        user = User.objects.create_user(username=email,email=email,first_name=first_name,last_name=last_name,password=password)
        user.save()
        
      
        return redirect ('login')
    return render(request , "users/user_register.html")




@login_required
def profile_view(request):
    return render(request,'users/profile.html',{'user': request.user})

@login_required
@user_passes_test(check_client)
def subscription_payment(request):
    
        

    if request.method == "POST":
        name = request.POST.get("name")
        subscription_id = request.POST.get("subscription_id")
        coupon_code = request.POST.get("coupon_code")
        subscription = Subscription.objects.get(id=subscription_id)
        amount =Decimal( subscription.price)
        discounted_amount_after_negotiation = amount
        print(discounted_amount_after_negotiation)

        if coupon_code:
            print("entered to apply coupon code ")
            try:
                coupon = CouponCodeForNegeotiation.objects.get(code=coupon_code)
                discounted_percentage_for_client = Decimal(coupon.discount_percentage)
                discounted_amount_after_negotiation = amount - (discounted_percentage_for_client / Decimal(100)) * amount
                amount=discounted_percentage_for_client
            except CouponCodeForNegeotiation.DoesNotExist as e:
               print("no coupon found")
               capture_exception(e)
                # Proceed with the original amount if the coupon code is invalid

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        razorpay_order = client.order.create(
            {"amount": int(amount * 100), "currency": "INR", "payment_capture": "1"}
        )
        order = Order.objects.create(
            subscription=subscription,
            name=name,
            amount=amount,
            provider_order_id=razorpay_order["id"]
        )
        order.save()

        return render(
            request,
            "users/callback.html",
            {
                "callback_url": "http://" + "127.0.0.1:8000" + "/razorpay/callback/",
                "razorpay_key": settings.RAZORPAY_KEY_ID,
                "order": order,
                # 'idempo_token': idempo.token,
            },
        )
    return render(request, "users/subscription_plans.html")

  
  

@csrf_exempt
def callback(request):

    def verify_signature(response_data):
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        try:
            return client.utility.verify_payment_signature(response_data)
        except razorpay.errors.SignatureVerificationError:
            return False

    if "razorpay_signature" in request.POST:
        payment_id = request.POST.get("razorpay_payment_id", "")
        provider_order_id = request.POST.get("razorpay_order_id", "")
        signature_id = request.POST.get("razorpay_signature", "")
        order = Order.objects.get(provider_order_id=provider_order_id)
        order.payment_id = payment_id
        order.signature_id = signature_id
        order.save()
        
        if verify_signature(request.POST):
            order.status = 'ACCEPT'
            order.save()
            context={
                'order':order,
                # 'idempo_token': idempo.token,
            }
            
            print("SUCCESS")
            return render(request, "users/success.html",context)
        else:
            order.status = 'REJECT'
            order.save()
            print("FAILURE: Signature verification failed.")
            return render(request, "users/success.html", context={'order':order})
    else:
        try:
            payment_id = json.loads(request.POST.get("error[metadata]")).get("payment_id")
            provider_order_id = json.loads(request.POST.get("error[metadata]")).get("order_id")
        except (TypeError, json.JSONDecodeError, AttributeError) as e:
            print(f"Error parsing error metadata: {e}")
            capture_exception(e)
            return render(request, "users/callback.html", context={"status": 'REJECT'})

        order = Order.objects.get(provider_order_id=provider_order_id)
        order.payment_id = payment_id
        order.status = 'REJECT'
        order.save()
        print("FAILURE: Error in payment process.")
        return render(request, "users/callback.html", context={"status": order.status})

# integrity error need to handle in this view - username must be unique


@login_required
@user_passes_test(check_client)
def Trainer_approval_function(request):
    try:
        if request.method == 'POST':
            admin_user = request.user
            order_transaction = Order.objects.filter(name=admin_user, status='ACCEPT').first()

            if not order_transaction:
                sweetify.warning(request, "No transaction found", button="OK")
                return render(request, 'users/Trainer_approval_Page.html')

            subscription = order_transaction.subscription
            no_of_persons_onboard_by_client = subscription.no_of_persons_onboard
            print(no_of_persons_onboard_by_client,"kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk")

            # Handle file upload
            uploaded_file = request.FILES.get('excel_file')
            if uploaded_file:
                admin_user_id=admin_user.id
                print(admin_user_id,"ppppppppppppppppppppppppppppppppppppppp")
                # Save the uploaded file temporarily
                file_path = default_storage.save(f'temp/{uploaded_file.name}', ContentFile(uploaded_file.read()))
                print(file_path,"ooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo")
                
                # Pass file path and admin user ID to the Celery task
                process_excel_file.delay(file_path, admin_user_id, no_of_persons_onboard_by_client)
                print(process_excel_file,"lollllllllllllllll")

                sweetify.success(request, "Users are being onboarded, you'll be notified once done.", button="OK")
                print("success")
            else:
                sweetify.error(request, "No file uploaded!", button="OK")

            return render(request, 'users/Trainer_approval_Page.html')

        else:
            return render(request, 'users/Trainer_approval_Page.html')

    except Exception as e:
        print(e)
        capture_exception(e)
        return render(request, 'users/staff_dashboard.html')
    
# def get_excel_data(request,user_objs,admin_user,role_dict):
#     get_user_objs=process_excel_file(user_objs)
#     get_admin_user=Trainer_approval_function(admin_user)
#     success_count = 0
#     error_count = 0
#     user_objs = []
#     role_dict = {}
#     for user in get_user_objs:
#             role = role_dict[user.username]
#             group, created = Group.objects.get_or_create(name=role.capitalize())
#             user.groups.add(group)
#             print(f"Added {user.username} to group {group.name}")

#             if role == 'trainer':
#                         TrainerLogDetail.objects.create(
#                             trainer_name=user,
#                             onboarded_by=get_admin_user,
#                             no_of_asanas_created=0,
#                             created_at=timezone.now(),
#                             updated_at=timezone.now()
#                         )
#             else:
#                         StudentLogDetail.objects.create(
#                             student_name=user,
#                             added_by=get_admin_user,
#                             created_at=timezone.now(),
#                             updated_at=timezone.now()
#                         )
#                         success_count += 1
#             print(success_count,"lllllllllllllllllllllllllllllllll")
#             sweetify.success(request,"Users onboarded Successfully",button="OK")
#             return render(request, 'users/Trainer_approval_Page.html')
  

# @idempotent_view
def user_login(request):
    time.sleep(2)


    if request.user.is_authenticated:
        for group in request.user.groups.all():
            if group.name == 'Client':
                return render(request, 'users/Trainer_approval_Page.html')
            elif group.name == 'Trainer':
                return render(request, 'users/view_trained.html')
            else:
                return render(request, "users/staff_dashboard.html")
        return redirect("home")

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(username=user_obj.username, password=password)
            if user is not None:
                auth_login(request, user)
                for group in request.user.groups.all():
                    if group.name == 'Client':
                        return render(request, 'users/Trainer_approval_Page.html')
                    elif group.name == 'Trainer':
                        return render(request, 'users/view_trained.html')
                    else:
                        return redirect("staff_dashboard")
                return redirect("home")
            else:
                return render(request, "users/login.html", {
                    # 'idempo_token': idempo.token
                })
        except User.DoesNotExist as e:
            capture_exception(e)
            sweetify.warning(request,"User not found",button="OK")
            return render(request, "users/login.html", {
                # 'idempo_token': idempo.token
            })

    else:
        return render(request, "users/login.html", {
            # 'idempo_token': idempo.token
        })


def change_password(request):
    if request.method == 'POST':
        form = ResetForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            oldpassword = form.cleaned_data['oldpassword']
            newpassword = form.cleaned_data['newpassword1']

            try:
                user = User.objects.get(username=username)
                
                # Check if the old password is correct
                if user.check_password(oldpassword):
                    user.set_password(newpassword)
                    user.save()
                    
                    # Important: Update the session with the new password
                    update_session_auth_hash(request, user)
                    
                    # Redirect to a success page
                    return render(request, 'users/reset_success.html')

                else:
                    
                    form.add_error('oldpassword', 'Old password is incorrect.')
            except User.DoesNotExist:
                form.add_error('username', 'This username does not exist.')

        # If the form is invalid or the password check fails, re-render the form with errors
        return render(request, 'users/reset_password.html', {'form': form})
    else:
        form = ResetForm()
        return render(request, 'users/reset_password.html', {'form': form})

@login_required(login_url='login')
def log_out(request):
    try:
        auth.logout(request)
        sweetify.success(request,"User logged out successfully",button="OK")
    except Exception as e:
        messages.error(request, 'An error occurred while authentication.')
        print(e)
        return redirect("home")
    return redirect("login")

@login_required
@user_passes_test(check_trainer or check_client)
def view_trained(request):
    trained_asanas = Asana.objects.filter(created_by = request.user)
   
    return render(request,"users/view_trained.html",{
        "trained_asanas":trained_asanas,
        'is_trainer': True,
        

    })





@login_required
@user_passes_test(check_trainer  or  check_student)
def view_posture(request,asana_id):
    postures = Posture.objects.filter(asana=Asana.objects.get(id=asana_id)).order_by('step_no')
   
    return render(request,"users/view_posture.html",{
        "postures":postures,
        'is_trainer': True,
        
    })


class CreateAsanaView( UserPassesTestMixin, View):

    # time.sleep(5)
    print("hello")
    def test_func(self):
        return check_trainer(self.request.user) 



    def get_max_forms(self,request):
        trainee_name=self.request.user
        try:
            print(trainee_name)
            client_for_trainer = TrainerLogDetail.objects.filter(trainer_name=trainee_name).first()
            if client_for_trainer:
                client = client_for_trainer.onboarded_by
                no_of_asanas_created_by_trainee = client_for_trainer.no_of_asanas_created

                transaction = Order.objects.filter(name=client, status='ACCEPT').first()
                if transaction:
                    subscription = transaction.subscription
                    max_forms = subscription.permitted_asanas
                else:
                    max_forms = 1
                    no_of_asanas_created_by_trainee = 0
            else:
                max_forms = 1
                no_of_asanas_created_by_trainee = 0
        except Exception as e:
            print(f"Exception occurred: {e}")
            capture_exception(e)
            max_forms = 1
            no_of_asanas_created_by_trainee = 0

        return max_forms, no_of_asanas_created_by_trainee

    def get(self, request, *args, **kwargs):
        
        max_forms, no_of_asanas_created_by_trainee = self.get_max_forms(request.user)
        print(max_forms)
        
        AsanaCreationFormSet = formset_factory(AsanaCreationForm, extra=1, max_num=max_forms, validate_max=True, absolute_max=max_forms)

        if 'update' in request.GET:
            asana_id = request.GET.get('asana_id')
            print(asana_id)
            asana = Asana.objects.get(id=asana_id)
            form = AsanaCreationForm(instance=asana)
            sweetify.success(request,"Choose type of PO",button="OK")
            return render(request, "users/update_asana.html", {
                'form': form,
                'asana_id': asana_id,
                'is_trainer': True,
            })
            
        else:
            formset = AsanaCreationFormSet()
            return render(request, "users/create_asana.html", {
                'formset': formset,
                'is_trainer': True,
                'enable':True,
            })

     
    def post(self, request, *args, **kwargs):
        time.sleep(5)
        max_forms, no_of_asanas_created_by_trainee = self.get_max_forms(request.user)
        AsanaCreationFormSet = formset_factory(AsanaCreationForm, extra=1, max_num=max_forms, validate_max=True, absolute_max=max_forms)
        created_asanas_by_trainer = TrainerLogDetail.objects.get(trainer_name=request.user)
        remaining_forms = max_forms - no_of_asanas_created_by_trainee

        if 'update_asana' in request.POST:
            asana_id = request.POST.get('asana_id')
            asana = Asana.objects.get(id=asana_id)
            form = AsanaCreationForm(request.POST, instance=asana)
            if form.is_valid():
                form.save()
                return redirect("view-trained")
            else:
                return render(request, "users/update_asana.html", {
                    'form': form,
                    'asana_id': asana_id,
                    'is_trainer': True,
                })

        elif 'delete_asana' in request.POST:
            asana_id = request.POST.get('asana_id')
            asana =get_object_or_404(Asana,id=asana_id)
            
            created_asanas_by_trainer.no_of_asanas_created -= 1
            created_asanas_by_trainer.save()
            asana.delete()
            return redirect("view-trained")

        else:
            
            formset = AsanaCreationFormSet(request.POST)
            if formset.is_valid():
                  print("entered          llllllllllll")
                  for form in formset:
                    print("888888888888888")
                    if remaining_forms > 0:
                        
                        asana = form.save(commit=False)
                        asana.created_by = request.user
                        asana.created_at = timezone.now()
                        asana.last_modified_at = timezone.now()
                        print("asssssssssssssssssssssssssss ")
                        asana.save()

                        created_asanas_by_trainer.no_of_asanas_created += 1
                        # created_asanas_by_trainer.asanas_by_trainer.add(asana)
                        # created_asanas_by_trainer.user = request.user
                        # created_asanas_by_trainer.course_name = course_name
                        # created_asanas_by_trainer.description = description
                        created_asanas_by_trainer.created_at = timezone.now()
                        created_asanas_by_trainer.updated_at = timezone.now()
                        created_asanas_by_trainer.save()

                        for i in range(1, asana.no_of_postures + 1):
                            Posture.objects.create(name=f"Step-{i}", asana=asana, step_no=i)

                        no_of_asanas_created_by_trainee += 1
                        remaining_forms -= 1
                        print(remaining_forms,"lllllllllllllllllllllllllllllllllllllllllllll")
                    return redirect("view-trained")
            else:


                return render(request, "users/create_asana.html", {
                    'formset': formset,
                    'is_trainer': True,
                })


    


class CourseCreationView(LoginRequiredMixin, UserPassesTestMixin, View):
    # idempo_redirect = 'view-trained'  # Where to redirect if a duplicate POST request is detected

    def test_func(self):
        return check_trainer(self.request.user)



    def get(self, request, *args, **kwargs):
        current_user = self.request.user
        course_id = request.GET.get('course_id')
        if course_id:
            course = get_object_or_404(CourseDetails, id=course_id)
            form = CourseCreationForm(instance=course, user=self.request.user)
            return render(request, "users/update_course.html", {
                'form': form,
                'course_id': course_id,
                'is_trainer': True,
            })
        else:
            form = CourseCreationForm(user=self.request.user)
            courses = CourseDetails.objects.filter(user=current_user)
            return render(request, "users/trainer_dashboard.html", {
                'form': form,
                'is_trainer': True,
                'courses': courses,
            })

    def post(self, request, *args, **kwargs):
        time.sleep(5)
        course_id = request.POST.get('course_id')
        current_user = self.request.user
        if 'update_course' in request.POST:
            course = get_object_or_404(CourseDetails, id=course_id)
            form = CourseCreationForm(request.POST, instance=course, user=self.request.user)
            if form.is_valid():
                form.save() 
                # form.save_m2m()  # Save many-to-many data
                return redirect('view-trained')
            else:
                return render(request, "users/update_course.html", {
                    'form': form,
                    'course_id': course_id,
                    'is_trainer': True,
                })

        elif 'delete_course' in request.POST:
            course = get_object_or_404(CourseDetails, id=course_id)
            course.delete()
            return redirect('view-trained')

        else:
            form = CourseCreationForm(request.POST, user=self.request.user)
            if form.is_valid():
                course = form.save(commit=False)
                course.user = request.user
                course.created_at = timezone.now()
                course.updated_at = timezone.now()
                course.save()  # Save the instance to the database
                form.save_m2m()  # Save many-to-many data

                return render(request,'users/trainer_dashboard.html')
            else:
                return render(request, "users/trainer_dashboard.html", {
                    'form': form,
                    'is_trainer': True,
                })



@login_required
# @user_passes_test(check_student)
def home(request):
    subscriptions = Subscription.objects.all()
    return render(request,"users/home.html",{'subscriptions':subscriptions})

@login_required
@user_passes_test(check_student)
def staff_dashboard_function(request):
    user = request.user

    if user.groups.filter(name='Trainer').exists() or user.is_superuser:
        is_trainer = True
    else:
        is_trainer = False

    context = {
        'is_trainer': is_trainer,
    }
    
    return render(request,"users/staff_dashboard.html",context)

@login_required
@user_passes_test(check_trainer)
def edit_posture(request,posture_id):
  
    posture = Posture.objects.get(id=posture_id)
    if request.method == "POST":
        if "meta_details" in request.POST:
            form = EditPostureForm(request.POST,instance=posture)
            if form.is_valid():
                form.save()
        else:
            name = f"{posture.asana.name}_{posture.step_no}.csv"
            dataset = ast.literal_eval(request.POST["dataset"])
            dataset = pd.DataFrame(dataset)
            dataset = dataset.transpose()
            dataset.to_csv(f'./media/{name}',index=False,header=False)
            posture.dataset.name = name
            decoded_data=base64.b64decode(request.POST['snapshot'])
            img_file = open(f"./media/images/{posture_id}.png", 'wb')
            img_file.write(decoded_data)
            img_file.close()
            posture.snap_shot.name = f"./images/{posture_id}.png"
            posture.save()
            
    print("edit_posture")
    form = EditPostureForm(instance=posture)
    return render(request, "users/edit_posture.html",{
        "form":form,
        "posture":posture,
        'is_trainer': True,
       
        
    })







class  StudentCourseMapView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return check_trainer(self.request.user)
   
    def get_enrollment_details(self,user):
        trainer_details=TrainerLogDetail.objects.filter(trainer_name=self.request.user).first()
        if trainer_details:
            client_name=trainer_details.onboarded_by
            print(client_name,"loll")
            enrolled_studs = list(StudentLogDetail.objects.filter(added_by=client_name))
            print(enrolled_studs,"line 621")
            if enrolled_studs:
# here i need to add empty result set exceptions 
                
                 student_name = []
                 for student in enrolled_studs:
                           student_name.append(student.student_name)

                 print(type(student_name),student_name, "line 45465768")
                 students = User.objects.filter(username__in=student_name)
                 print(students,"lopppppppppppppghrdhj")
            
        
                 enrollment_details=EnrollmentDetails.objects.filter(user__in=students)
                 return enrollment_details
        
            
        
        else:
            print("No students found")



    def get(self, request, *args, **kwargs):
        enrollment_details=self.get_enrollment_details(request.user)
        print(enrollment_details,"kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk")
        current_user = self.request.user
        enrollment_id = request.GET.get('enrollment_id')
        
        print(enrollment_id,"kopopokjodjskja")


        print(f"GET request received with enrollment_id: {enrollment_id}")


        
        print("oooooooooooooooooooooooooooooooooooooooo")
       
        if  enrollment_id:
            try:
                 print("yet to update ","idsfsei")
                 print(enrollment_id,"llllllllllllllllllll")
                 enrollment = get_object_or_404(EnrollmentDetails, id=enrollment_id)
                 print(enrollment,"sjfdssssssssssssssssssssssssssssssssssssssssss    ")
                 form = StudentCourseMappingForm(instance=enrollment, user=self.request.user)
          
                 print(f"GET request received with enrollment_id for updation : {enrollment_id}")
                 return render(request, "users/update_student_course_form.html", {
                             'form': form,
                             'enrollment_id': enrollment_id,
})
            except ValueError as e:
                print(f"Invalid enrollment_id: {enrollment_id}")
                capture_exception(e)
                return render(request, "users/student_mapping.html", {
                    'form': form,
                    'enrollment_details': enrollment_details,
                    'error': 'Invalid enrollment ID provided.'
                })

           

  
  
        else:
            print("lopp end")
            form = StudentCourseMappingForm(user=self.request.user)
            
            # print(enrollment_details,'line 211')
            return render(request, "users/student_mapping.html", {
                'form': form,
                 'enrollment_details': enrollment_details,
            })
   
    def post(self, request, *args, **kwargs):
        time.sleep(5)
        print("hello world ")
        enrollment_id = request.POST.get('enrollment_id')
        enrollment_details=self.get_enrollment_details(request.user)
        print(enrollment_id,"opppppppppppppppppppp")
        current_user = self.request.user
        print(current_user,"ooooooooooooooo")


       
        print("lollllllllllllllllllllllllll")
        if 'update_course_map_form' in request.POST:
            
            
            try:
                print("enterde to edit ")
                enrollment_id=request.POST.get('enrollment_id')
                print(enrollment_id,"kkkkkkkkkkkkkkkkk")
                enrollment = get_object_or_404(EnrollmentDetails, id=enrollment_id)
                form = StudentCourseMappingForm(request.POST, instance=enrollment, user=current_user)
                if form.is_valid():
                     form.save()
                     return render(request,'users/student_mapping.html',{
                                 'enrollment_details': enrollment_details,
                                #    'enrolled_courses':enrolled_courses,
                                 'enrollment_id': enrollment_id,
                })
                else:
                    return render(request, "users/update_student_course_form.html", {
                    'form': form,
                    'enrollment_id': enrollment_id,
                })
            except EnrollmentDetails.DoesNotExist as e:
                print(f"No EnrollmentDetails found with id: {enrollment_id}")
                capture_exception(e)
                return render(request, "users/student_mapping.html", {
                    'form': form,
                    # 'enrollment_details': enrollment_details,
                    'error': f'No EnrollmentDetails found with id: {enrollment_id}'
                })


            
        elif 'delete_course_map_form' in request.POST and enrollment_id:
          try:
            enrollment = get_object_or_404(EnrollmentDetails, id=enrollment_id)
            enrollment.delete()
            print(f"GET request received with enrollment_id: {enrollment_id}")
            return render(request,'users/trainer_dashboard.html')

            
          except EnrollmentDetails.DoesNotExist as e:
                print(f"No EnrollmentDetails found with id: {enrollment_id}")
                capture_exception(e)
                return render(request, "users/student_mapping.html", {
                    'form': form,
                    'enrollment_details': enrollment_details,
                    'error': f'No EnrollmentDetails found with id: {enrollment_id}'
                })
              

        else:
            form = StudentCourseMappingForm(request.POST, user=current_user)
            if form.is_valid():
                enrollment = form.save(commit=False)
                enrollment.created_at = timezone.now()
                enrollment.updated_at = timezone.now()
                enrollment.save()   
                form.save_m2m()
                return render(request, "users/trainer_dashboard.html", {
                    'form': form,
                     'enrollment_details': enrollment_details,
                     'enrollment_id': enrollment_id,
                })
            else:
                
                    
                print(f"GET request received with enrollment_id: {enrollment_id}")

                print(enrollment_details,'line 211')
                return render(request, "users/trainer_dashboard.html", {
                    'form': form,
                    # 'enrollment_details': enrollment_details,
                     'enrollment_id': enrollment_id,
                })







@login_required
@user_passes_test(check_student)
def user_view_asana(request):


    current_user=request.user
    print(current_user)

    enrolled_student_to_courses=EnrollmentDetails.objects.filter(user=current_user)
    trainer_asanas=[]
    if enrolled_student_to_courses.exists():
        all_courses=[]
        for enrollment in enrolled_student_to_courses:
            all_courses.extend(enrollment.students_added_to_courses.all())

            print(all_courses)
        
       
        
        for course in all_courses:
            trainer=course.user
            print(trainer)
            if trainer:
                asanas=CourseDetails.objects.filter(user=trainer)
                print(asanas,"llllllllllllllllllllllllllll")
                trainer_asanas.extend(asanas)
        return render(request, "users/user_view_asana.html", {
        
             "trainer_asanas": trainer_asanas,
            
       })
    else:
        print("You are not enrroled into this course")
        return render(request,"users/user_view_asana.html")




@login_required
@user_passes_test(check_student)
def user_view_posture(request,asana_id):
    try:
            postures = Posture.objects.filter(asana=Asana.objects.get(id=asana_id)).order_by('step_no')
            print(postures)
            
            print("user_view_posture") 
            return render(request,"users/user_view_posture.html",{
                  "postures":postures,
                   'is_trainer': True,
        
           })
    except Exception as e:
        capture_exception(e)    
        return JsonResponse({"error": "An error occurred"}, safe=False)





@login_required
@user_passes_test(check_student)
def get_posture(request,posture_id):
    if request.method == "GET":
        link = str(Posture.objects.get(id=posture_id).snap_shot.url)
        return JsonResponse({"url":link})
    else:
        return JsonResponse({"error": "expected GET method"})
    




@login_required
@user_passes_test(check_student)
def get_posture_dataset(request):
    if request.method == "GET":
        data = {}
        posture_id = request.GET['posture_id']
        posture = Posture.objects.get(id=posture_id)
        dataset = pd.read_csv(posture.dataset.path,header=None)
        dataset = dataset.values.tolist()
        data["dataset"] = dataset
        data["snapshot"] = posture.snap_shot.url
        
        return JsonResponse(data)
    else:
        return JsonResponse(status=400,data={"error":"Bad request"})
    

# @login_required
# @user_passes_test(check_client)
# def subscription_plans(request):
#     subscriptions= Subscription.objects.all()
#     return render(request,'users/subscription_plans.html',{'subscriptions':subscriptions}) 


@login_required
def dashboard(request):
    user = request.user
    user_groups = user.groups.values_list('name', flat=True)
    asanas = Asana.objects.filter(created_by=user)
    asana_accuracies = [
        {
            'asana': asana,
            
        }
        for asana in asanas
    ]
    user_overall_accuracy = calculate_user_overall_accuracy(user)
    
  


    context = {
        'activities': Activity.objects.filter(user=user).order_by('-timestamp'),
        'user_groups': user_groups,
     
    }

    if 'Client' in user_groups:
        context.update({
            'created_asana': Asana.objects.filter(created_by=user).count(),
            'uploaded_file': Activity.objects.filter(activity_type='Uploaded Excel File',user=user).count(),
        })
        
        return render(request, 'users/activity_log_users.html', context)

    elif 'Trainer' in user_groups:
        context.update({
            'created_asana': Asana.objects.filter(created_by=user).count(),
            'edited_posture': Activity.objects.filter(activity_type='Edited asana',user=user).count(),
            
           
        })
        
        return render(request, 'users/activity_log_users.html', context)

    elif 'Student' in user_groups:
        context.update({
            'viewed_asana': Activity.objects.filter(activity_type='view_trained',user=user).count(),
            'viewed_posture': Activity.objects.filter(activity_type='view_posture',user=user).count(),
      
           
        })
       
        return render(request, 'users/activity_log_users.html', context)

    else:
        return render(request, 'users/activity_log_users.html', context)
    

















