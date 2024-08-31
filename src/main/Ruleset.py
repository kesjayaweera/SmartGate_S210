#This module implements a rule-based decision system for controlling the next state in the state machine for the gate
#It will read from a JSON file that has the rules set accordingly
import json
from GateStates import State

class RulesetDecider:
    def __init__(self, config_path='../../config/config.json'):
        self.config_path = config_path
        self.rules = self.load_rules()

    def load_rules(self):
        with open(self.config_path, 'r') as file:
            return json.load(file)

    def decide(self, objectList: list):
        #Check the rules accordingly and set the state
        open_detected  = False
        close_detected = False
        open_objects   = []
        close_objects  = []

        for rule in self.rules['rules']:
            for obj in objectList:
                if obj in rule['objects']:
                    if rule['action'] == 'OPEN':
                        open_detected = True
                        open_objects.append(obj)
                    elif rule['action'] == 'CLOSE':
                        close_detected = True
                        close_objects.append(obj)

        #Decision Logic
        if close_detected and open_detected:
            return State.DOOR_CLOSE
        elif open_detected:
            return State.DOOR_OPEN
        elif close_detected:
            return State.DOOR_CLOSE
        
        return State.IDLE