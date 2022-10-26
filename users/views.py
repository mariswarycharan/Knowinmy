from django.shortcuts import render,redirect
from django.http import JsonResponse
from datetime import datetime
from django.contrib.auth.models import User
from yoga.settings import BASE_DIR, MEDIA_ROOT
from .models import *
from .forms import *
from django.contrib.auth import authenticate,login
from django.utils import timezone
from django.contrib.auth.decorators import login_required,user_passes_test
from .permissions import *
import ast
import pandas as pd
import base64


def register(request):
    if request.method == "POST":
        email = request.POST.get("email")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        password = request.POST.get("password")
        User.objects.create_user(username=email,email=email,first_name=first_name,last_name=last_name,password=password)
        return redirect ('login')
    return render(request , "users/user_register.html")


def user_login(request):
    if request.method == "POST":
        username = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(username=username,password=password)
        if user is not None:
            login(request,user)
            return redirect("home")
    return render(request,"users/login.html")


@login_required
@user_passes_test(check_trainer)
def view_trained(request):
    trained_asanas = Asana.objects.filter(created_by = request.user)
    return render(request,"users/view_trained.html",{
        "trained_asanas":trained_asanas,
    })


@login_required
@user_passes_test(check_trainer)
def view_posture(request,asana_id):
    postures = Posture.objects.filter(asana=Asana.objects.get(id=asana_id)).order_by('step_no')
    return render(request,"users/view_posture.html",{
        "postures":postures,
    })


@login_required
@user_passes_test(check_trainer)
def create_asana(request):
    form = AsanaCreationForm()
    if request.method == "POST":
        form = AsanaCreationForm(request.POST)
        if form.is_valid():
            asana = form.save(commit=False)
            asana.created_by = request.user
            asana.created_at = datetime.now(tz=timezone.utc)
            asana.last_modified_at = datetime.now(tz=timezone.utc)
            asana.save()
            for i in range(1,asana.no_of_postures+1):
                Posture.objects.create(name=f"Step-{i}",asana=asana,step_no=i)
            return redirect("view-trained")
    return render(request,"users/create_asana.html",{
        'form':form,
    })


@login_required
@user_passes_test(check_student)
def home(request):
    return render(request,"users/home.html")


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
    form = EditPostureForm(instance=posture)
    return render(request, "users/edit_posture.html",{
        "form":form,
        "posture":posture,
    })


#model testing user side
@login_required
@user_passes_test(check_student)
def user_view_asana(request):
    asanas = Asana.objects.all()
    trained_asanas = []
    for asana in asanas:
        if asana.related_postures.filter(dataset="").exists():
            pass
        else:
            trained_asanas.append(asana)
    return render(request,"users/user_view_asana.html",{
        "asanas":trained_asanas,
    })


@login_required
@user_passes_test(check_student)
def user_view_posture(request,asana_id):
    postures = Posture.objects.filter(asana=Asana.objects.get(id=asana_id)).order_by('step_no')
    return render(request,"users/user_view_posture.html",{
        "postures":postures,
    })




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