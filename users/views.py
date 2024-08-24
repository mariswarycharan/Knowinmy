from decimal import Decimal
import json
import os
from .tables import *
import time
from django.db.models import F
from django.contrib.auth import authenticate, update_session_auth_hash
from django.http import HttpResponseRedirect

from django.contrib.auth.hashers import make_password
from .tasks import *
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.urls import reverse, reverse_lazy
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
        
      
        return redirect('register_organization')
    return render(request , "users/user_register.html")




@login_required
def profile_view(request,slug):
    tenant=Tenant.objects.get(slug=slug)
    print(tenant,"line 87")
    
    return render(request,'users/profile.html',{'user': request.user,"slug":slug})

@login_required
@user_passes_test(check_client)
def subscription_payment(request):
    tenant = request.tenant  # Assuming the tenant is set in the middleware

    if request.method == "POST":
        name = request.POST.get("name")
        subscription_id = request.POST.get("subscription_id")
        coupon_code = request.POST.get("coupon_code")
        subscription = Subscription.objects.get(id=subscription_id, tenant=tenant)  # Filter by tenant
        amount = Decimal(subscription.price)
        discounted_amount_after_negotiation = amount

        if coupon_code:
            try:
                coupon = CouponCodeForNegeotiation.objects.get(code=coupon_code, tenant=tenant)
                discounted_percentage_for_client = Decimal(coupon.discount_percentage)
                discounted_amount_after_negotiation = amount - (discounted_percentage_for_client / Decimal(100)) * amount
                amount = discounted_amount_after_negotiation
            except CouponCodeForNegeotiation.DoesNotExist as e:
                print("No coupon found")
                capture_exception(e)
                # Proceed with the original amount if the coupon code is invalid

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        razorpay_order = client.order.create(
            {"amount": int(amount * 100), "currency": "INR", "payment_capture": "1"}
        )
        order = Order.objects.create(
            tenant=tenant,
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
            },
        )
    return render(request, "users/subscription_plans.html")



@csrf_exempt
def callback(request):
    tenant = request.tenant  # Assuming the tenant is set in the middleware

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
        order.tenant=request.tenant
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
        # Get the tenant from the request
        tenant = request.tenant if request.tenant else None

        if tenant is None:
            return render(request, 'error.html', {'message': 'Tenant not found'})

        if request.method == 'POST':
            admin_user = request.user

            # Ensure that you're filtering orders based on the tenant
            order_transaction = Order.objects.filter(
                name=admin_user,
                status='ACCEPT',
                tenant=tenant  # Filter based on tenant
            ).first()

            if not order_transaction:
                sweetify.warning(request, "No transaction found", button="OK")
                return render(request, 'users/Trainer_approval_Page.html')

            subscription = order_transaction.subscription
            no_of_persons_onboard_by_client = subscription.no_of_persons_onboard

            # Handle file upload
            uploaded_file = request.FILES.get('excel_file')
            if uploaded_file:
                admin_user_id = admin_user.id

                # Save the uploaded file temporarily
                file_path = default_storage.save(f'temp/{uploaded_file.name}', ContentFile(uploaded_file.read()))
                
                # Pass file path, admin user ID, and tenant information to the Celery task
                process_excel_file.delay(file_path, admin_user_id, no_of_persons_onboard_by_client, tenant.slug)

                sweetify.success(request, "Users are being onboarded, you'll be notified once done.", button="OK")
            else:
                sweetify.error(request, "No file uploaded!", button="OK")

            return render(request, 'users/Trainer_approval_Page.html')

        else:
            return render(request, 'users/Trainer_approval_Page.html')

    except Exception as e:
        print(e)
        capture_exception(e)
        return render(request, 'users/staff_dashboard.html')
    


@login_required
@user_passes_test(check_superuser)   
def client_list(request):
    table=ClientTable(Order.objects.all())

    print(table,"print this tosd")
    return render(request,'users/client_table.html',{'table':table})










