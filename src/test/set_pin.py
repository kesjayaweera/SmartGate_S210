import sys
import Jetson.GPIO as GPIO

def set_pin_state(pin, state):
    # Set the pin numbering mode to BCM
    GPIO.setmode(GPIO.BOARD)
    
    # Set up the pin as an output
    GPIO.setup(pin, GPIO.OUT)
    
    # Set the pin to the desired state
    if state == 1:
        GPIO.output(pin, GPIO.HIGH)
        print(f"Pin {pin} set to HIGH")
    elif state == 0:
        GPIO.output(pin, GPIO.LOW)
        print(f"Pin {pin} set to LOW")
    else:
        print("Invalid state. Use 1 for HIGH or 0 for LOW.")
    
    # Clean up the GPIO settings
    #GPIO.cleanup()

if __name__ == "__main__":
    # Check for correct number of arguments
    if len(sys.argv) != 3:
        print("Usage: python script.py <pin_number> <state>")
        sys.exit(1)
    
    try:
        # Parse the command line arguments
        pin_number = int(sys.argv[1])
        state = int(sys.argv[2])
        
        # Set the pin to the desired state
        set_pin_state(pin_number, state)
        
    except ValueError:
        print("Invalid input. Please provide integer values for pin number and state.")
        sys.exit(1)
