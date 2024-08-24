import ioControl as io
import time

def initDoor():
    io.setVal('ENB', True)
    io.setVal('IN3', False)
    io.setVal('IN4', False)
    return True

def openDoor():
    io.setVal('IN3', False)
    io.setVal('IN4', True)
    return True

def closeDoor():
    io.setVal('IN3', True)
    io.setVal('IN4', False)
    return True

def stopDoor():
    io.setVal('IN3', False)
    io.setVal('IN4', False)
    return True

# OPEN = 11, CLOSE = 13
def isDoorFullyOpen():
    hallEffectOpened = (io.getVal('OPEN') == 0 and io.getVal('CLOSE') == 1)
    return hallEffectOpened

def isDoorFullyClosed():
    hallEffectClosed = (io.getVal('OPEN') == 1 and io.getVal('CLOSE') == 0)
    return hallEffectClosed