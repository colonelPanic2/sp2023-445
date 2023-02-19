from tkinter import *
import RPi.GPIO as gpio
gpio.setmode(gpio.BCM)
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
    def __init__(self,pins=[7,0,1,5,6,12,13,19]):
        self.pins=pins # the default pins are all GPIO pins
        self.pressed={'w':0,'a':0,'s':0,'d':0}
        for pin in self.pins:
            gpio.setup(pin,gpio.OUT)
            gpio.output(pin,0)

        self.root = Tk()
        self.root.title("Motors GUI")
        self.root.geometry("64x64")
        self.app = Frame(self.root)
        self.app.grid()
        # button0=Button(app,text="Forward")
        # button0.bind("<Button-1>",forward)
        # button0.grid()
        self.root.bind('w',self.forward)
        self.root.bind('<KeyRelease-w>',self.forward_)
        self.root.bind('a',self.left)
        self.root.bind('<KeyRelease-a>',self.left_)
        self.root.bind('s',self.back)
        self.root.bind('<KeyRelease-s>',self.back_)
        self.root.bind('d',self.right)
        self.root.bind('<KeyRelease-d>',self.right_)
        self.root.bind('<Control-c>',exit)
        self.root.mainloop()
        return
    
    ### USER MOTOR CONTROLS: use functions from MOTOR CONTROLS
    # Make the car move forward
    def forward(self,event):
        self.pressed['w'] = 1
        self.left_move()
        self.right_move()
        print(self.readall())
        return
    # Stop if the car isn't moving left OR right
    def forward_(self,event):
        self.pressed['w'] = 0
        if not self.pressed['d']:
            self.left_stop()
        if not self.pressed['a']:
            self.right_stop()
        print(self.readall())
    # Make the car turn right
    def right(self,event):
        self.pressed['d'] = 1
        if self.pressed['s'] and not self.pressed['a']:
            self.right_stop()
            self.left_move(1) # only move the left motors backward
        else:
            self.left_move()
        print(self.readall())
    # Stop moving the left motors if the car isn't moving forward OR backward
    def right_(self,event):
        self.pressed['d'] = 0
        if not self.pressed['w'] and not self.pressed['s']:
            self.left_stop()
        print(self.readall())
        return
    # Make the car turn left
    def left(self,event):
        self.pressed['a'] = 1
        if self.pressed['s'] and not self.pressed['d']:
            self.left_stop()
            self.right_move(1) # only move the right motors backward
        else: 
            self.right_move()
        print(self.readall())
    # Stop moving the right motors if the car isn't moving forward OR backward
    def left_(self,event):
        self.pressed['a'] = 0
        if not self.pressed['w'] and not self.pressed['s']:
            self.right_stop()
        print(self.readall())
    # Make the car move backwards
    def back(self,event):
        self.pressed['s'] = 1
        if self.pressed['a'] and not self.pressed['d']:
            self.right_move(1) # reverse only the right motors
        elif self.pressed['d'] and not self.pressed['a']:
            self.left_move(1) # reverse only the left motors
        else:
            self.right_move(1)
            self.left_move(1)
        print(self.readall())
    # Stop if the car isn't moving left OR right
    def back_(self,event):
        self.pressed['s'] = 0
        if not self.pressed['a']:
            self.right_stop()
        if not self.pressed['d']:
            self.left_stop()
        print(self.readall())

    ### MOTOR CONTROLS: use functions from the GENERAL FUNCTIONS to set output signals
    # Make the left motors move forward (reverse=0) or backward (reverse=1).
    def left_move(self,reverse=0):
        self.setpin(0,reverse)
        self.setpin(1,1)
    # Make the left motors stop
    def left_stop(self):
        self.setpin(0,0)
        self.setpin(1,0)
    # Make the right motors move forward (reverse=0) or backward (reverse=1).
    def right_move(self,reverse=0):
        self.setpin(2,reverse)
        self.setpin(3,1)
    # Make the right motors stop
    def right_stop(self):
        self.setpin(2,0)
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
        return str(gpio.input(self.pins[pin]))
    # Read the values of all of the output pins
    def readall(self):
        outputs=''
        for pin_idx in range(len(self.pins)):
            outputs+=self.read(pin_idx)
        return outputs

    

