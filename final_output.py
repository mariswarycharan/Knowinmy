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
import pandas as pd
import statistics
# from train_data import dataset_pose

df = pd.read_csv(r"H:\yoga\media\test 3_Step-1.csv")
df = df.loc[:,~df.columns.str.contains("^Unnamed")]
ini_col = df.columns
mode_list = []
count_results = 0

mp_draw = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles
my_pose = mp.solutions.pose
myhand = mp.solutions.hands
hands = myhand.Hands(max_num_hands = 2)
pose = my_pose.Pose()

x = 0
y = 10
result_display = ""

video = cv2.VideoCapture(0)
while True:
    cap,frame = video.read()
    frame=cv2.resize(frame,(749, 720))
    frame = cv2.flip(frame,1)
    cv2.line(frame, pt1=(30,650),pt2=(600,650),color=(255,0,0),thickness=3)
    frame = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
    height_frame , width_frame,_ = frame.shape
    results = pose.process(frame)
    results_hand = hands.process(frame)
    if results_hand.multi_hand_landmarks:
        for hand_landmarks in results_hand.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks,myhand.HAND_CONNECTIONS,
                                   mp_styles.get_default_hand_landmarks_style(),
                                   mp_styles.get_default_hand_connections_style())
    
    if results.pose_landmarks:
        
        mp_draw.draw_landmarks(frame,results.pose_landmarks,my_pose.POSE_CONNECTIONS,
                            landmark_drawing_spec=mp_draw.DrawingSpec(color=(255,255,255),thickness=3, circle_radius=3),
                            connection_drawing_spec=mp_draw.DrawingSpec(color=(49,125,237) ,thickness=2, circle_radius=2))
        body_landmarks = results.pose_landmarks.landmark
        
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
        # from total dataset spliting the each step dataset 
        
        each_step_data = df[df.columns[x:y]]
        # print(each_step_data)
        # columns of the each step dataset
        each_columns = list(each_step_data.columns)
        # prinQt(len(each_columns))
        for j in each_columns[1:]:
            mode1 = statistics.mode(list(each_step_data[str(j)]))
            mode_list.append(mode1)
        sum_mode = sum(mode_list)
    
        # condition for checking pose
        if (round(two_hand_distance) in list(each_step_data[str(each_columns[1])]) and round(right_hand_angle2_ellow) in list(each_step_data[str(each_columns[2])]) and round(left_hand_angle1_ellow) in list(each_step_data[str(each_columns[3])]) and
            round(right_hand_angle4_shoulder) in list(each_step_data[str(each_columns[4])]) and round(left_hand_angle3_shoulder) in list(each_step_data[str(each_columns[5])]) and 
            round(right_hip) in list(each_step_data[str(each_columns[6])]) and round(left_hip) in list(each_step_data[str(each_columns[7])]) and 
            round(right_knee) in list(each_step_data[str(each_columns[8])]) and round(left_knee) in list(each_step_data[str(each_columns[9])])):
            sum_each_angle = right_hand_angle2_ellow + left_hand_angle1_ellow + right_hand_angle4_shoulder + left_hand_angle3_shoulder + right_hip + left_hip + right_knee + left_knee
            accuracy = (sum_each_angle/sum_mode)*100
            if accuracy > 100:
                accuracy = accuracy - 100
                accuracy = 100 - accuracy
                print("your accuracy of ",str(each_columns[0]),"is",accuracy)
            else:
                pass
                print("your accuracy of ",str(each_columns[0]),"is",accuracy)
            count_results += 1
            if count_results == 25:
                result_display += "successfully done"
                result_display += str(each_columns[0])
                count_results = 0
                
        mode_list.clear()
        
        #  x and y for changing each step dataset
        x += 10
        y += 10
        if y > len(ini_col):
            x = 0
            y = 10
    # cv2.putText(frame,str(result_display),(50,100),cv2.FONT_HERSHEY_PLAIN,3,(0,255,0),3,cv2.LINE_AA)    
    cv2.putText(frame,str(result_display),(50,600),cv2.FONT_HERSHEY_PLAIN,3,(0,255,0),3,cv2.LINE_AA)
    cv2.putText(frame,str(count_results),(50,60),cv2.FONT_HERSHEY_PLAIN,3,(255,0,0),4,cv2.LINE_AA)
    print(result_display)
    cv2.imshow("image",frame)
    
    key =  cv2.waitKey(1)
    if key == 81:
        break
  
video.release()

cv2.destroyAllWindows()

