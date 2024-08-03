from decimal import Decimal
import json


from django.views import View
# from bulkmodel.models import BulkModel
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
from django.db import transaction
import razorpay
import pandas as pd
import base64
from django.shortcuts import render
from openpyxl import load_workbook

from django.dispatch import receiver
from .models import Activity
from .utils import  calculate_asana_overall_accuracy, calculate_user_overall_accuracy
from django.views.decorators.http import require_http_methods




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
            except CouponCodeForNegeotiation.DoesNotExist:
               print("no coupon found")
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
                'order':order
            }
            
            print("SUCCESS")
            return render(request, "users/success.html",context)
        else:
            order.status = 'REJECT'
            order.save()
            print("FAILURE: Signature verification failed.")
            return render(request, "users/failed.html", context={'order':order})
    else:
        try:
            payment_id = json.loads(request.POST.get("error[metadata]")).get("payment_id")
            provider_order_id = json.loads(request.POST.get("error[metadata]")).get("order_id")
        except (TypeError, json.JSONDecodeError, AttributeError) as e:
            print(f"Error parsing error metadata: {e}")
            return render(request, "users/callback.html", context={"status": 'REJECT'})

        order = Order.objects.get(provider_order_id=provider_order_id)
        order.payment_id = payment_id
        order.status = 'REJECT'
        order.save()
        print("FAILURE: Error in payment process.")
        return render(request, "users/callback.html", context={"status": order.status})




@login_required
@user_passes_test(check_client)
def Trainer_approval_function(request):
    try:
        if request.method == 'POST':
            admin_user = request.user
            order_transaction = Order.objects.filter(name=admin_user, status='ACCEPT').first()
            
            if not order_transaction:
                print("No transaction found")
                return render(request, 'users/Trainer_approval_Page.html')

            subscription = order_transaction.subscription
            no_of_persons_onboard_by_client = subscription.no_of_persons_onboard

            new_persons = request.FILES.get('excel_file')
            df = pd.read_excel(new_persons, nrows=no_of_persons_onboard_by_client, engine='openpyxl')

            success_count = 0
            error_count = 0
            user_objs = []
            role_dict = {}

            with transaction.atomic():
                for i, row in df.iterrows():
                    username = row['username']
                    email = row['email']
                    first_name = row['first_name']
                    last_name = row['last_name']
                    password = row['password']
                    role = row['roles'].lower()

                    user = User(
                        username=username,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                    )
                    user.set_password(password)
                    user_objs.append(user)
                    role_dict[username] = role

                User.objects.bulk_create(user_objs)

                for user in user_objs:
                    role = role_dict[user.username]
                    group, created = Group.objects.get_or_create(name=role.capitalize())
                    user.groups.add(group)
                    print(f"Added {user.username} to group {group.name}")

                    if role == 'trainer':
                        TrainerLogDetail.objects.create(
                            trainer_name=user,
                            onboarded_by=admin_user,
                            no_of_asanas_created=0,
                            created_at=timezone.now(),
                            updated_at=timezone.now()
                        )
                    else:
                        EnrollmentDetails.objects.create(
                            user=user,
                            added_by=admin_user,
                            student_status='ACCEPT',
                            created_at=timezone.now(),
                            updated_at=timezone.now()
                        )
                    success_count += 1

            # messages.success(request, f'Successfully created {success_count} users.')
            return render(request, 'users/Trainer_approval_Page.html')
        else:
            return render(request, 'users/Trainer_approval_Page.html')

    except Exception as e:
        print(e)
        #       messages.error(request, 'An error occurred while processing the file.')
        return render(request, 'users/staff_dashboard.html')
       
       
                
