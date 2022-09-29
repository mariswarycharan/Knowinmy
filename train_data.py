from turtle import right
from unittest import result
import cv2
from cv2 import VideoCapture
from lightgbm import cv
from matplotlib import image
import mediapipe as mp
from nbformat import read
import numpy as np
import math
import time
import pyautogui
import pandas as pd
# import pyttsx3

# already made dataset
# add this lines to add next step !!!!!!!!!!!!!!!!!!!!!!! 
# df = pd.read_csv(r"C:\Users\USER\Documents\vs code example\maindata")

name_of_step = str(input("enter your step name to train the pose: "))
# engine = pyttsx3.init()
# engine.say("to train your model show the pose")
# engine.runAndWait()
time.sleep(3)
# columns = list(df.columns)

mp_draw = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles
my_pose = mp.solutions.pose
pose = my_pose.Pose()
close_count = 0

# initial empty dataset 
initial_dataset = pd.DataFrame()
# 
dataset_pose = pd.DataFrame(data={name_of_step:[],name_of_step+"_hands_distance":[],name_of_step+"_right_hand_angle2_ellow":[],
                                  name_of_step+"_left_hand_angle1_ellow":[],name_of_step+"_right_hand_angle4_shoulder":[],
                                  name_of_step+"_left_hand_angle3_shoulder":[],name_of_step+"_right_hip":[],name_of_step+"_left_hip":[],
                                  name_of_step+"_right_knee":[],name_of_step+"_left_knee":[]})

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
                
            # cv2.circle(frame,(round(x1*width_frame),round(y1*height_frame)),radius=20,color=(180,20,40),thickness=3)
            return round(angle)
        
