import ioControl as io
import numpy as np
import time
import cv2

reqClose = 0

io.setAllPins()

def initDoor():
    io.setVal('ENB', True)
    return True

def openDoor():
    io.setVal('IN3', False)
    io.setVal('IN4', True)
    return True

def closeDoor():
    io.setVal('IN3', True)
    io.setVal('IN4', False)
    return True

initDoor()
cv2.imshow('Frame', np.zeros(shape=[512,512,3],dtype=np.uint8))

for i in range(500):
    openDoor()
    print('Opening')
    time.sleep(0.4)
io.allPinsOff()