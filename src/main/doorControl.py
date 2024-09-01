import ioControl as io
import time

#This class is used to set and control the state of the door of the gate

class DoorControl:
    """
    A class to manage and control the state of the gate door.
    
    This class provides methods to initialize, open, close, and stop the door movement via the Motor control board pins.
    It also includes methods to check if the door is fully open or closed using Hall Effect sensors.
    """
    def __init__(self):
        self.is_door_opening = False
        self.is_door_closing = False
        self.init_door()
    
    #Door initial state
    def init_door(self):
        io.setVal('ENB', True)
        io.setVal('IN3', False)
        io.setVal('IN4', False)
        self.is_door_opening = False
        self.is_door_closing = False
    
    #Open door
    def open_door(self):
        io.setVal('IN3', False)
        io.setVal('IN4', True)
        self.is_door_opening = True
        self.is_door_closing = False
    
    #Close door
    def close_door(self):
        io.setVal('IN3', True)
        io.setVal('IN4', False)
        self.is_door_opening = False
        self.is_door_closing = True
    
    #Stop the door
    def stop_door(self):
        io.setVal('IN3', False)
        io.setVal('IN4', False)
        self.is_door_opening = False
        self.is_door_closing = False
    
    #Check if door is fully open by checking Hall Effect sensors
    def is_door_fully_open(self):
        return io.getVal('OPEN') == 0 and io.getVal('CLOSE') == 1

    #Check if door is fully closed by checking Hall Effect sensors
    def is_door_fully_closed(self):
        return io.getVal('OPEN') == 1 and io.getVal('CLOSE') == 0
