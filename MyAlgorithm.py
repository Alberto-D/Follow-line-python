#!/usr/bin/python
#-*- coding: utf-8 -*-
import threading
import time
from datetime import datetime

import math
import cv2
import numpy as np

from PIL import Image

time_cycle = 80

boundaries = [
	([20, 0, 0], [50, 10, 70]),
]

class MyAlgorithm(threading.Thread):

    V=0
    W=0

    def __init__(self, camera, motors):
        self.camera = camera
        self.motors = motors
        self.threshold_image = np.zeros((640,360,3), np.uint8)
        self.color_image = np.zeros((640,360,3), np.uint8)
        self.stop_event = threading.Event()
        self.kill_event = threading.Event()
        self.lock = threading.Lock()
        self.threshold_image_lock = threading.Lock()
        self.color_image_lock = threading.Lock()
        threading.Thread.__init__(self, args=self.stop_event)
    
    def getImage(self):
        self.lock.acquire()
        img = self.camera.getImage().data
        self.lock.release()
        return img

    def set_color_image (self, image):
        img  = np.copy(image)
        if len(img.shape) == 2:
          img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        self.color_image_lock.acquire()
        self.color_image = img
        self.color_image_lock.release()
        
    def get_color_image (self):
        self.color_image_lock.acquire()
        img = np.copy(self.color_image)
        self.color_image_lock.release()
        return img
        
    def set_threshold_image (self, image):
        img = np.copy(image)
        if len(img.shape) == 2:
          img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        self.threshold_image_lock.acquire()
        self.threshold_image = img
        self.threshold_image_lock.release()
        
    def get_threshold_image (self):
        self.threshold_image_lock.acquire()
        img  = np.copy(self.threshold_image)
        self.threshold_image_lock.release()
        return img

    def run (self):

        while (not self.kill_event.is_set()):
            start_time = datetime.now()
            if not self.stop_event.is_set():
                self.algorithm()
            finish_Time = datetime.now()
            dt = finish_Time - start_time
            ms = (dt.days * 24 * 60 * 60 + dt.seconds) * 1000 + dt.microseconds / 1000.0
            #print (ms)
            if (ms < time_cycle):
                time.sleep((time_cycle - ms) / 1000.0)

    def stop (self):
        self.stop_event.set()

    def play (self):
        if self.is_alive():
            self.stop_event.clear()
        else:
            self.start()

    def kill (self):
        self.kill_event.set()

    def draw_circle(self,output,heigth):
        first_point = 0
        last_point  = 0
        for i in range(570):
            if np.any(output[heigth, i] != 0):
                if first_point == 0:
                    first_point = i
                last_point = i

        middle = (first_point+last_point)/2   
        cv2.circle(output, (middle,heigth), radius=5, color=(0, 0, 255), thickness=-1) 
        return middle

    def check_recta(self,m1,m2,m3):
        # if (340<m1<460):
        if(310<m3<350):
           return True
        else:
            return False



    def algorithm(self):
           
        #GETTING THE IMAGES
        image = self.getImage()

        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)


        for (lower, upper) in boundaries:
	    # create NumPy arrays from the boundaries
	    lower = np.array(lower, dtype = "uint8")
	    upper = np.array(upper, dtype = "uint8")
	    # find the colors within the specified boundaries and apply
	    # the mask
	    mask = cv2.inRange(image, lower, upper)
	    output = cv2.bitwise_and(image, image, mask = mask)

        height, width, channels = output.shape
        # 480 alto por 570 ancho, en el 240 es el horizonte, 3l 300 3mpi3za a la izquierda


        near = self.draw_circle(output,400)
        medium = self.draw_circle(output,300)
        far = self.draw_circle(output,250)

        VA_recto = self.check_recta(near, medium, far)

        #print("near:", near, " medium:", medium, " far :", far)
        if(VA_recto):
            MyAlgorithm.V = 30
            
            MyAlgorithm.W =-0.004*(far-330)
            print("RECTO V es : ", MyAlgorithm.V," W es : ",  MyAlgorithm.W) 
            #W=0
        else:
            pd = 0.005
            if(abs(far-330)>30):
                pd = 0.020
                #while(MyAlgorithm.V>15):
                if(MyAlgorithm.V > 25):
                    MyAlgorithm.V = MyAlgorithm.V-3
            
                print("CERRADA V es : ", MyAlgorithm.V," W es : ",  MyAlgorithm.W) 

            if(abs(far-330)>60):
                pd = 0.03
                if(MyAlgorithm.V>15):
                    MyAlgorithm.V = MyAlgorithm.V-4
                print(" MUY CERRADA V es : ", MyAlgorithm.V," W es : ",  MyAlgorithm.W) 
        
            MyAlgorithm.W =-pd*(far-330)

           
        self.motors.sendW(MyAlgorithm.W)
            

        self.motors.sendV(MyAlgorithm.V)
       
        

        print "Runing"

        self.set_threshold_image(output)
