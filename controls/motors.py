import RPi.GPIO as gpio
gpio.setmode(gpio.BOARD)
gpio.setwarnings(False)

# Pin mapping:
# self.pins[0]: 1 to reverse the left motors, 0 else
# self.pins[1]: 1 to move the left motors, 0 else
# self.pins[2]: 1 to reverse the right motors, 0 else
# self.pins[3]: 1 to move the right motors, 0 else
# self.pins[4:8]: UNDEFINED

class GPIO:
    # Initialize the object with a set of GPIO pin #s for the Pi
    # - 1 byte of information between the Pi and microcontroller should be more than enough
    def __init__(self,pins=[26,27,28,29,31,33,35,37]):
        self.pins=pins # the default pins are all GPIO pins
        for pin in self.pins:
            gpio.setup(pin,gpio.OUT)
            gpio.output(pin,0)
        return
    
    ### MOTOR CONTROLS: use functions from the GENERAL FUNCTIONS
    # Make the left motors move forward (reverse=0) or backward (reverse=1).
    def left_move(self,reverse=0):
        self.setpin(0,reverse)
        self.setpin(1,1)
    # Make the left motors stop
    def left_stop(self):
        self.setpin(1,0)
    # Make the right motors move forward (reverse=0) or backward (reverse=1).
    def right_move(self,reverse=0):
        self.setpin(2,reverse)
        self.setpin(3,1)
    # Make the right motors stop
    def right_stop(self):
        self.setpin(3,0)

    ### GENERAL FUNCTIONS: send data to the microcontroller 
    # Set the pin with the given index to the self.pins list to the specified value (default 0)
    def setpin(self,pin,val=0):
        gpio.output(self.pins[pin],val)
        return
    # Set all output pins to either 0 or 1
    def setall(self,val):
        for pin in self.pins:
            self.setpin(pin,val)
        return
    # Read the value of the pin with the given index to the self.pins list
    def read(self,pin):
        return gpio.input(self.pins[pin])
    # Read the values of all of the output pins
    def readall(self):
        outputs=''
        for pin in self.pins:
            outputs+=str(self.read(pin))
        return outputs

    