@login_required
@user_passes_test(check_client)
def student_mapped_to_courses(request):
    print("hello")
    admin_user=request.user
    print(admin_user)
    if admin_user:
       order_transaction = Order.objects.filter(name=admin_user,status='ACCEPT').first()
       print(order_transaction)
       if not order_transaction:
            print("trainaction not found")
            # sweeetify alert
            return render(request,'users/Trainer_approval_Page.html')

    if request.method == 'POST':
        
        form = StudentCourseMappingForm(request.POST,user=request.user)
    
        if form.is_valid():
            student_user = form.cleaned_data['user']
            print(student_user)
            courses_to_be_mapped = form.cleaned_data['students_added_to_courses']
            try:
                print("entered line 232")
            
                enrollment= EnrollmentDetails.objects.get(user=student_user)
                print(enrollment)
            except:
                enrollment = EnrollmentDetails(user=student_user)
                enrollment.save()
            print("successfully saved ")
            enrollment.students_added_to_courses.set(courses_to_be_mapped)

           
            
            # Save the EnrollmentDetails object
            enrollment.save()
            

          
            # messages.success(request, "Courses mapped to student successfully")
        return render(request,'users/trainer_dashboard.html',{
            'forms': forms,
              
            
        })  

            
            
           
            
            
    else:
        form = StudentCourseMappingForm()
    
    return render(request, 'users/student_mapping.html',{'form':form})
    
              
                
                




@login_required
def profile_view(request):
    return render(request,'users/profile.html',{'user': request.user})


# class CourseCreationView(LoginRequiredMixin, UserPassesTestMixin, View):
#     def test_func(self):
#         return check_trainer(self.request.user) or check_client(self.request.user)
#     def get(self,request,*args,**kwargs):
#         current_user=self.request.user
#         print(current_user)
#         form =CourseCreationForm
#         if 'update' in request.GET:
#             course_id=request.GET.get('course_id')
#             course=CourseDetails.get(id=course_id)
#             form=CourseCreationForm(instance=course)
#             return render(request, "users/update_course.html", {
#                 'form': form,
#                 'course_id':course_id ,
#                 'is_trainer': True,
#             })
#         else:
#             form =CourseCreationForm()
#             return render(request, "users/create_asana.html", {
#                 'form': form,
#                 'is_trainer': True,
#             })
#     def post(self, request, *args, **kwargs):
#         form =CourseCreationForm
#         if 'update_course' in request.POST:
#             course_id=request.POST.get('course_id')
#             course=CourseDetails.get(id=course_id)
#             form=CourseCreationForm(instance=course)
#             if form.is_valid():
#                 form.save()
#                 return redirect("view-trained")
#             else:
#                  return render(request, "users/update_asana.html", {
#                     'form': form,
#                     'course_id': course_id,
#                     'is_trainer': True,
#                 })
#         elif 'delete_asana' in request.POST:
#             course_id=request.POST.get('course_id')
#             course=CourseDetails.get(id=course_id)
#             course.delete()
#         else:
#             form =CourseCreationForm(request.POST)
#             if form.is_valid():
#                 course=form.save(commit=False)
#                 course = form.save(commit=False)  # Create the instance but don't save it yet
#                 course.user = request.user  # Set the user field
#                 course.created_at = timezone.now()  # Set the created_at field
#                 course.updated_at = timezone.now()  # Set the updated_at field
#                 course.save()  # Save the instance to the database
#                 form.save_m2m()  # Save the many-to-many data
#                 return redirect('view-trained')
#             else:
#                 return render(request, "users/trainer_dashboard.html")


           


class CourseCreationView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return check_trainer(self.request.user) or check_client(self.request.user)

    def get(self, request, *args, **kwargs):
        current_user=self.request.user
        course_id = request.GET.get('course_id')
        if course_id:
            course = get_object_or_404(CourseDetails, id=course_id)
           
            
            form = CourseCreationForm(instance=course,user=self.request.user)
            return render(request, "users/update_course.html", {
                'form': form,
                'course_id': course_id,
                'is_trainer': True,
            })
        else:
            form = CourseCreationForm(user=self.request.user)
            courses=CourseDetails.objects.filter(user=current_user)

            return render(request, "users/trainer_dashboard.html", {
                'form': form,
                'is_trainer': True,
                'courses':courses,
            })

    def post(self, request, *args, **kwargs):
        course_id = request.POST.get('course_id')
        current_user=self.request.user
        if 'update_course' in request.POST:
            course = get_object_or_404(CourseDetails, id=course_id)
            form = CourseCreationForm(request.POST, instance=course,user=self.request.user)
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
            form = CourseCreationForm(request.POST,user=self.request.user)
            if form.is_valid():
                course = form.save(commit=False)
                course.user = request.user
                course.created_at = timezone.now()
                course.updated_at = timezone.now()
                course.save()  # Save the instance to the database
                form.save_m2m()  # Save many-to-many data
                return redirect('view-trained')
            else:
                return render(request, "users/create_course.html", {
                    'form': form,
                    'is_trainer': True,
                })






    

                
            


  