@login_required
def onboarding_view(request):
    admin_user = request.user
    tenant = request.tenant  # Assuming tenant is set in middleware

    # Filter the order by tenant and user
    order_transaction = Order.objects.filter(name=admin_user, status='ACCEPT', tenant=tenant).first()

    if not order_transaction:
        sweetify.warning(request, "No transaction found", button="OK")
        print("No transaction found")
        return render(request, 'users/Trainer_approval_Page.html')

    subscription = order_transaction.subscription
    print(subscription, "Subscription Details")
    no_of_persons_onboard_by_client = subscription.no_of_persons_onboard
    print(no_of_persons_onboard_by_client, "Max Persons to Onboard")

    # Check if the ClientOnboarding record exists for the current user within the tenant
    client_onboarding, created = ClientOnboarding.objects.get_or_create(
        client=admin_user,
        tenant=tenant,  # Filter by tenant
        defaults={'trainers_onboarded': 0, 'students_onboarded': 0}
    )

    # Calculate the maximum number of forms to display
    max_forms = no_of_persons_onboard_by_client - (
        client_onboarding.trainers_onboarded + client_onboarding.students_onboarded
    )
    remaining_forms = max_forms
    print(remaining_forms, "Remaining Forms to Onboard")

    # Create the formset
    UserFormSet = formset_factory(UserOnboardingForm, extra=1, max_num=max_forms, validate_max=True)

    if request.method == 'POST':
        formset = UserFormSet(request.POST)

        if formset.is_valid():
            for form in formset:
                user = form.save(commit=False)
                user.set_unusable_password()  # or set a random password if you prefer
                user.save()

                role = form.cleaned_data.get('role')
                if role == 'trainer':
                    TrainerLogDetail.objects.create(
                        trainer_name=user,
                        onboarded_by=admin_user,
                        tenant=tenant,  # Associate with the tenant
                        no_of_asanas_created=0
                    )
                    # Update ClientOnboarding model
                    client_onboarding.trainers_onboarded = F('trainers_onboarded') + 1
                else:
                    StudentLogDetail.objects.create(
                        student_name=user,
                        added_by=admin_user,
                        tenant=tenant  # Associate with the tenant
                    )
                    # Update ClientOnboarding model
                    client_onboarding.students_onboarded = F('students_onboarded') + 1

            # Save the updated counts to the database
            client_onboarding.save()
            remaining_forms -= len(formset)
            print(remaining_forms, "Remaining Forms after Onboarding")
            return render(request, 'users/Trainer_approval_Page.html')

    else:
        formset = UserFormSet()

    return render(request, 'users/onboarding_form.html', {'formset': formset})


def user_login(request):



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



@login_required(login_url='login')
def log_out(request):
    try:
        auth.logout(request)  # Logout the user
        sweetify.success(request, "User logged out successfully", button="OK")
        
        # Redirect based on the presence of tenant slug in the URL
        if hasattr(request, 'tenant') and request.tenant:
            return redirect('home', slug=request.tenant.slug)
        else:
            return redirect('home')  # Redirect to the normal home page if no tenant slug
    except Exception as e:
        messages.error(request, 'An error occurred while logging out.')
        print(e)
        return redirect('home')  # Redirect to the home page in case of error

@login_required
@user_passes_test(check_trainer or check_client)
def view_trained(request,slug):

    tenant = Tenant.objects.get(slug=slug)
    print(tenant,"Line 404") # Assuming tenant is set in middleware
    trained_asanas = Asana.objects.filter(created_by=request.user, tenant=tenant)
   
    return render(request, "users/view_trained.html", {
        "trained_asanas": trained_asanas,
        'is_trainer': True,
        'tenant':tenant
    })


@login_required
@user_passes_test(check_trainer or check_student)
def view_posture(request, asana_id,slug):
    tenant = Tenant.objects.get(slug=slug) # Assuming tenant is set in middleware

    # Ensure the asana belongs to the tenant
    asana = Asana.objects.get(id=asana_id, tenant=tenant)
    
    # Filter postures by asana and tenant
    postures = Posture.objects.filter(asana=asana).order_by('step_no')
   
    return render(request, "users/view_posture.html", {
        "postures": postures,
        'is_trainer': True,
        'tenant':tenant
    })

