import cv2
import imutils
from YoloDetTRT import YoloTRT

import Jetson.GPIO as GPIO
import doorControl as door
import ioControl as io

from enum import Enum, auto
import threading

from HTTPServer import Initialize_Server, Shutdown_Server, set_latest_frame
from Ruleset import RulesetDecider
from GateStates import State

import signal
import sys

def gstreamer_pipeline(
    capture_width=1280,
    capture_height=720,
    display_width=1280,
    display_height=720,
    framerate=5,
    flip_method=0
):
    return (
        f"nvarguscamerasrc ! "
        f"video/x-raw(memory:NVMM), "
        f"width=(int){capture_width}, height=(int){capture_height}, "
        f"format=(string)NV12, framerate=(fraction){framerate}/1 ! "
        f"nvvidconv flip-method={flip_method} ! "
        f"video/x-raw, width=(int){display_width}, height=(int){display_height}, format=(string)BGRx ! "
        f"videoconvert ! "
        f"video/x-raw, format=(string)BGR ! appsink"
    )

def cleanup():
    print("[+] Cleaning up resources...")
    io.allPinsOff()
    GPIO.cleanup()
    Shutdown_Server(http_server)

def signal_handler(sig, frame):
    print('[+] Ctrl+C Detected... Exiting...')
    cleanup()
    sys.exit(0)

def main():
    #Global HTTP server for resource allocation and deallocation
    global http_server

    #Set up signal handler keyboard interrupt
    signal.signal(signal.SIGINT, signal_handler)

    #Start HTTP server on a separate thread
    #Should also make the web server optional as well
    http_server = Initialize_Server()

    #Set up the GPIO channel
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(7, GPIO.OUT, initial=GPIO.LOW)

    #Initialize door and IO pins
    io.setAllPins()
    door.initDoor()

    #Initialize State Machine
    current_state = State.IDLE

    #Initialize object detection class list
    objectList = []

    #Initialize YOLOv5 model via TensorRT engine
    model = YoloTRT(library="../../lib/libmyplugins.so", engine="../../models/yolov5s.engine", classes_file='../../models/classes/yolov5s.txt', conf=0.5, yolo_ver="v5")

    #In the DECIDE state, the RulesetDecider will be responsible for setting the next state depending on the configuration
    decider = RulesetDecider()

    #Open the camera using GStreamer pipeline
    cap = cv2.VideoCapture(gstreamer_pipeline(), cv2.CAP_GSTREAMER)

    #Our main loop
    while True:
        #------------IDLE State ------------------------------------------------------------
        if current_state == State.IDLE:
            print("System is idle.")
            if io.getVal('PIR'):
                current_state = State.DETECT
            else:
                current_state = State.IDLE #Put back to IDLE state

        #------------DETECT State ----------------------------------------------------------
        elif current_state == State.DETECT:
            print("Detecting objects.")
            ret_val, img = cap.read()
            if not ret_val:
                break

            #Resize the frame for YOLOv5
            img = imutils.resize(img, width=600)

            #Perform inference
            detections, t = model.Inference(img)

            #Update the latest_frame for streaming
            set_latest_frame(img.copy())

            objectList = [obj['class'] for obj in detections]
            current_state = State.DECISION

        #------------DECISION State --------------------------------------------------------
        elif current_state == State.DECISION:
            print("Decision making door.")
            
            #Decide on ruleset
            current_state = decider.decide(objectList)

        #------------DOOR OPEN State -------------------------------------------------------
        elif current_state == State.DOOR_OPEN:
            print("Opening door.")

            if not door.isDoorFullyOpen():
                door.openDoor()
            else:
                print('Door stopped on opening')
                door.stopDoor()
            
            current_state = State.IDLE

        #------------DOOR CLOSE State ------------------------------------------------------
        elif current_state == State.DOOR_CLOSE:
            print("Closing door.")
            
            #Read Hall Effect sensor of Door Closed. Keep closing if the Hall effect sensor is 0
            if not door.isDoorFullyClosed():
                door.closeDoor()
            else:
                print('Door stopped on closing')
                door.stopDoor()
                
            current_state = State.IDLE

        #------------Default State --------------------
        elif current_state == State.DELAY:
            print("Delaying operation.")
    
    #Sets all pins to LOW
    io.allPinsOff()

#Main logic
if __name__ == "__main__":
    main()
