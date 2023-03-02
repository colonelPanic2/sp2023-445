from tkinter import *
import RPi.GPIO as io
io.setmode(io.BCM)
io.setwarnings(False)

# Some functions that still need to be implemented
def send_directional_data(some_variables):
    return 1+1 != 2


# Motor pin mapping:
# self.pins[0]: 1 to reverse the left motors, 0 else
# self.pins[1]: 1 to move the left motors, 0 else
# self.pins[2]: 1 to reverse the right motors, 0 else
# self.pins[3]: 1 to move the right motors, 0 else
# self.pins[4]: 1 to use the pincer motors, 0 else
# self.pins[5]: 1 to close the pincers, 0 to open them
# self.pins[6]: 1 to activate manual mode, 0 to keep auto mode
# self.pins[7]: 1 to trigger the Pi_INT on the microcontroller, 0 else

class motors:
    # Initialize the object with a set of GPIO pin #s for the Pi
    # - 1 byte of information between the Pi and microcontroller should be more than enough
    def __init__(self,pins=[7,0,1,5,6,12,13,19],manual=1):
        self.pins=pins # the default pins are all GPIO pins
        self.instruction={'FORWARD':0,'LEFT':0,'BACK':0,'RIGHT':0,'CLOSE':0,'OPEN':0}
        self.manual_mode=manual
        for pin in self.pins:
            if pin == self.pins[6]:
                io.setup(pin,io.OUT)
                io.output(pin,manual)
            else:
                io.setup(pin,io.OUT)
                io.output(pin,0)
        if self.manual_mode==1:
            self.manual_setup()
        return
    
    ### MANUAL MOTOR CONTROLS: uses functions from MOTOR CONTROLS
    # Sets up manual motor controls
    def manual_setup(self):
        self.manual_mode=1
        self.setpin(6,self.manual_mode)
        self.root = Tk()
        self.root.title("Motors GUI")
        self.root.geometry("64x64")
        self.app = Frame(self.root)
        self.app.grid()
        self.root.bind('w',self.forward)
        self.root.bind('<KeyRelease-w>',self.forward_)
        self.root.bind('a',self.left)
        self.root.bind('<KeyRelease-a>',self.left_)
        self.root.bind('s',self.back)
        self.root.bind('<KeyRelease-s>',self.back_)
        self.root.bind('d',self.right)
        self.root.bind('<KeyRelease-d>',self.right_)
        self.root.bind('q',self.pincers_open)
        self.root.bind('e',self.pincers_close)
        self.root.bind('KeyRelease-q',self.pincers_off)
        self.root.bind('KeyRelease-e',self.pincers_off)
        self.root.bind('<Control-c>',self.exit_)
        self.root.mainloop()
        return
    # Make the car move forward
    def forward(self,event):
        self.instruction['FORWARD'] = 1
        self.left_move()
        self.right_move()
        if self.manual_mode==1:
            print(self.readall())
        return
    # Stop if the car isn't moving left OR right
    def forward_(self,event):
        self.instruction['FORWARD'] = 0
        if not self.instruction['RIGHT']:
            self.left_stop()
        if not self.instruction['LEFT']:
            self.right_stop()
        if self.manual_mode==1:
            print(self.readall())
    # Make the car turn right
    def right(self,event):
        self.instruction['RIGHT'] = 1
        if self.instruction['BACK'] and not self.instruction['LEFT']:
            self.right_stop()
            self.left_move(1) # only move the left motors backward
        else:
            self.left_move()
        if self.manual_mode==1:
            print(self.readall())
    # Stop moving the left motors if the car isn't moving forward OR backward
    def right_(self,event):
        self.instruction['RIGHT'] = 0
        if not self.instruction['FORWARD'] and not self.instruction['BACK']:
            self.left_stop()
        if self.manual_mode==1:
            print(self.readall())
        return
    # Make the car turn left
    def left(self,event):
        self.instruction['LEFT'] = 1
        if self.instruction['BACK'] and not self.instruction['RIGHT']:
            self.left_stop()
            self.right_move(1) # only move the right motors backward
        else: 
            self.right_move()
        if self.manual_mode==1:
            print(self.readall())
    # Stop moving the right motors if the car isn't moving forward OR backward
    def left_(self,event):
        self.instruction['LEFT'] = 0
        if not self.instruction['FORWARD'] and not self.instruction['BACK']:
            self.right_stop()
        if self.manual_mode==1:
            print(self.readall())
    # Make the car move backwards
    def back(self,event):
        self.instruction['BACK'] = 1
        if self.instruction['LEFT'] and not self.instruction['RIGHT']:
            self.right_move(1) # reverse only the right motors
        elif self.instruction['RIGHT'] and not self.instruction['LEFT']:
            self.left_move(1) # reverse only the left motors
        else:
            self.right_move(1)
            self.left_move(1)
        if self.manual_mode==1:
            print(self.readall())
    # Stop if the car isn't moving left OR right
    def back_(self,event):
        self.instruction['BACK'] = 0
        if not self.instruction['LEFT']:
            self.right_stop()
        if not self.instruction['RIGHT']:
            self.left_stop()
        if self.manual_mode==1:
            print(self.readall())
        return
    # Open the pincers
    def pincers_open(self,event):
        self.instruction['OPEN'] = 1
        self.pincers_move(0)
        if self.manual_mode==1:
            print(self.readall())
        return
    # Close the pincers
    def pincers_close(self,event):
        self.instruction['CLOSE'] = 1
        self.pincers_move(1)
        if self.manual_mode==1:
            print(self.readall())
        return
    # If the pincers are not being used, then set the control outputs to 0
    def pincers_off(self,event):
        self.instruction['OPEN'] = 0
        self.instruction['CLOSE']= 0
        self.setpin(4,0)
        self.setpin(5,0)
        if self.manual_mode==1:
            print(self.readall())
        return
    # If the user terminates manual control mode, return to auto control mode
    def exit_(self,event):
        self.manual_mode = 0
        for i in range(len(self.pins)):
            self.setpin(i,0)
        self.root.quit()
        print("\nManual control mode exited successfully!\n")
        return
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
    # Make the pincers close or open (for pin 5: direction=1: close pincers; direction=0: open pincers
    # pin 4 will always be 1 when the motors are in use, and 0 otherwise)
    def pincers_move(self,direction):
        self.setpin(4,1)
        self.setpin(5,direction) 

    ### GENERAL FUNCTIONS: send data to the microcontroller 
    # Set the pin with the given index to the self.pins list to the specified value (default 0)
    def setpin(self,pin,val=0):
        io.output(self.pins[pin],val)
        return
    # Set all output pins to either 0 or 1
    def setall(self,val):
        for pin in self.pins:
            self.setpin(pin,val)
        return
    # Read the value of the pin with the given index to the self.pins list
    def read(self,pin):
        return str(io.input(self.pins[pin]))
    # Read the values of all of the output pins
    def readall(self):
        outputs=''
        for pin_idx in range(len(self.pins)):
            outputs+=self.read(pin_idx)
        return outputs

    