class CreateAsanaView(UserPassesTestMixin, View):

    def test_func(self):
        return check_trainer(self.request.user)

    def get_max_forms(self, request,slug):
        trainee_name = self.request.user
        tenant = Tenant.objects.get(slug=slug)  # Assuming tenant is set in middleware
        try:
            print(trainee_name)
            client_for_trainer = TrainerLogDetail.objects.filter(trainer_name=trainee_name, tenant=tenant).first()
            if client_for_trainer:
                client = client_for_trainer.onboarded_by
                no_of_asanas_created_by_trainee = client_for_trainer.no_of_asanas_created

                transaction = Order.objects.filter(name=client, status='ACCEPT', tenant=tenant).first()
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
        tenant = request.tenant  # Assuming tenant is set in middleware
        max_forms, no_of_asanas_created_by_trainee = self.get_max_forms(request)
        print(max_forms)

        AsanaCreationFormSet = formset_factory(AsanaCreationForm, extra=1, max_num=max_forms, validate_max=True, absolute_max=max_forms)

        if 'update' in request.GET:
            asana_id = request.GET.get('asana_id')
            print(asana_id)
            asana = Asana.objects.get(id=asana_id, tenant=tenant)
            form = AsanaCreationForm(instance=asana)
            sweetify.success(request, "Choose type of PO", button="OK")
            return render(request, "users/update_asana.html", {
                'form': form,
                'asana_id': asana_id,
                'is_trainer': True,
                'tenant':tenant
            })

        else:
            formset = AsanaCreationFormSet()
            return render(request, "users/create_asana.html", {
                'formset': formset,
                'is_trainer': True,
                'enable': True,
                'tenant':tenant
            })

    def post(self, request, *args, **kwargs):
        tenant = request.tenant  # Assuming tenant is set in middleware
        max_forms, no_of_asanas_created_by_trainee = self.get_max_forms(request)
        AsanaCreationFormSet = formset_factory(AsanaCreationForm, extra=1, max_num=max_forms, validate_max=True, absolute_max=max_forms)
        created_asanas_by_trainer = TrainerLogDetail.objects.get(trainer_name=request.user, tenant=tenant)
        remaining_forms = max_forms - no_of_asanas_created_by_trainee

        if 'update_asana' in request.POST:
            asana_id = request.POST.get('asana_id')
            asana = Asana.objects.get(id=asana_id, tenant=tenant)
            form = AsanaCreationForm(request.POST, instance=asana)
            if form.is_valid():
                form.save()
                return redirect("view-trained")
            else:
                return render(request, "users/update_asana.html", {
                    'form': form,
                    'asana_id': asana_id,
                    'is_trainer': True,
                    'tenant':tenant
                })

        elif 'delete_asana' in request.POST:
            asana_id = request.POST.get('asana_id')
            asana = get_object_or_404(Asana, id=asana_id, tenant=tenant)
            
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
                        asana.tenant = tenant  # Ensure the tenant is set for the asana
                        asana.created_at = timezone.now()
                        asana.last_modified_at = timezone.now()
                        print("asssssssssssssssssssssssssss ")
                        asana.save()

                        created_asanas_by_trainer.no_of_asanas_created += 1
                        created_asanas_by_trainer.created_at = timezone.now()
                        created_asanas_by_trainer.updated_at = timezone.now()
                        created_asanas_by_trainer.save()

                        for i in range(1, asana.no_of_postures + 1):
                            Posture.objects.create(name=f"Step-{i}", asana=asana, step_no=i, tenant=tenant)

                        no_of_asanas_created_by_trainee += 1
                        remaining_forms -= 1
                        print(remaining_forms, "lllllllllllllllllllllllllllllllllllllllllllll")
                    return redirect("view-trained")
            else:
                return render(request, "users/create_asana.html", {
                    'formset': formset,
                    'is_trainer': True,
                    'tenant':tenant
                })