def user_login(request):
    if request.method == "POST":
        
        email = request.POST.get("email")
        password = request.POST.get("password")
        User_obj = User.objects.get(email=email)
        user = auth.authenticate(username=User_obj.username,password=password)
        if user is not None :
            login(request,user)
            for group in request.user.groups.all() :
                if group.name == 'Trainer' or group.name == 'Student' or group.name == 'Client':
                    return redirect("staff_dashboard")
            return redirect("home")

    return render(request,"users/login.html")

@login_required

@user_passes_test(check_trainer or check_client)
def view_trained(request):
    trained_asanas = Asana.objects.filter(created_by = request.user)
   
    return render(request,"users/view_trained.html",{
        "trained_asanas":trained_asanas,
        'is_trainer': True,

    })


@login_required

@user_passes_test(check_trainer  or check_client)
def view_posture(request,asana_id):
    postures = Posture.objects.filter(asana=Asana.objects.get(id=asana_id)).order_by('step_no')
   
    return render(request,"users/view_posture.html",{
        "postures":postures,
        'is_trainer': True,
        
    })


class CreateAsanaView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return check_trainer(self.request.user) or check_client(self.request.user)

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
            max_forms = 1
            no_of_asanas_created_by_trainee = 0

        return max_forms, no_of_asanas_created_by_trainee

    def get(self, request, *args, **kwargs):
        max_forms, no_of_asanas_created_by_trainee = self.get_max_forms(request.user)
        print(max_forms)
        
        AsanaCreationFormSet = formset_factory(AsanaCreationForm, extra=1, max_num=max_forms, validate_max=True, absolute_max=max_forms)

        if 'update' in request.GET:
            asana_id = request.GET.get('asana_id')
            asana = Asana.objects.get(id=asana_id)
            form = AsanaCreationForm(instance=asana)
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
            })

    def post(self, request, *args, **kwargs):
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
            asana = Asana.objects.get(id=asana_id)
            asana.delete()
            created_asanas_by_trainer.no_of_asanas_created -= 1
            created_asanas_by_trainer.save()
            return redirect("view-trained")

        else:
            formset = AsanaCreationFormSet(request.POST)
            if formset.is_valid():
                for form in formset:
                    if remaining_forms > 0:
                        
                        asana = form.save(commit=False)
                        asana.created_by = request.user
                        asana.created_at = timezone.now()
                        asana.last_modified_at = timezone.now()
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
                return redirect("view-trained")
            else:
                return render(request, "users/create_asana.html", {
                    'formset': formset,
                    'is_trainer': True,
                })
   


                
            





def record_accuracy(request):
    if request.method == 'GET':
        print("entered record_accuracy function")
        try:
            print("started to load the data")
            data = json.loads(request.body)
            print(data)
            posture_id = data.get('posture_id')
            print(posture_id)
            accuracy = data.get('accuracy_for_posture')
            print(accuracy)
            try:
                accuracy_values = []
                posture_id_get_asana=Posture.objects.filter(id=posture_id)
                asana_name=posture_id_get_asana.asana
            
                accuracy_values.append(accuracy)
                print(accuracy, "data")
                print(accuracy_values, "values")
                if 'accuracy_values' not in request.session:
                     request.session['accuracy_values']=[]
                     request.session['accuracy_values'].append(accuracy)
                     request.session.modified=True
                     response_data = {'status': 'success', 'message': 'Accuracy recorded'}
                     return JsonResponse(response_data,safe=False)
            except:
                return JsonResponse("error",safe=False)
        except json.JSONDecodeError:
                    return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    else:
            return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)  



