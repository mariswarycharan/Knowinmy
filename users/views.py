from tkinter.messagebox import NO
from django.shortcuts import render,redirect
from django.http.response import HttpResponse
from django.views.decorators import gzip
from django.http import StreamingHttpResponse
import cv2
import os
import threading
import math
import cv2
from cv2 import VideoCapture
import mediapipe as mp
import pandas as pd
from datetime import datetime,timedelta

from yoga.settings import BASE_DIR
from .models import *
from pathlib import Path
from django.conf import settings
import statistics
from .forms import *
from django.contrib.auth import authenticate,login
from django.utils import timezone

def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(username=username,password=password)
        if user is not None:
            login(request,user)
            return redirect("home")
    return render(request,"users/login.html")

 
def view_trained(request):
    trained_asanas = Asana.objects.filter(created_by = request.user)
    return render(request,"users/view_trained.html",{
        "trained_asanas":trained_asanas,
    })


def view_posture(request,asana_id):
    postures = Posture.objects.filter(asana=Asana.objects.get(id=asana_id)).order_by('order')
    return render(request,"users/view_posture.html",{
        "postures":postures,
    })


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
                Posture.objects.create(name=f"Step-{i}",asana=asana,order=i)
            return redirect("view-trained")
    return render(request,"users/create_asana.html",{
        'form':form,
    })

def home(request):
    return render(request,"users/home.html")




#model starts
mp_draw = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles
my_pose = mp.solutions.pose
pose = my_pose.Pose()

# write the function find angle between three points  
def calculate_angle(landmark1,landmark2,landmark3):
    global angle
    x1,y1 = landmark1
    x2,y2 = landmark2
    x3,y3 = landmark3
    angle = math.degrees(math.atan2(y3-y2,x3-x2)-math.atan2(y1-y2,x1-x2))
    if angle < 0 :
        angle *= -1
    if angle > 180:
        angle = 360 - angle
    # cv2.circle(frame,(round(self.x1*width_frame),round(self.y1*height_frame)),radius=20,color=(180,20,40),thickness=3)
    return round(angle)