class CourseCreationView(UserPassesTestMixin, View):

    def test_func(self):
        return check_trainer(self.request.user)

    def get(self, request,slug, *args, **kwargs):
        tenant = Tenant.objects.get(slug=slug)  # Assuming tenant is set in middleware
        course_id = kwargs.get('course_id')
        current_user = self.request.user
        
        print(course_id, "line 594x")
        if course_id:
            course = get_object_or_404(CourseDetails, id=course_id, tenant=tenant)
            form = CourseCreationForm(instance=course, user=self.request.user)
            return render(request, "users/update_course.html", {
                'form': form,
                'course_id': course_id,
                'is_trainer': True,
                'tenant':tenant
            })
        else:
            form = CourseCreationForm(user=self.request.user)
            courses = CourseDetails.objects.filter(user=current_user, tenant=tenant)
            return render(request, "users/trainer_dashboard.html", {
                'form': form,
                'is_trainer': True,
                'courses': courses,
                
                'tenant':tenant
            })

    def post(self, request, slug,*args, **kwargs):
        tenant = Tenant.objects.get(slug=slug) # Assuming tenant is set in middleware
        course_id = request.POST.get('course_id')
        print(course_id, "line 614")
        current_user = self.request.user
        
        if 'update_course' in request.POST:
            course = get_object_or_404(CourseDetails, id=course_id, tenant=tenant)
            form = CourseCreationForm(request.POST, instance=course, user=self.request.user)
            print("line 620")
            if form.is_valid():
                form.save()
                return redirect('view-trained')
            else:
                return render(request, "users/update_course.html", {
                    'form': form,
                    'course_id': course_id,
                    'is_trainer': True,
                    
                'tenant':tenant
                })

        elif 'delete_course' in request.POST:
            course = get_object_or_404(CourseDetails, id=course_id, tenant=tenant)
            course.delete()
            return render(request, 'users/trainer_dashboard.html')

        else:
            form = CourseCreationForm(request.POST, user=self.request.user)
            if form.is_valid():
                course = form.save(commit=False)
                course.user = request.user
                course.tenant = tenant  # Set the tenant for the course
                course.created_at = timezone.now()
                course.updated_at = timezone.now()
                course.save()  # Save the instance to the database
                form.save_m2m()  # Save many-to-many data

                return render(request, 'users/trainer_dashboard.html')
            else:
                return render(request, "users/trainer_dashboard.html", {
                    'form': form,
                    'is_trainer': True,
                    
                'tenant':tenant
                })


# @user_passes_test(check_student)
def home(request, slug=None):
    if slug:
        tenant = get_object_or_404(Tenant, slug=slug)
        # Fetch subscriptions if tenant exists
        subscriptions = Subscription.objects.filter(tenant=tenant)
        return render(request, "users/home.html", {'subscriptions': subscriptions, 'tenant': tenant})
    else:
        # Render the normal home page if no slug is provided or tenant does not exist
        return render(request, "users/home.html")
@login_required
@user_passes_test(check_student)
def staff_dashboard_function(request):
    user = request.user
    tenant = request.tenant  # Assuming tenant is set in middleware

    if user.groups.filter(name='Trainer').exists() or user.is_superuser:
        is_trainer = True
    else:
        is_trainer = False

    context = {
        'is_trainer': is_trainer,
    }
    
    return render(request, "users/staff_dashboard.html", context)



@login_required
@user_passes_test(check_trainer)
def edit_posture(request, posture_id):
    tenant = request.tenant  # Assuming tenant is set in middleware
    posture = get_object_or_404(Posture, id=posture_id, asana__tenant=tenant)
    
    if request.method == "POST":
        if "meta_details" in request.POST:
            form = EditPostureForm(request.POST, instance=posture)
            if form.is_valid():
                form.save()
        else:
            name = f"{posture.asana.name}_{posture.step_no}.csv"
            dataset = ast.literal_eval(request.POST["dataset"])
            dataset = pd.DataFrame(dataset)
            dataset = dataset.transpose()
            dataset.to_csv(f'./media/{name}', index=False, header=False)
            posture.dataset.name = name
            decoded_data = base64.b64decode(request.POST['snapshot'])
            with open(f"./media/images/{posture_id}.png", 'wb') as img_file:
                img_file.write(decoded_data)
            posture.snap_shot.name = f"./images/{posture_id}.png"
            posture.save()

    form = EditPostureForm(instance=posture)
    return render(request, "users/edit_posture.html", {
        "form": form,
        "posture": posture,
        'is_trainer': True,
    })







