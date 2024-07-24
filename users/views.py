import json
from django.views.decorators.csrf import csrf_exempt
from django.forms import formset_factory
from pyexpat.errors import messages
from django.contrib.auth.models import Group
from django.conf import settings
from django.shortcuts import render,redirect
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
import razorpay
import pandas as pd
import base64
from django.shortcuts import render
from openpyxl import load_workbook

from django.dispatch import receiver
from .models import Activity





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

def subscription_payment(request):
    if request.method == "POST":
        name = request.POST.get("name")
        subscription_id = request.POST.get("subscription_id")
        subscription = Subscription.objects.get(id=subscription_id)
        amount = subscription.price
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        razorpay_order = client.order.create(
            {"amount": int(amount) , "currency": "INR", "payment_capture": "1"}
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
            user= request.user
            transaction = Order.objects.filter(name=user, status='ACCEPT').first() 
            if transaction:
                subscription = transaction.subscription
                no_of_persons_onboard_by_client =subscription.no_of_persons_onboard
                print(no_of_persons_onboard_by_client,"line 157")
            else:
                print("No transaction found")
            
            # Fetch the uploaded file
            new_persons = request.FILES.get('excel_file')

            
            df = pd.read_excel(new_persons,nrows=no_of_persons_onboard_by_client, engine='openpyxl')
            print(df)

            success_count=0
            error_count=0
            
            for i,row in df.iterrows():
                user,created=User.objects.get_or_create(
                    username=row['username'],
                    defaults={
                          'email':row['email'],
                          'first_name':row['first_name'],
                          'last_name':row['last_name'],
                          'password':row['password']

                    }
                   
                   
                )
                if created:
                    print("created sucessfully",user.username)
                
                    role = row['roles'].lower()
                    password = row['password']
                    print(password)
                   
                    if role:
                          group, created = Group.objects.get_or_create(name=role.capitalize())
                          user.groups.add(group)
                          print(f"Added {user.username} to group {group.name}")
                    user.set_password(password)
                    user.save()    
                    success_count+=1
                    
                else:
                    print("user not createsd")
                error_count=+0
            messages.success(request, ' users uploaded successfully.')
            if error_count > 0:
                messages.error(request, 'rows could not be processed.')
                
               
                return render(request, 'users/home.html')
        return render(request,'users/Trainer_approval_Page.html')

                     
    except Exception as e:
        print(f"An error occurred: {e}")
       
        return render(request, 'users/staff_dashboard.html')

                

              
                
                




@login_required
def profile_view(request):
    return render(request,'users/profile.html',{'user': request.user})

@login_required
@user_passes_test(check_trainer )
def Trainer_dashboard(request):
    try: 
        trainer = CourseDetails.objects.get(user=request.user)

      
        
        return render(request, "users/trainer_dashboard.html")
    except CourseDetails.DoesNotExist:
        print("Trainer does not exist")
        return HttpResponse("Trainer details not found", status=404)  
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return HttpResponse("An unexpected error occurred", status=500)



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


@login_required
@user_passes_test(lambda u: check_trainer(u) or check_client(u))
def create_asana(request):
    form_count = 0
    max_forms = 0
  
    try:
        trainee_name = request.user
        client_for_trainer = CourseDetails.objects.filter(user=trainee_name)
        
        if client_for_trainer.exists():
            client = client_for_trainer.first().added_by
            print(f"Client found: {client}")

            # Check if there is a successful transaction for the client
            transaction = Order.objects.filter(name=client, status='ACCEPT').first()
            
            if transaction:
                subscription = transaction.subscription
                print(subscription,"hhhhhhhhhhhhhhhhhhhhhhhh")
                max_forms = subscription.permitted_asanas
                print(f"Subscription found: {subscription}, Max forms allowed: {max_forms}")
            else:
                print("No valid transaction found for the client.")
        else:
            print("No client for trainer found.")

    except Exception as e:
        print(f"Exception occurred: {e}")
    

    if max_forms <= 0:
        max_forms = 1  

    # Create the formset factory with the correct max_num and extra
    AsanaCreationFormSet = formset_factory(AsanaCreationForm, extra=max_forms, max_num=max_forms, validate_max=True, absolute_max=max_forms)
    print(max_forms)
 
    if request.method == "POST":
        print("moved inside if condition")
        formset = AsanaCreationFormSet(request.POST)
        print("hello")
        if formset.is_valid():
            form_count = 0
            max_forms_create = max_forms
            for form in formset:
                if form_count < max_forms:
                    try:
                        asana = form.save(commit=False)
                        asana.created_by = request.user
                        asana.created_at = timezone.now()
                        asana.last_modified_at = timezone.now()
                        asana.save()

                        
                       
                        
                        # Create postures
                        for i in range(1, asana.no_of_postures + 1):
                            Posture.objects.create(name=f"Step-{i}", asana=asana, step_no=i)
                        max_forms_create -= 1
                        form_count += 1
                    
                    except Exception as e:
                        print(f"Error while processing form: {e}")

            print(f"Total forms created: {form_count}")

            return redirect("view-trained")
        else:
            print("Formset is not valid")
            print(formset.errors)  # Print formset errors for debugging

    else:
        formset = AsanaCreationFormSet()

    return render(request, "users/create_asana.html", {
        'formset': formset, 
        'is_trainer': True,
    })


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
@user_passes_test(check_student)
def user_view_asana(request):
    asanas = Asana.objects.all()
    print(asanas)
    trained_asanas = []
    print(trained_asanas)
    current_user = request.user
    
    
        
    print(current_user)
    for asana in asanas:
        if asana.related_postures.filter(dataset="").exists():
            pass
        else:
            if current_user == asana.created_by:
                trained_asanas.append(asana)
           
            
       
    return render(request,"users/user_view_asana.html",{
        "asanas":asanas,
        'is_trainer': True,

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

    context = {
        'activities': Activity.objects.filter(user=user).order_by('-timestamp'),
        'user_groups': user_groups,
     
    }

    if 'Client' in user_groups:
        context.update({
            'created_asana': Asana.objects.filter(created_by=user).count(),
            'uploaded_file': Activity.objects.filter(activity_type='Uploaded Excel File').count(),
        })
        
        return render(request, 'users/activity_log_users.html', context)

    elif 'Trainer' in user_groups:
        context.update({
            'created_asana': Asana.objects.filter(created_by=user).count(),
            'edited_posture': Activity.objects.filter(activity_type='Edited asana').count(),
            
        })
        
        return render(request, 'users/activity_log_users.html', context)

    elif 'Student' in user_groups:
        context.update({
            'viewed_asana': Activity.objects.filter(activity_type='view_trained').count(),
            'viewed_posture': Activity.objects.filter(activity_type='view_posture').count(),
           
        })
       
        return render(request, 'users/activity_log_users.html', context)

    else:
        return render(request, 'users/activity_log_users.html', context)