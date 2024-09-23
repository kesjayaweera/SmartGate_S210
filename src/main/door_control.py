import io_control as io
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
        io.set_val('ENB', True)
        io.set_val('IN3', False)
        io.set_val('IN4', False)
        self.is_door_opening = False
        self.is_door_closing = False
    
    #Open door
    def open_door(self):
        if not self.is_door_opening:
            io.set_val('IN3', False)
            io.set_val('IN4', True)
            self.is_door_opening = True
            self.is_door_closing = False
            print("Door opening started.")
        else:
            print("Door is already opening.")
    
    #Close door
    def close_door(self):
        if not self.is_door_closing:
            io.set_val('IN3', True)
            io.set_val('IN4', False)
            self.is_door_opening = False
            self.is_door_closing = True
        else:
            print("Door is already closing.")
    
    #Stop the door
    def stop_door(self):
        io.set_val('IN3', False)
        io.set_val('IN4', False)
        self.is_door_opening = False
        self.is_door_closing = False
    
    #Check if door is fully open by checking Hall Effect sensors
    def is_door_fully_open(self):
        return io.get_val('OPEN') == 0 and io.get_val('CLOSE') == 1

    #Check if door is fully closed by checking Hall Effect sensors
    def is_door_fully_closed(self):
        return io.get_val('OPEN') == 1 and io.get_val('CLOSE') == 0
