from django.urls import path
from .views import *
from django.conf.urls.static import static
from django.conf import settings


urlpatterns =[
    path("",home,name="home"),
    path("login/",user_login,name="login"),
    path("create_asana/",create_asana,name="create-asana"),

    #train - trainer side
    path("train_model/<int:posture_id>",train_live_feed,name="train-model"),
    path("view_trained/",view_trained,name="view-trained"),
    path("view_posture/<int:asana_id>",view_posture,name="view-posture"),
    

    #test - user side
    path("user_view_asana/",user_view_asana,name="user-view-asana"),
    path("user_view_posture/<int:asana_id>",user_view_posture,name="user-view-posture"),
    path("test_model/<int:posture_id>",test_live_feed,name="test-model"),
    path("get_posture/<int:posture_id>",get_posture,name="get-posture"),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)