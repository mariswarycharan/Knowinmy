from django.urls import path
from .views import *
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth import views as auth_views


urlpatterns =[

    path("",home,name="home"),
    path("login/",user_login,name="login"),
    path("register/",register,name="register"),
    path("create_asana/",create_asana,name="create-asana"),
    path("staff_dashboard/",staff_dashboard_function,name="staff_dashboard"),
    # path("reset_password/",auth_ views,PasswordResetView.as_view()),
    path("reset_password/", auth_views.PasswordResetView.as_view(), name="password_reset"),
    path("reset_password_sent/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset_password_complete/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),

    

    #train - trainer side
    path("view_trained/",view_trained,name="view-trained"),
    path("view_posture/<int:asana_id>",view_posture,name="view-posture"),
    path("edit_postures/<int:posture_id>",edit_posture,name="edit-posture"),
    

    #test - user side
    path("user_view_asana/",user_view_asana,name="user-view-asana"),
    path("user_view_posture/<int:asana_id>/",user_view_posture,name="user-view-posture"),
    path("get_posture/<int:posture_id>",get_posture,name="get-posture"),

    #Trainer_approval
    path("trainer_approval/",Trainer_approval_function,name="Trainer-approval"),
    
    # add student 
   
    path("trainer_dashboard/",Trainer_dashboard,name="Trainer-dashboard"),
   
    #profile
    path('profile/',profile_view,name='profile-user'),

    # student mapping
    path('student_mapping/',student_mapped_to_courses,name='student-mapp-courses'),
   


    #api
    path("get_posture_dataset/",get_posture_dataset,name="get-posture-dataset"),

    # logging page 


    # dashboard page 
    path('dashboard/',dashboard,name='dashboard'),

    #accuracy page 
    path('record_accuracy/', record_accuracy, name='record-accuracy'),
    path('finalize_accuracy',finalize_accuracy,name='finalize-accuracy'),

    #subscription page 
    path('subscription_plans/',subscription_plans,name='subscription-plans'),

    #payment page 
    path('payment/',subscription_payment,name='subscription-payment'),
    path("razorpay/callback/", callback, name="callback"),
  
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)