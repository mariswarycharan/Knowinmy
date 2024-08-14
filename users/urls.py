from django.urls import path
from .views import *
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.urls import path, include
from .views import CreateAsanaView

from django.contrib.auth import views as auth_views




urlpatterns =[

    path("",home,name="home"),
    path('payment/',subscription_payment,name='subscription-payment'),
    path("razorpay/callback/", callback, name="callback"),
    path("register/",register,name="register"),
    path("login/",user_login,name="login"),
    path("logout/",log_out,name="logout"),
   
    path('create_asana/', CreateAsanaView.as_view(), name='create-asana'),
    path("staff_dashboard/",staff_dashboard_function,name="staff_dashboard"),
    # # path("reset_password/",auth_ views,PasswordResetView.as_view()),
    # path("reset_password/", auth_views.PasswordResetView.as_view(), name="password_reset"),
    # path("reset_password_sent/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    # path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    # path("reset_password_complete/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
    path('password-reset/', ResetPasswordView.as_view(), name='password_reset'),



    

    

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
    # path("get_excel_data/",get_excel_data,name="get-data"),
    
    # add student 
   
    path("trainer_dashboard/",CourseCreationView.as_view(),name="create-course"),


    # CRUD FOR ASANA CREATION 
    path('update_asana/<int:asana_id>/', CreateAsanaView.as_view(), name='update_asana'),
    # path('delete_asana/<int:asana_id>/',CreateAsanaView.as_view(),name='delete_asana'),
    # path('delete_asana/<int:asana_id>/', create_asana, name='delete_asana'),


    # crud for course creation
    path('update_course/<int:course_id/',CourseCreationView.as_view(),name='update_course'),
    
   
    #profile
    path('profile/',profile_view,name='profile-user'),

    # student mapping
    path('student_mapping/',StudentCourseMapView.as_view(),name='student-mapp-courses'),
    path('update_student_course/<int:enrollment_i',StudentCourseMapView.as_view(),name='student-course-update'),
   


    #api
    path("get_posture_dataset/",get_posture_dataset,name="get-posture-dataset"),

    # logging page 


    # dashboard page 
    path('dashboard/',dashboard,name='dashboard'),

   

    #subscription page 
    # path('subscription_plans/',subscription_plans,name='subscription-plans'),

    #payment page 
    # path('payment/',subscription_payment,name='subscription-payment'),
    # path("razorpay/callback/", callback, name="callback"),
  
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)