class StudentCourseMapView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return check_trainer(self.request.user)
    
    def get_enrollment_details(self, user):
        tenant = self.request.tenant  # Assuming tenant is set in middleware
        trainer_details = TrainerLogDetail.objects.filter(trainer_name=user, tenant=tenant).first()
        if trainer_details:
            client_name = trainer_details.onboarded_by
            enrolled_studs = list(StudentLogDetail.objects.filter(added_by=client_name, tenant=tenant))
            if enrolled_studs:
                student_names = [student.student_name for student in enrolled_studs]
                students = User.objects.filter(username__in=student_names)
                enrollment_details = EnrollmentDetails.objects.filter(user__in=students, tenant=tenant)
                return enrollment_details
        return EnrollmentDetails.objects.none()  # Return an empty queryset if no students found

    def get(self, request, *args, **kwargs):
        enrollment_details = self.get_enrollment_details(request.user)
        enrollment_id = request.GET.get('enrollment_id')
        
        if enrollment_id:
            enrollment = get_object_or_404(EnrollmentDetails, id=enrollment_id, tenant=request.tenant)
            form = StudentCourseMappingForm(instance=enrollment, user=self.request.user)
            return render(request, "users/update_student_course_form.html", {
                'form': form,
                'enrollment_id': enrollment_id,
            })
        else:
            form = StudentCourseMappingForm(user=self.request.user)
            return render(request, "users/student_mapping.html", {
                'form': form,
                'enrollment_details': enrollment_details,
            })
    
    def post(self, request, *args, **kwargs):
        tenant = request.tenant  # Assuming tenant is set in middleware
        enrollment_id = request.POST.get('enrollment_id')
        enrollment_details = self.get_enrollment_details(request.user)
        
        if 'update_course_map_form' in request.POST and enrollment_id:
            enrollment = get_object_or_404(EnrollmentDetails, id=enrollment_id, tenant=tenant)
            form = StudentCourseMappingForm(request.POST, instance=enrollment, user=request.user)
            if form.is_valid():
                form.save()
                return render(request, "users/update_student_course_form.html", {
                    'form': form,
                    'enrollment_id': enrollment_id,
                })
            else:
                return render(request, "users/student_mapping.html", {
                    'form': form,
                    'enrollment_details': enrollment_details,
                    'enrollment_id': enrollment_id,
                })

        elif 'delete_course_map_form' in request.POST and enrollment_id:
            enrollment = get_object_or_404(EnrollmentDetails, id=enrollment_id, tenant=tenant)
            enrollment.delete()
            return render(request, 'users/student_mapping.html')

        else:
            form = StudentCourseMappingForm(request.POST, user=request.user)
            if form.is_valid():
                enrollment = form.save(commit=False)
                enrollment.created_at = timezone.now()
                enrollment.updated_at = timezone.now()
                enrollment.tenant = tenant  # Set the tenant for the enrollment
                enrollment.save()
                form.save_m2m()
                return render(request, "users/student_mapping.html", {
                    'form': form,
                    'enrollment_details': enrollment_details,
                    'enrollment_id': enrollment_id,
                })
            else:
                return render(request, "users/trainer_dashboard.html", {
                    'form': form,
                    'enrollment_id': enrollment_id,
                })





@login_required
@user_passes_test(check_student)
def user_view_asana(request,slug):
    tenant = Tenant.objects.get(slug=slug)  
    print(tenant,"line 781")# Assuming tenant is set in middleware
    current_user = request.user

    enrolled_student_to_courses = EnrollmentDetails.objects.filter(user=current_user, tenant=tenant)
    trainer_asanas = []
    if enrolled_student_to_courses.exists():
        all_courses = []
        for enrollment in enrolled_student_to_courses:
            all_courses.extend(enrollment.students_added_to_courses.all())

        for course in all_courses:
            trainer = course.user
            if trainer:
                asanas = CourseDetails.objects.filter(user=trainer, tenant=tenant)
                trainer_asanas.extend(asanas)
    return render(request, "users/user_view_asana.html", {
        "trainer_asanas": trainer_asanas,
        "tenant":tenant
    })


