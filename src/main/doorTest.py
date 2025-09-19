import ioControl as io
import Jetson.GPIO as GPIO
import numpy as np
import time
import cv2

reqClose = 0

io.setAllPins()

def initDoor():
    io.setVal('ENB', True)
    return True

def openDoor():
    # while not (cv2.waitKey(15) & 0xFF == ord('d')):
    #     if not io.getVal('OPEN'):
    #         break
    #     else:
    io.setVal('IN3', False)
    io.setVal('IN4', True)
    #io.setVal('IN3', False)
    #io.setVal('IN4', False)
    return True

def closeDoor():
    # while True:
    #     if not io.getVal('CLOSE'):
    #         reqClose = 0
    #         time.sleep(0.4)
    #         break
    #     else:
    io.setVal('IN3', True)
    io.setVal('IN4', False)
    #io.setVal('IN3', False)
    #io.setVal('IN4', False)
    return True

initDoor()
cv2.imshow('Frame', np.zeros(shape=[512,512,3],dtype=np.uint8))

for i in range(10):
    # if cv2.waitKey(15) & 0xFF == ord('q'):
    #     print('Terminated')
    #     break
    #elif cv2.waitKey(30) & 0xFF == ord('a'):
    closeDoor()
    print('Opening')
    time.sleep(0.2)
for i in range(10):
    openDoor()
    print("Closing")
    time.sleep(0.2)
    #elif cv2.waitKey(50) & 0xFF == ord('d'):
    #    reqClose = 1
    #    closeDoor()
    #    print('Closing')
    #else:
    #    io.setVal('IN3', False)
    #    io.setVal('IN4', False)
    #print('Open: ' + str(io.getVal('OPEN')) + ', Close: ' + str(io.getVal("CLOSE")) + ', reqClose: ' + str(reqClose))
io.allPinsOff()
GPIO.cleanup()