@csrf_exempt
def finalize_accuracy(request):
    if request.method == 'POST':
        try:
            if 'accuracy_values' not in request.session or not request.session['accuracy_values']:
                return JsonResponse({'status': 'error', 'message': 'No accuracy values to finalize'}, status=400)
            accuracy_values = request.session.pop('accuracy_values')
            average_accuracy = sum(accuracy_values) / len(accuracy_values)
            data = json.loads(request.body)
            posture_id = data.get('posture_id')
            user = request.user
            posture_id_get_asana=Posture.objects.filter(id=posture_id)
            asana_name=posture_id_get_asana.asana
            PostureAccuracy.objects.create(
                asana_for_accuracy=asana_name,
                accuracy=average_accuracy,
                user=user,
                recorded_at=timezone.now()
            )

            response_data = {
                'status': 'success',
                'average_accuracy': average_accuracy,
                'message': 'Accuracy finalized and stored'
            }
            return JsonResponse(response_data)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


            
    #         if accuracy_values:
    #                 print("entered accuracy calculation")
    #                 average_accuracy = sum(accuracy_values) / len(accuracy_values)
    #                 get_posture_id = get_object_or_404(Posture, id=posture_id)
    #                 asana=get_posture_id.asana
    #                 print("asana",asana)
    #                 user = request.user
    #                 print(user)
                    
    #                 with transaction.atomic():# Create or update the PostureAccuracy object
    #                           PostureAccuracy.objects.update_or_create(
    #                                 asana_for_accuracy=asana_name,
    #                                 user_to_calculate=user,
    #                                 accuracy=average_accuracy,
    #                                 recorded_at=timezone.now()
                       
    #                 )

    #                 asana_overall_accuracy = calculate_asana_overall_accuracy(asana)
    #                 user_overall_accuracy = calculate_user_overall_accuracy(user)

    #                 context = {
    #                     'status': 'success',
    #                     'accuracy_for_posture': average_accuracy,
    #                     'asana_overall_accuracy':  asana_overall_accuracy,
    #                     'user_overall_accuracy':user_overall_accuracy
    #                 }
    #                 return render(request,'users/accuracy.html',context)
    #         else:
    #                 return JsonResponse({'status': 'error', 'message': 'No accuracy values provided'}, status=400)
           
    #     except json.JSONDecodeError:
    #         return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    # else:
    #     return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)





@login_required
# @user_passes_test(check_student)
def home(request):
    return render(request,"users/home.html")

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

@login_required
def Add_Student(request):
    # here i need to map the student with particular course 
    # he can see only that asana 



    return render(request,"add_student.html")
   


@login_required
@user_passes_test(check_student)
def user_view_asana(request):
    asanas = Asana.objects.all()
    current_user = request.user
    print(current_user, "firstly get instance user")
    try:
                enrollment= EnrollmentDetails.objects.get(user=current_user)
                print("it does not  returned 2 obj")
    except:
                enrollment = EnrollmentDetails(user=current_user)
                enrollment.save()
                
   
    
    
    courses=enrollment.students_added_to_courses.all()
    print(courses)
    trainer_asanas = []
    print("hello world ")
    
    # Loop through each course to find the associated trainer and their asanas
    for course in courses:
        print("for loop for find the trainer")
        # Assuming that `trainer` is a ForeignKey in CourseDetails to the User model
        trainer = course.user
        print(trainer)
         # Modify based on your actual model relationship
        
        if trainer:
            # Fetch asanas associated with the trainer
            asanas = Asana.objects.filter(created_by=trainer)
            print(asanas)
            trainer_asanas.extend(asanas)
            print(trainer_asanas)
    return render(request, "users/user_view_asana.html", {
        
            "trainer_asanas": trainer_asanas,
            
        })


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
    except:
        return JsonResponse("Eroor")






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
    

@login_required
@user_passes_test(check_client)
def subscription_plans(request):
    subscriptions= Subscription.objects.all()
    return render(request,'users/subscription_plans.html',{'subscriptions':subscriptions}) 

           
  
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
    