@login_required
@user_passes_test(check_student)
def user_view_posture(request, asana_id):
    tenant = request.tenant  # Assuming tenant is set in middleware
    try:
        asana = get_object_or_404(Asana, id=asana_id, tenant=tenant)
        postures = Posture.objects.filter(asana=asana).order_by('step_no')
        return render(request, "users/user_view_posture.html", {
            "postures": postures,
            'is_trainer': True,
        })
    except Exception as e:
        capture_exception(e)    
        return JsonResponse({"error": "An error occurred"}, safe=False)




@login_required
@user_passes_test(check_student)
def get_posture(request, posture_id):
    if request.method == "GET":
        tenant = request.tenant  # Assuming tenant is set in middleware
        posture = get_object_or_404(Posture, id=posture_id, asana__tenant=tenant)
        link = str(posture.snap_shot.url)
        return JsonResponse({"url": link})
    else:
        return JsonResponse({"error": "expected GET method"})





@login_required
@user_passes_test(check_student)
def get_posture_dataset(request):
    if request.method == "GET":
        tenant = request.tenant  # Assuming tenant is set in middleware
        posture_id = request.GET.get('posture_id')
        posture = get_object_or_404(Posture, id=posture_id, asana__tenant=tenant)
        dataset = pd.read_csv(posture.dataset.path, header=None)
        dataset = dataset.values.tolist()
        data = {
            "dataset": dataset,
            "snapshot": posture.snap_shot.url
        }
        return JsonResponse(data)
    else:
        return JsonResponse(status=400, data={"error": "Bad request"})


# @login_required
# @user_passes_test(check_client)
# def subscription_plans(request):
#     subscriptions= Subscription.objects.all()
#     return render(request,'users/subscription_plans.html',{'subscriptions':subscriptions}) 






























def client_list(request):
    # Fetch all orders with related subscriptions
    orders = Order.objects.select_related('subscription').all()
    
    # Fetch all onboarding data
    onboarding_data = ClientOnboarding.objects.all()
    print(onboarding_data,"line 986")
    
    # Create a dictionary for easy lookup by client ID
    onboarding_dict = {onboarding.client.id: onboarding for onboarding in onboarding_data}
    print(onboarding_dict,"line 990")
    
    return render(request, 'users/client_list.html', {
        'orders': orders,
        'onboarding_dict': onboarding_dict
    })

# def delete_client(request, order_id):
#     order = get_object_or_404(Order, id=order_id)
#     if request.method == 'POST':
#         subscription = order.subscription
#         order.delete()
#         if not Order.objects.filter(subscription=subscription).exists():
#             subscription.delete()
#         return redirect('client_list')
#     return render(request, 'users/confirm_delete.html', {'order': order})


def delete_client(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        # Retrieve the associated client
        client = order.subscription.client
        print(client,"line 1014")
        # Delete the user
        client.delete()
        return redirect('client_list')
    return render(request, 'users/confirm_delete.html', {'order': order})








@login_required
def register_organisation(request):
    if request.method == 'POST':
        form = OrganisationForm(request.POST)
        if form.is_valid():
            form.save()  # Save the form data to the Tenant model
            print("Form is valid. Redirecting to login.")
            return redirect(reverse('login'))  # Ensure 'login' matches your URL pattern name
        else:
            print("Form is invalid. Errors:", form.errors)
    else:
        form = OrganisationForm()

    return render(request, 'users/register_organization.html', {'form': form})




# def tenant_data(request,slug):
#     tenant = getattr(request, 'tenant', None)
#     if tenant:
#         tenant = Tenant.objects.get(slug=slug)
#         asanas=Asana.objects.get(tenant=tenant)
#         subscriptions = EnrollmentDetails.objects.filter(tenant=tenant)
#         other_models = CourseDetails.objects.filter(tenant=tenant)

#         data = (f"Tenants: {tenant.client_name}\n"
#                 f"Asanas: {asanas.name}\n"
#                 f"Subscriptions: {subscriptions.count()}\n"
#                 f"Other Models: {other_models.count()}")

#         return HttpResponse(data)
#     return HttpResponse("Tenant not found")