video = cv2.VideoCapture(0)
while True:
    cap,frame = video.read()
    frame=cv2.resize(frame,(749, 720))
    frame = cv2.flip(frame,1)
    frame = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
    height_frame , width_frame,_ = frame.shape
    results = pose.process(frame)
    
    if results.pose_landmarks:
        
        mp_draw.draw_landmarks(frame,results.pose_landmarks,my_pose.POSE_CONNECTIONS,
                            landmark_drawing_spec=mp_draw.DrawingSpec(color=(255,255,255),thickness=3, circle_radius=3),
                            connection_drawing_spec=mp_draw.DrawingSpec(color=(49,125,237) ,thickness=2, circle_radius=2))
        body_landmarks = results.pose_landmarks.landmark
        
        
        
        # for angles in our body 8 angles !!!!!!!!!!!!!!!
        
        left_hand_angle1_ellow = calculate_angle([body_landmarks[my_pose.PoseLandmark.RIGHT_SHOULDER.value].x,body_landmarks[my_pose.PoseLandmark.RIGHT_SHOULDER.value].y],
                                           [body_landmarks[my_pose.PoseLandmark.RIGHT_ELBOW.value].x,body_landmarks[my_pose.PoseLandmark.RIGHT_ELBOW.value].y],
                                           [body_landmarks[my_pose.PoseLandmark.RIGHT_WRIST.value].x,body_landmarks[my_pose.PoseLandmark.RIGHT_WRIST.value].y])
        
        right_hand_angle2_ellow = calculate_angle([body_landmarks[my_pose.PoseLandmark.LEFT_SHOULDER.value].x,body_landmarks[my_pose.PoseLandmark.LEFT_SHOULDER.value].y],
                                           [body_landmarks[my_pose.PoseLandmark.LEFT_ELBOW.value].x,body_landmarks[my_pose.PoseLandmark.LEFT_ELBOW.value].y],
                                           [body_landmarks[my_pose.PoseLandmark.LEFT_WRIST.value].x,body_landmarks[my_pose.PoseLandmark.LEFT_WRIST.value].y])
        
        left_hand_angle3_shoulder = calculate_angle([body_landmarks[my_pose.PoseLandmark.RIGHT_ELBOW.value].x,body_landmarks[my_pose.PoseLandmark.RIGHT_ELBOW.value].y],
                                           [body_landmarks[my_pose.PoseLandmark.RIGHT_SHOULDER.value].x,body_landmarks[my_pose.PoseLandmark.RIGHT_SHOULDER.value].y],
                                           [body_landmarks[my_pose.PoseLandmark.RIGHT_HIP.value].x,body_landmarks[my_pose.PoseLandmark.RIGHT_HIP.value].y])
                                           
        
        right_hand_angle4_shoulder = calculate_angle([body_landmarks[my_pose.PoseLandmark.LEFT_ELBOW.value].x,body_landmarks[my_pose.PoseLandmark.LEFT_ELBOW.value].y],
                                            [body_landmarks[my_pose.PoseLandmark.LEFT_SHOULDER.value].x,body_landmarks[my_pose.PoseLandmark.LEFT_SHOULDER.value].y],
                                            [body_landmarks[my_pose.PoseLandmark.LEFT_HIP.value].x,body_landmarks[my_pose.PoseLandmark.LEFT_HIP.value].y])
        
        left_hip = calculate_angle([body_landmarks[my_pose.PoseLandmark.RIGHT_SHOULDER.value].x,body_landmarks[my_pose.PoseLandmark.RIGHT_SHOULDER.value].y],
                                    [body_landmarks[my_pose.PoseLandmark.RIGHT_HIP.value].x,body_landmarks[my_pose.PoseLandmark.RIGHT_HIP.value].y],
                                    [body_landmarks[my_pose.PoseLandmark.RIGHT_KNEE.value].x,body_landmarks[my_pose.PoseLandmark.RIGHT_KNEE.value].y])
        
        right_hip = calculate_angle([body_landmarks[my_pose.PoseLandmark.LEFT_SHOULDER.value].x,body_landmarks[my_pose.PoseLandmark.LEFT_SHOULDER.value].y],
                                    [body_landmarks[my_pose.PoseLandmark.LEFT_HIP.value].x,body_landmarks[my_pose.PoseLandmark.LEFT_HIP.value].y],
                                    [body_landmarks[my_pose.PoseLandmark.LEFT_KNEE.value].x,body_landmarks[my_pose.PoseLandmark.LEFT_KNEE.value].y])
        
        left_knee = calculate_angle([body_landmarks[my_pose.PoseLandmark.RIGHT_HIP.value].x,body_landmarks[my_pose.PoseLandmark.RIGHT_HIP.value].y],
                                    [body_landmarks[my_pose.PoseLandmark.RIGHT_KNEE.value].x,body_landmarks[my_pose.PoseLandmark.RIGHT_KNEE.value].y],
                                    [body_landmarks[my_pose.PoseLandmark.RIGHT_ANKLE.value].x,body_landmarks[my_pose.PoseLandmark.RIGHT_ANKLE.value].y])
        
        right_knee = calculate_angle([body_landmarks[my_pose.PoseLandmark.LEFT_HIP.value].x,body_landmarks[my_pose.PoseLandmark.LEFT_HIP.value].y],
                                     [body_landmarks[my_pose.PoseLandmark.LEFT_KNEE.value].x,body_landmarks[my_pose.PoseLandmark.LEFT_KNEE.value].y],
                                     [body_landmarks[my_pose.PoseLandmark.LEFT_ANKLE.value].x,body_landmarks[my_pose.PoseLandmark.LEFT_ANKLE.value].y])
        
        right_wrist_cordi =  round(body_landmarks[my_pose.PoseLandmark.LEFT_WRIST.value].x*width_frame)
        left_wrist_cordi =  round(body_landmarks[my_pose.PoseLandmark.RIGHT_WRIST.value].x*width_frame)
        two_hand_distance = right_wrist_cordi - left_wrist_cordi
        if two_hand_distance < 0:
            two_hand_distance *= -1
            
        check_list = { name_of_step:[name_of_step], name_of_step+"_hands_distance":[two_hand_distance],name_of_step+"_right_hand_angle2_ellow":[right_hand_angle2_ellow],name_of_step+"_left_hand_angle1_ellow":[left_hand_angle1_ellow],
                      name_of_step+"_right_hand_angle4_shoulder":[right_hand_angle4_shoulder],name_of_step+"_left_hand_angle3_shoulder":[left_hand_angle3_shoulder],
                      name_of_step+"_right_hip":[right_hip],name_of_step+"_left_hip":[left_hip],name_of_step+"_right_knee":[right_knee],name_of_step+"_left_knee":[left_knee]}
        # to make each row into dataframe
        add_dataset_each_row = pd.DataFrame(data=check_list)
        # adding of each rows to dataset name dataset_pose
        dataset_pose = pd.concat([dataset_pose,add_dataset_each_row],ignore_index=True)
        
    cv2.imshow("image",frame)
    
    close_count += 1
    if close_count > 500:
        # to enter the first pose step datas so combine the initial_dataset and dataset of each pose step to add   
        # final_dataset_first_pose = pd.concat([initial_dataset,dataset_pose])
        # final_dataset_first_pose.reset_index()
        dataset_pose.to_csv(str(name_of_step)+"_dataset.csv")
        break
        # combining the next all pose step using this code
        # add this lines to add next step !!!!!!!!!!!!!!!!!!!!!!!
        # if name_of_step not in columns:
        #     new_final_dataset = pd.concat([df,final_dataset_first_pose],axis=1,join="inner")
            # check = pyautogui.confirm("Are you sure to add the data to final dataset")
            # if check == "OK":
            #     new_final_dataset.to_csv("maindata")
            # else:
            #     pass
        # final_dataset_first_pose.to_csv("maindata.csv")
        # break
    
    key =  cv2.waitKey(1)
    if key == 81:
        break
  
video.release()

cv2.destroyAllWindows()
