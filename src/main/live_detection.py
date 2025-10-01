import cv2
import imutils
from YoloDetTRT import YoloTRT

import Jetson.GPIO as GPIO
from door_control import DoorControl
import io_control as io

from enum import Enum, auto
import threading

from http_server import Initialize_Server, Shutdown_Server, set_latest_frame0, set_latest_frame1, set_door_controller_reference, Fetch_Queued_Command
from ruleset_decider import RulesetDecider
from gate_states import State
from json_config import JsonConfig

import signal
import sys

def gstreamer_pipeline(
    sensor_id=0,
    capture_width=1280,
    capture_height=720,
    display_width=1280,
    display_height=720,
    framerate=5,
    flip_method=0
):
    return (
        f"nvarguscamerasrc sensor-id={sensor_id} ! "
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
    io.all_pins_off()
    GPIO.cleanup()
    Shutdown_Server(web_server)

def signal_handler(sig, frame):
    print('[+] Ctrl+C Detected... Exiting...')
    cleanup()
    sys.exit(0)

def main():
    #Global HTTP server for resource allocation and deallocation
    global web_server

    #Set up signal handler keyboard interrupt
    signal.signal(signal.SIGINT, signal_handler)

    #Initialize configuration settings for the SmartGate
    config = JsonConfig()

    #Grab respective configurations from config.json file
    model_config  = config.get_model_config() 
    rules_config  = config.get_rules_config() 
    server_config = config.get_server_config()

    #Initialize YOLOv5 model via TensorRT engine
    model = YoloTRT(model_config)

    #In the DECIDE state, the RulesetDecider will be responsible for setting the next state depending on the configuration
    decider = RulesetDecider(rules_config)

    #Start web server on a separate thread
    #Should also make the web server optional as well
    web_server = Initialize_Server(server_config)

    #Set up the GPIO channel
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(7, GPIO.OUT, initial=GPIO.LOW)

    #Initialize IO pins and door control
    io.set_all_pins()
    door_controller = DoorControl()

    #The HTTP Server would need the reference of the door_controller object to get status on each '/status' GET request
    set_door_controller_reference(door_controller)

    #Initialize State Machine
    current_state = State.IDLE

    #Initialize object detection class list
    object_list = []

    #Open both cameras using GStreamer pipeline
    cap0 = cv2.VideoCapture(gstreamer_pipeline(sensor_id=0), cv2.CAP_GSTREAMER)
    cap1 = cv2.VideoCapture(gstreamer_pipeline(sensor_id=1), cv2.CAP_GSTREAMER)
    
    #Our main loop
    while True:
        #----------Check for commands from POST requests coming from HTTP server------------
        command = Fetch_Queued_Command()
        if command:
            if command == 'OPEN_DOOR':
                current_state = State.DOOR_OPEN
            elif command == 'CLOSE_DOOR':
                current_state = State.DOOR_CLOSE

        #------------IDLE State ------------------------------------------------------------
        if current_state == State.IDLE:
            print("System is idle.")

            #Ensure the motor stops when Hall Effect sensors are detected during IDLE state
            if door_controller.is_door_fully_closed() and door_controller.is_door_closing:
                door_controller.stop_door()
                print("Door fully closed, stopping motor.")
            elif door_controller.is_door_fully_open() and door_controller.is_door_opening:
                door_controller.stop_door()
                print("Door fully open, stopping motor.")

            #On any movement, set to DETECT state which will start capturing from the camera
            if io.get_val('PIR'):
                current_state = State.DETECT
            else:
                current_state = State.IDLE #Put back to IDLE state

        #------------DETECT State ----------------------------------------------------------
        elif current_state == State.DETECT:
            print("Detecting objects.")
            ret_val0, img0 = cap0.read()
            ret_val1, img1 = cap1.read()
            if not ret_val0 or not ret_val1:
                break

            #Resize the frame for YOLOv5
            img0 = imutils.resize(img0, width=600)
            img1 = imutils.resize(img1, width=600)

            #Perform inference
            detections0, t0 = model.Inference(img0)
            detections1, t1 = model.Inference(img1)
            #Update the latest_frame for streaming
            set_latest_frame0(img0.copy())
            set_latest_frame1(img1.copy())
            object_list = [obj['class'] for obj in detections0] + [obj['class'] for obj in detections1]
            current_state = State.DECISION

        #------------DECISION State --------------------------------------------------------
        elif current_state == State.DECISION:
            print("Decision making door.")
            
            #Decide on ruleset
            current_state = decider.decide(object_list)

        #------------DOOR OPEN State -------------------------------------------------------
        elif current_state == State.DOOR_OPEN:
            print("Opening door.")

            if not door_controller.is_door_fully_open():
                door_controller.open_door()
            else:
                print('Door stopped on opening')
                door_controller.stop_door()
            
            current_state = State.IDLE

        #------------DOOR CLOSE State ------------------------------------------------------
        elif current_state == State.DOOR_CLOSE:
            print("Closing door.")

            #Read Hall Effect sensor of Door Closed. Keep closing if the Hall effect sensor is 0
            if not door_controller.is_door_fully_closed():
                door_controller.close_door()
            else:
                print('Door stopped on closing')
                door_controller.stop_door()
                
            current_state = State.IDLE

        #------------Default State --------------------
        elif current_state == State.DELAY:
            print("Delaying operation.")
    
    #Sets all pins to LOW
    io.all_pins_off()

#Main logic
if __name__ == "__main__":
    main()
