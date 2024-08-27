from django.urls import path
from .views import *
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from .views import CreateAsanaView

from django.contrib.auth import views as auth_views



urlpatterns = [
    # Base path with slug
    path('', home, name='home'),
    path('register/', register, name='register'),
    path('register-organisation/', register_organisation, name='register_organization'),
   
    # path('<slug:slug>/login/', user_login, name='login_slug'),
    path('login/', user_login, name='login'),
    path('<slug:slug>/payment/', subscription_payment, name='subscription-payment'),
    path('<slug:slug>/razorpay/callback/', callback, name='callback'),
    path('<slug:slug>/logout/', log_out, name='logout'),
    path('<slug:slug>/create_asana/', CreateAsanaView.as_view(), name='create-asana'),
    path('<slug:slug>/update_asana/<int:asana_id>/', CreateAsanaView.as_view(), name='update_asana'),
    path('<slug:slug>/staff_dashboard/', staff_dashboard_function, name='staff_dashboard'),
    path('<slug:slug>/view_trained/', view_trained, name='view-trained'),
    path('<slug:slug>/view_posture/<int:asana_id>/', view_posture, name='view-posture'),
    path('<slug:slug>/edit_postures/<int:posture_id>/', edit_posture, name='edit-posture'),
    path('<slug:slug>/user_view_asana/', user_view_asana, name='user-view-asana'),
    path('<slug:slug>/user_view_posture/<int:asana_id>/', user_view_posture, name='user-view-posture'),
    path('<slug:slug>/get_posture/<int:posture_id>/', get_posture, name='get-posture'),
    path('<slug:slug>/trainer_approval/', Trainer_approval_function, name='Trainer-approval'),
    path('<slug:slug>/onboarding_users_form/', onboarding_view, name='onboard-users-form'),
    path('<slug:slug>/client_table/', client_list, name='client-list'),
    path('<slug:slug>/trainer_dashboard/', CourseCreationView.as_view(), name='create-course'),
    path('<slug:slug>/update_course/<int:course_id>/', CourseCreationView.as_view(), name='update_course'),
    path('<slug:slug>/profile/', profile_view, name='profile-user'),
    path('<slug:slug>/student_mapping/', StudentCourseMapView.as_view(), name='student-mapp-courses'),
    path('<slug:slug>/update_student_course/<int:enrollment_id>/', StudentCourseMapView.as_view(), name='student-course-update'),
    path('<slug:slug>/clients/', client_list, name='client_list'),
    path('<slug:slug>/clients/<int:order_id>/delete/', delete_client, name='delete_client'),
    path('<slug:slug>/get_posture_dataset/', get_posture_dataset, name='get-posture-dataset'),
    # Define a URL for tenant-specific data
    # path('<slug:slug>/tenant-data/', tenant_data, name='tenant-data'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)