class TrainVideoCamera(object):
    def __init__(self,posture_id):
        self.name_of_step = Posture.objects.get(id=posture_id).name
        # self.created_at = datetime.now()
        self.posture_id = posture_id
        self.ab = 0
        self.video = cv2.VideoCapture(0)
        self.dataset_pose = pd.DataFrame(data={self.name_of_step:[],self.name_of_step+"_hands_distance":[],self.name_of_step+"_right_hand_angle2_ellow":[],
                                  self.name_of_step+"_left_hand_angle1_ellow":[],self.name_of_step+"_right_hand_angle4_shoulder":[],
                                  self.name_of_step+"_left_hand_angle3_shoulder":[],self.name_of_step+"_right_hip":[],self.name_of_step+"_left_hip":[],
                                  self.name_of_step+"_right_knee":[],self.name_of_step+"_left_knee":[]})
        (self.grabbed, self.frame) = self.video.read()
        threading.Thread(target=self.update, args=()).start()

    def __del__(self):
        self.video.release()

    def get_frame(self):
        image = self.frame
        _, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()

    def update(self):
        while True:
            # if (self.created_at + timedelta(seconds=60)) < datetime.now():
            #     self.dataset_pose.to_csv(str(self.name_of_step)+"_dataset.csv")
            #     break
            if self.ab == 500:
                asana_name = Posture.objects.get(id=self.posture_id).asana.name
                print(self.dataset_pose.to_csv(Path("./media/" + asana_name + "_" + self.name_of_step+".csv")))
                posture = Posture.objects.get(id=self.posture_id)
                posture.dataset.name =  asana_name + "_" + self.name_of_step+".csv"
                posture.save()
                break
            self.ab += 1
            
            (grabbed, frame) = self.video.read()
            frame=cv2.resize(frame,(749, 720))
            frame = cv2.flip(frame,1)
            frame = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
            font = cv2.FONT_HERSHEY_SIMPLEX
  
            # org
            org = (00, 185)
            
            # fontScale
            fontScale = 1
            
            # Red color in BGR
            color = (0, 0, 255)
            
            # Line thickness of 2 px
            thickness = 2
            
            # Using cv2.putText() method
            frame = cv2.putText(frame, str(self.ab), org, font, fontScale, 
                            color, thickness, cv2.LINE_AA, False)
            self.results = pose.process(frame)
            self.height_frame , self.width_frame,_ = frame.shape
            if self.results.pose_landmarks:
                mp_draw.draw_landmarks(frame,self.results.pose_landmarks,my_pose.POSE_CONNECTIONS,
                                landmark_drawing_spec=mp_draw.DrawingSpec(color=(255,255,255),thickness=3, circle_radius=3),
                                connection_drawing_spec=mp_draw.DrawingSpec(color=(49,125,237) ,thickness=2, circle_radius=2))
                self.body_landmarks = self.results.pose_landmarks.landmark
        
                self.left_hand_angle1_ellow = calculate_angle([self.body_landmarks[my_pose.PoseLandmark.RIGHT_SHOULDER.value].x,self.body_landmarks[my_pose.PoseLandmark.RIGHT_SHOULDER.value].y],
                                                [self.body_landmarks[my_pose.PoseLandmark.RIGHT_ELBOW.value].x,self.body_landmarks[my_pose.PoseLandmark.RIGHT_ELBOW.value].y],
                                                [self.body_landmarks[my_pose.PoseLandmark.RIGHT_WRIST.value].x,self.body_landmarks[my_pose.PoseLandmark.RIGHT_WRIST.value].y])
                
                self.right_hand_angle2_ellow = calculate_angle([self.body_landmarks[my_pose.PoseLandmark.LEFT_SHOULDER.value].x,self.body_landmarks[my_pose.PoseLandmark.LEFT_SHOULDER.value].y],
                                                [self.body_landmarks[my_pose.PoseLandmark.LEFT_ELBOW.value].x,self.body_landmarks[my_pose.PoseLandmark.LEFT_ELBOW.value].y],
                                                [self.body_landmarks[my_pose.PoseLandmark.LEFT_WRIST.value].x,self.body_landmarks[my_pose.PoseLandmark.LEFT_WRIST.value].y])
                
                self.left_hand_angle3_shoulder = calculate_angle([self.body_landmarks[my_pose.PoseLandmark.RIGHT_ELBOW.value].x,self.body_landmarks[my_pose.PoseLandmark.RIGHT_ELBOW.value].y],
                                                [self.body_landmarks[my_pose.PoseLandmark.RIGHT_SHOULDER.value].x,self.body_landmarks[my_pose.PoseLandmark.RIGHT_SHOULDER.value].y],
                                                [self.body_landmarks[my_pose.PoseLandmark.RIGHT_HIP.value].x,self.body_landmarks[my_pose.PoseLandmark.RIGHT_HIP.value].y])
                                                
                
                self.right_hand_angle4_shoulder = calculate_angle([self.body_landmarks[my_pose.PoseLandmark.LEFT_ELBOW.value].x,self.body_landmarks[my_pose.PoseLandmark.LEFT_ELBOW.value].y],
                                                    [self.body_landmarks[my_pose.PoseLandmark.LEFT_SHOULDER.value].x,self.body_landmarks[my_pose.PoseLandmark.LEFT_SHOULDER.value].y],
                                                    [self.body_landmarks[my_pose.PoseLandmark.LEFT_HIP.value].x,self.body_landmarks[my_pose.PoseLandmark.LEFT_HIP.value].y])
                
                self.left_hip = calculate_angle([self.body_landmarks[my_pose.PoseLandmark.RIGHT_SHOULDER.value].x,self.body_landmarks[my_pose.PoseLandmark.RIGHT_SHOULDER.value].y],
                                            [self.body_landmarks[my_pose.PoseLandmark.RIGHT_HIP.value].x,self.body_landmarks[my_pose.PoseLandmark.RIGHT_HIP.value].y],
                                            [self.body_landmarks[my_pose.PoseLandmark.RIGHT_KNEE.value].x,self.body_landmarks[my_pose.PoseLandmark.RIGHT_KNEE.value].y])
                
                self.right_hip = calculate_angle([self.body_landmarks[my_pose.PoseLandmark.LEFT_SHOULDER.value].x,self.body_landmarks[my_pose.PoseLandmark.LEFT_SHOULDER.value].y],
                                            [self.body_landmarks[my_pose.PoseLandmark.LEFT_HIP.value].x,self.body_landmarks[my_pose.PoseLandmark.LEFT_HIP.value].y],
                                            [self.body_landmarks[my_pose.PoseLandmark.LEFT_KNEE.value].x,self.body_landmarks[my_pose.PoseLandmark.LEFT_KNEE.value].y])
                
                self.left_knee = calculate_angle([self.body_landmarks[my_pose.PoseLandmark.RIGHT_HIP.value].x,self.body_landmarks[my_pose.PoseLandmark.RIGHT_HIP.value].y],
                                            [self.body_landmarks[my_pose.PoseLandmark.RIGHT_KNEE.value].x,self.body_landmarks[my_pose.PoseLandmark.RIGHT_KNEE.value].y],
                                            [self.body_landmarks[my_pose.PoseLandmark.RIGHT_ANKLE.value].x,self.body_landmarks[my_pose.PoseLandmark.RIGHT_ANKLE.value].y])
                
                self.right_knee = calculate_angle([self.body_landmarks[my_pose.PoseLandmark.LEFT_HIP.value].x,self.body_landmarks[my_pose.PoseLandmark.LEFT_HIP.value].y],
                                            [self.body_landmarks[my_pose.PoseLandmark.LEFT_KNEE.value].x,self.body_landmarks[my_pose.PoseLandmark.LEFT_KNEE.value].y],
                                            [self.body_landmarks[my_pose.PoseLandmark.LEFT_ANKLE.value].x,self.body_landmarks[my_pose.PoseLandmark.LEFT_ANKLE.value].y])
                
                right_wrist_cordi =  round(self.body_landmarks[my_pose.PoseLandmark.LEFT_WRIST.value].x*self.width_frame)
                left_wrist_cordi =  round(self.body_landmarks[my_pose.PoseLandmark.RIGHT_WRIST.value].x*self.width_frame)
                two_hand_distance = right_wrist_cordi - left_wrist_cordi
                if two_hand_distance < 0:
                    two_hand_distance *= -1
                    
                check_list = { self.name_of_step:[self.name_of_step], self.name_of_step+"_hands_distance":[two_hand_distance],self.name_of_step+"_right_hand_angle2_ellow":[self.right_hand_angle2_ellow],self.name_of_step+"_left_hand_angle1_ellow":[self.left_hand_angle1_ellow],
                            self.name_of_step+"_right_hand_angle4_shoulder":[self.right_hand_angle4_shoulder],self.name_of_step+"_left_hand_angle3_shoulder":[self.left_hand_angle3_shoulder],
                            self.name_of_step+"_right_hip":[self.right_hip],self.name_of_step+"_left_hip":[self.left_hip],self.name_of_step+"_right_knee":[self.right_knee],self.name_of_step+"_left_knee":[self.left_knee]}
                # to make each row into dataframe
                add_dataset_each_row = pd.DataFrame(data=check_list)
                # adding of each rows to dataset name dataset_pose
                self.dataset_pose = pd.concat([self.dataset_pose,add_dataset_each_row],ignore_index=True)           
            (self.grabbed,self.frame) = (grabbed, frame)

def train_gen(camera):
    while True:
        if camera.ab  == 500:
            del camera
            yield(b'--frame\r\n'
              b'Content-Type: image/jpeg\r\n\r\n' + b'\r\n\r\n')
            break
        frame = camera.get_frame()
        yield(b'--frame\r\n'
              b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@gzip.gzip_page
def train_live_feed(request,posture_id):
    try:
        cam = TrainVideoCamera(posture_id)
        return StreamingHttpResponse(train_gen(cam), content_type="multipart/x-mixed-replace;boundary=frame")
    except:  
        pass

#model testing user side

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


def user_view_posture(request,asana_id):
    postures = Posture.objects.filter(asana=Asana.objects.get(id=asana_id)).order_by('order')
    return render(request,"users/user_view_posture.html",{
        "postures":postures,
    })


myhand = mp.solutions.hands
hands = myhand.Hands(max_num_hands = 2)

class TestVideoCamera(object):
    def __init__(self,posture_id):
        self.posture_id = posture_id 
        print(Posture.objects.get(id=posture_id).dataset.path)
        self.df = pd.read_csv(Posture.objects.get(id=posture_id).dataset.path)
        self.df = self.df.loc[:,~self.df.columns.str.contains("^Unnamed")]
        self.ini_col = self.df.columns
        self.x = 0
        self.y = 10
        self.mode_list = []
        self.result_display = ""
        self.count_results = 0
        self.video = cv2.VideoCapture(0)
        (self.grabbed, self.frame) = self.video.read()
        threading.Thread(target=self.update, args=()).start()

    def __del__(self):
        self.video.release()
        frame = None

    def get_frame(self):
        image = self.frame
        _, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()
    

    def calculate_angle(self,landmark1,landmark2,landmark3):
        self.x1,self.y1 = landmark1
        self.x2,self.y2 = landmark2
        self.x3,self.y3 = landmark3
        self.angle = math.degrees(math.atan2(self.y3-self.y2,self.x3-self.x2)-math.atan2(self.y1-self.y2,self.x1-self.x2))
        if self.angle < 0 :
            self.angle *= -1
        if self.angle > 180:
            self.angle = 360 - self.angle
            
        # cv2.circle(frame,(round(self.x1*width_frame),round(self.y1*height_frame)),radius=20,color=(180,20,40),thickness=3)
        return round(self.angle)

    def changing_colour(self,frame,angle,dataset_column,codi1_x,codi1_y,codi2_x,codi2_y,codi3_x,codi3_y,pose_name_display):
                if angle in dataset_column:
                    cv2.line(img=frame,pt1=(codi1_x,codi1_y),pt2=(codi2_x,codi2_y),color=(0,140,0),thickness=5)
                    cv2.line(img=frame,pt1=(codi2_x,codi2_y),pt2=(codi3_x,codi3_y),color=(0,140,0),thickness=5)
                else:
                    cv2.line(img=frame,pt1=(codi1_x,codi1_y),pt2=(codi2_x,codi2_y),color=(0,0,255),thickness=5)
                    cv2.line(img=frame,pt1=(codi2_x,codi2_y),pt2=(codi3_x,codi3_y),color=(0,0,255),thickness=5)
                    # print("wrongly done part of your body :",pose_name_display)   
    def update(self):
        while True:
            # if (self.created_at + timedelta(seconds=60)) < datetime.now():
            #     self.dataset_pose.to_csv(str(self.name_of_step)+"_dataset.csv")
            #     break
            
            (grabbed, frame) = self.video.read()
            frame=cv2.resize(frame,(749, 720))
            frame = cv2.flip(frame,1)
            # cv2.line(frame, pt1=(30,650),pt2=(600,650),color=(255,0,0),thickness=3)
            frame = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)

        
            self.height_frame , self.width_frame,_ = frame.shape
            self.results = pose.process(frame)
            self.results_hand = hands.process(frame)

            if self.results_hand.multi_hand_landmarks:
                for hand_landmarks in self.results_hand.multi_hand_landmarks:
                    mp_draw.draw_landmarks(frame, hand_landmarks,myhand.HAND_CONNECTIONS,
                                        mp_styles.get_default_hand_landmarks_style(),
                                        mp_styles.get_default_hand_connections_style())
            
            
            if self.results.pose_landmarks:
                
                # mp_draw.draw_landmarks(frame,self.results.pose_landmarks,my_pose.POSE_CONNECTIONS,
                #                     landmark_drawing_spec=mp_draw.DrawingSpec(color=(255,255,255),thickness=3, circle_radius=3),
                #                     connection_drawing_spec=mp_draw.DrawingSpec(color=(255,255,255) ,thickness=3, circle_radius=3))
                self.body_landmarks = self.results.pose_landmarks.landmark
                
                # write the function find angle between three points
                
                # for angles in our body 8 angles !!!!!!!!!!!!!!!
                
                self.left_hand_angle1_ellow = self.calculate_angle([self.body_landmarks[my_pose.PoseLandmark.RIGHT_SHOULDER.value].x,self.body_landmarks[my_pose.PoseLandmark.RIGHT_SHOULDER.value].y],
                                                [self.body_landmarks[my_pose.PoseLandmark.RIGHT_ELBOW.value].x,self.body_landmarks[my_pose.PoseLandmark.RIGHT_ELBOW.value].y],
                                                [self.body_landmarks[my_pose.PoseLandmark.RIGHT_WRIST.value].x,self.body_landmarks[my_pose.PoseLandmark.RIGHT_WRIST.value].y])
                
                self.right_hand_angle2_ellow = self.calculate_angle([self.body_landmarks[my_pose.PoseLandmark.LEFT_SHOULDER.value].x,self.body_landmarks[my_pose.PoseLandmark.LEFT_SHOULDER.value].y],
                                                [self.body_landmarks[my_pose.PoseLandmark.LEFT_ELBOW.value].x,self.body_landmarks[my_pose.PoseLandmark.LEFT_ELBOW.value].y],
                                                [self.body_landmarks[my_pose.PoseLandmark.LEFT_WRIST.value].x,self.body_landmarks[my_pose.PoseLandmark.LEFT_WRIST.value].y])
                
                self.left_hand_angle3_shoulder = self.calculate_angle([self.body_landmarks[my_pose.PoseLandmark.RIGHT_ELBOW.value].x,self.body_landmarks[my_pose.PoseLandmark.RIGHT_ELBOW.value].y],
                                                [self.body_landmarks[my_pose.PoseLandmark.RIGHT_SHOULDER.value].x,self.body_landmarks[my_pose.PoseLandmark.RIGHT_SHOULDER.value].y],
                                                [self.body_landmarks[my_pose.PoseLandmark.RIGHT_HIP.value].x,self.body_landmarks[my_pose.PoseLandmark.RIGHT_HIP.value].y])
                                                
                self.right_hand_angle4_shoulder = self.calculate_angle([self.body_landmarks[my_pose.PoseLandmark.LEFT_ELBOW.value].x,self.body_landmarks[my_pose.PoseLandmark.LEFT_ELBOW.value].y],
                                                    [self.body_landmarks[my_pose.PoseLandmark.LEFT_SHOULDER.value].x,self.body_landmarks[my_pose.PoseLandmark.LEFT_SHOULDER.value].y],
                                                    [self.body_landmarks[my_pose.PoseLandmark.LEFT_HIP.value].x,self.body_landmarks[my_pose.PoseLandmark.LEFT_HIP.value].y])
                
                self.left_hip = self.calculate_angle([self.body_landmarks[my_pose.PoseLandmark.RIGHT_SHOULDER.value].x,self.body_landmarks[my_pose.PoseLandmark.RIGHT_SHOULDER.value].y],
                                            [self.body_landmarks[my_pose.PoseLandmark.RIGHT_HIP.value].x,self.body_landmarks[my_pose.PoseLandmark.RIGHT_HIP.value].y],
                                            [self.body_landmarks[my_pose.PoseLandmark.RIGHT_KNEE.value].x,self.body_landmarks[my_pose.PoseLandmark.RIGHT_KNEE.value].y])
                
                self.right_hip = self.calculate_angle([self.body_landmarks[my_pose.PoseLandmark.LEFT_SHOULDER.value].x,self.body_landmarks[my_pose.PoseLandmark.LEFT_SHOULDER.value].y],
                                            [self.body_landmarks[my_pose.PoseLandmark.LEFT_HIP.value].x,self.body_landmarks[my_pose.PoseLandmark.LEFT_HIP.value].y],
                                            [self.body_landmarks[my_pose.PoseLandmark.LEFT_KNEE.value].x,self.body_landmarks[my_pose.PoseLandmark.LEFT_KNEE.value].y])
                
                self.left_knee = self.calculate_angle([self.body_landmarks[my_pose.PoseLandmark.RIGHT_HIP.value].x,self.body_landmarks[my_pose.PoseLandmark.RIGHT_HIP.value].y],
                                            [self.body_landmarks[my_pose.PoseLandmark.RIGHT_KNEE.value].x,self.body_landmarks[my_pose.PoseLandmark.RIGHT_KNEE.value].y],
                                            [self.body_landmarks[my_pose.PoseLandmark.RIGHT_ANKLE.value].x,self.body_landmarks[my_pose.PoseLandmark.RIGHT_ANKLE.value].y])
                
                self.right_knee = self.calculate_angle([self.body_landmarks[my_pose.PoseLandmark.LEFT_HIP.value].x,self.body_landmarks[my_pose.PoseLandmark.LEFT_HIP.value].y],
                                            [self.body_landmarks[my_pose.PoseLandmark.LEFT_KNEE.value].x,self.body_landmarks[my_pose.PoseLandmark.LEFT_KNEE.value].y],
                                            [self.body_landmarks[my_pose.PoseLandmark.LEFT_ANKLE.value].x,self.body_landmarks[my_pose.PoseLandmark.LEFT_ANKLE.value].y])
                
                self.right_wrist_cordi =  round(self.body_landmarks[my_pose.PoseLandmark.LEFT_WRIST.value].x*self.width_frame)
                self.left_wrist_cordi =  round(self.body_landmarks[my_pose.PoseLandmark.RIGHT_WRIST.value].x*self.width_frame)
                self.two_hand_distance = self.right_wrist_cordi - self.left_wrist_cordi
                if self.two_hand_distance < 0:
                    self.two_hand_distance *= -1
                # from total dataset spliting the each step dataset 
                
                self.each_step_data = self.df[self.df.columns[self.x:self.y]]
                # print(each_step_data)
                # columns of the each step dataset
                self.each_columns = list(self.each_step_data.columns)
                # prinQt(len(each_columns))
                for j in self.each_columns[1:]:
                    self.mode1 = statistics.mode(list(self.each_step_data[str(j)]))
                    self.mode_list.append(self.mode1)
                self.sum_mode = sum(self.mode_list)
            
                # condition for checking pose
                if (round(self.two_hand_distance) in list(self.each_step_data[str(self.each_columns[1])]) and round(self.right_hand_angle2_ellow) in list(self.each_step_data[str(self.each_columns[2])]) and round(self.left_hand_angle1_ellow) in list(self.each_step_data[str(self.each_columns[3])]) and
                    round(self.right_hand_angle4_shoulder) in list(self.each_step_data[str(self.each_columns[4])]) and round(self.left_hand_angle3_shoulder) in list(self.each_step_data[str(self.each_columns[5])]) and 
                    round(self.right_hip) in list(self.each_step_data[str(self.each_columns[6])]) and round(self.left_hip) in list(self.each_step_data[str(self.each_columns[7])]) and 
                    round(self.right_knee) in list(self.each_step_data[str(self.each_columns[8])]) and round(self.left_knee) in list(self.each_step_data[str(self.each_columns[9])])):
                    self.sum_each_angle = self.right_hand_angle2_ellow + self.left_hand_angle1_ellow + self.right_hand_angle4_shoulder + self.left_hand_angle3_shoulder + self.right_hip + self.left_hip + self.right_knee + self.left_knee
                    self.accuracy = (self.sum_each_angle/self.sum_mode)*100
                    # mp_draw.draw_landmarks(frame,self.results.pose_landmarks,my_pose.POSE_CONNECTIONS,
                    #                 landmark_drawing_spec=mp_draw.DrawingSpec(color=(170, 255, 0),thickness=3, circle_radius=3),
                    #                 connection_drawing_spec=mp_draw.DrawingSpec(color=(170, 255, 0) ,thickness=3, circle_radius=3))
                    if self.accuracy > 100:
                        self.accuracy = self.accuracy - 100
                        self.accuracy = 100 - self.accuracy
                        print("your accuracy of ",str(self.each_columns[0]),"is",self.accuracy)

                    self.count_results += 1
                    if self.count_results == 60 :
                        self.result_display += "successfully done"
                        self.result_display += str(self.each_columns[0])
                        break
                        
                        
                self.mode_list.clear()

                self.changing_colour(frame,round(self.right_hand_angle2_ellow),list(self.each_step_data[str(self.each_columns[2])]),
                        round(self.body_landmarks[my_pose.PoseLandmark.RIGHT_SHOULDER.value].x*self.width_frame),round(self.body_landmarks[my_pose.PoseLandmark.RIGHT_SHOULDER.value].y*self.height_frame),
                        round(self.body_landmarks[my_pose.PoseLandmark.RIGHT_ELBOW.value].x*self.width_frame),round(self.body_landmarks[my_pose.PoseLandmark.RIGHT_ELBOW.value].y *self.height_frame),
                        round(self.body_landmarks[my_pose.PoseLandmark.RIGHT_WRIST.value].x*self.width_frame),round(self.body_landmarks[my_pose.PoseLandmark.RIGHT_WRIST.value].y*self.height_frame),
                        self.each_columns[2])
        
                self.changing_colour(frame,round(self.left_hand_angle1_ellow),list(self.each_step_data[str(self.each_columns[3])]),
                                round(self.body_landmarks[my_pose.PoseLandmark.LEFT_SHOULDER.value].x*self.width_frame),round(self.body_landmarks[my_pose.PoseLandmark.LEFT_SHOULDER.value].y*self.height_frame),
                                round(self.body_landmarks[my_pose.PoseLandmark.LEFT_ELBOW.value].x*self.width_frame),round(self.body_landmarks[my_pose.PoseLandmark.LEFT_ELBOW.value].y *self.height_frame),
                                round(self.body_landmarks[my_pose.PoseLandmark.LEFT_WRIST.value].x*self.width_frame),round(self.body_landmarks[my_pose.PoseLandmark.LEFT_WRIST.value].y*self.height_frame),
                                self.each_columns[3])
                
                self.changing_colour(frame,round(self.right_hand_angle4_shoulder),list(self.each_step_data[str(self.each_columns[4])]),
                                round(self.body_landmarks[my_pose.PoseLandmark.RIGHT_ELBOW.value].x*self.width_frame),round(self.body_landmarks[my_pose.PoseLandmark.RIGHT_ELBOW.value].y *self.height_frame),
                                round(self.body_landmarks[my_pose.PoseLandmark.RIGHT_SHOULDER.value].x*self.width_frame),round(self.body_landmarks[my_pose.PoseLandmark.RIGHT_SHOULDER.value].y*self.height_frame),
                                round(self.body_landmarks[my_pose.PoseLandmark.RIGHT_HIP.value].x*self.width_frame),round(self.body_landmarks[my_pose.PoseLandmark.RIGHT_HIP.value].y*self.height_frame),
                                self.each_columns[4])
            
                self.changing_colour(frame,round(self.left_hand_angle3_shoulder),list(self.each_step_data[str(self.each_columns[5])]),
                                round(self.body_landmarks[my_pose.PoseLandmark.LEFT_ELBOW.value].x*self.width_frame),round(self.body_landmarks[my_pose.PoseLandmark.LEFT_ELBOW.value].y *self.height_frame),
                                round(self.body_landmarks[my_pose.PoseLandmark.LEFT_SHOULDER.value].x*self.width_frame),round(self.body_landmarks[my_pose.PoseLandmark.LEFT_SHOULDER.value].y*self.height_frame),
                                round(self.body_landmarks[my_pose.PoseLandmark.LEFT_HIP.value].x*self.width_frame),round(self.body_landmarks[my_pose.PoseLandmark.LEFT_HIP.value].y*self.height_frame),
                                self.each_columns[5])
                
                self.changing_colour(frame,round(self.right_hip),list(self.each_step_data[str(self.each_columns[6])]),
                                round(self.body_landmarks[my_pose.PoseLandmark.RIGHT_SHOULDER.value].x*self.width_frame),round(self.body_landmarks[my_pose.PoseLandmark.RIGHT_SHOULDER.value].y*self.height_frame),
                                round(self.body_landmarks[my_pose.PoseLandmark.RIGHT_HIP.value].x*self.width_frame),round(self.body_landmarks[my_pose.PoseLandmark.RIGHT_HIP.value].y*self.height_frame),
                                round(self.body_landmarks[my_pose.PoseLandmark.RIGHT_KNEE.value].x*self.width_frame),round(self.body_landmarks[my_pose.PoseLandmark.RIGHT_KNEE.value].y *self.height_frame),
                                self.each_columns[6])
                
                self.changing_colour(frame, round(self.left_hip),list(self.each_step_data[str(self.each_columns[7])]),
                                round(self.body_landmarks[my_pose.PoseLandmark.LEFT_SHOULDER.value].x*self.width_frame),round(self.body_landmarks[my_pose.PoseLandmark.LEFT_SHOULDER.value].y*self.height_frame),
                                round(self.body_landmarks[my_pose.PoseLandmark.LEFT_HIP.value].x*self.width_frame),round(self.body_landmarks[my_pose.PoseLandmark.LEFT_HIP.value].y*self.height_frame),
                                round(self.body_landmarks[my_pose.PoseLandmark.LEFT_KNEE.value].x*self.width_frame),round(self.body_landmarks[my_pose.PoseLandmark.LEFT_KNEE.value].y *self.height_frame),
                                self.each_columns[7])
                                    
                self.changing_colour(frame,round(self.right_knee),list(self.each_step_data[str(self.each_columns[8])]),
                                round(self.body_landmarks[my_pose.PoseLandmark.RIGHT_HIP.value].x*self.width_frame),round(self.body_landmarks[my_pose.PoseLandmark.RIGHT_HIP.value].y*self.height_frame),
                                round(self.body_landmarks[my_pose.PoseLandmark.RIGHT_KNEE.value].x*self.width_frame),round(self.body_landmarks[my_pose.PoseLandmark.RIGHT_KNEE.value].y *self.height_frame),
                                round(self.body_landmarks[my_pose.PoseLandmark.RIGHT_ANKLE.value].x*self.width_frame),round(self.body_landmarks[my_pose.PoseLandmark.RIGHT_ANKLE.value].y*self.height_frame),
                                self.each_columns[8])
                
                self.changing_colour(frame,round(self.left_knee),list(self.each_step_data[str(self.each_columns[9])]),
                                round(self.body_landmarks[my_pose.PoseLandmark.LEFT_HIP.value].x*self.width_frame),round(self.body_landmarks[my_pose.PoseLandmark.LEFT_HIP.value].y*self.height_frame),
                                round(self.body_landmarks[my_pose.PoseLandmark.LEFT_KNEE.value].x*self.width_frame),round(self.body_landmarks[my_pose.PoseLandmark.LEFT_KNEE.value].y *self.height_frame),
                               round(self.body_landmarks[my_pose.PoseLandmark.LEFT_ANKLE.value].x*self.width_frame),round(self.body_landmarks[my_pose.PoseLandmark.LEFT_ANKLE.value].y*self.height_frame),
                                self.each_columns[9])
                        
                #  x and y for changing each step dataset
                self.x += 10
                self.y += 10
                if self.y > len(self.ini_col):
                    self.x = 0
                    self.y = 10   
            cv2.putText(frame,str(self.result_display),(50,600),cv2.FONT_HERSHEY_PLAIN,3,(0,255,0),3,cv2.LINE_AA)
            cv2.putText(frame,str(self.count_results),(50,60),cv2.FONT_HERSHEY_PLAIN,3,(255,0,0),4,cv2.LINE_AA)
            

            (self.grabbed,self.frame) = (grabbed, frame)

def test_gen(camera):
    while True:
        if camera.count_results == 60:
            yield(b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + b'\r\n\r\n')
            del camera
            break
        frame = camera.get_frame()
        yield(b'--frame\r\n'
              b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


@gzip.gzip_page
def test_live_feed(request,posture_id):
    try:
        cam = TestVideoCamera(posture_id)
        return StreamingHttpResponse(test_gen(cam), content_type="multipart/x-mixed-replace;boundary=frame")
    except:  
        pass



