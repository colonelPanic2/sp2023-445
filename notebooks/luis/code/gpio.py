import time
from tkinter import *
from helpers.helpers import writefile,platform,clear,time_data
try: 
    import RPi.GPIO as io
except:
    from helpers.helpers import  io
from signal import raise_signal,SIGUSR1, SIGUSR2


# Control pin mapping:
# self.pins[0]: 1 to reverse the left motors, 0 else
# self.pins[1]: 1 to move the left motors, 0 else
# self.pins[2]: 1 to reverse the right motors, 0 else
# self.pins[3]: 1 to move the right motors, 0 else
# self.pins[4]: 1 to use the pincer motors, 0 else
# self.pins[5]: 1 to close the pincers, 0 to open them
# self.pins[6]: 1 to activate manual mode, 0 to keep auto mode
# self.pins[7]: 1 to trigger the Pi_INT on the microcontroller, 0 else
class control:
    # Initialize the object with a set of GPIO pin #s for the Pi
    def __init__(self,gettimes,noprint,demo,manual,init_time,logfile):
        self.gettimes=gettimes
        self.noprint=noprint
        self.demo=demo
        self.manual=manual
        self.init_time=init_time
        self.logfile = logfile
        self.pins=[7,0,1,5,6,12,13,19, 16,26] # the default pins are all GPIO pins
        self.instruction={'CAMSWITCH':0,'FORWARD':0,'LEFT':0,'BACK':0,'RIGHT':0,'CLOSE':0,'OPEN':0,'CLEAR':0,'SIGUSR1':0,'SIGUSR2':0}
        self.INT_start_time = 0
        self.proximity = 0
        self.DONE = False
        # If gettimes=='time', then set up for runtime data collection
        # for each of the state function loops
        time_data(gettimes,'',0)
        io.setmode(io.BCM)
        io.setwarnings(False)
        for pin in self.pins:
            if pin == self.pins[6]:
                io.setup(pin, io.OUT)
                io.output(pin,int(manual!=0))
            else:
                io.setup(pin, io.OUT)
                io.output(pin,0)
        # NOTE: UNTESTED MICROCONTROLLER COMMS CODE
        io.setup(self.pins[8],io.IN,pull_up_down=io.PUD_DOWN)
        io.add_event_detect(self.pins[8],io.RISING,callback=self.callback_SIGUSR1)
        io.setup(self.pins[9],io.IN,pull_up_down=io.PUD_DOWN)
        io.add_event_detect(self.pins[9],io.RISING,callback=self.callback_SIGUSR2)
        return
    def init_manual_control(self,cam):
        print(f"WARNING: YOU ARE CURRENTLY IN MANUAL CONTROL MODE.\n\
         While in manual control mode, the fetching subsystem is inactive.\n\
         However, the camera's input to the fetching subsystem is visible.\n\
         The small, blank window represents the input manual input to the \n\
         control subsystem. Click on this window and press the Q,W,E,A,S,D\n\
         keys in order to issue orders to the control subsystem. The region\n\
         currently occupied by the ball and the time that the ball has spent\n\
         in that region can be seen in the terminal. You can clear the text\n\
         in the terminal by pressing 'l', and you can switch cameras by\n\
         pressing 'c'. YOU MUST HAVE AT LEAST 2 CAMERAS CONNECTED TO YOUR\n\
         COMPUTER WHEN TRYING TO SWITCH CAMERAS, OR THE PROGRAM WILL CRASH.\n\n\
         Pressing CTRL+C in either the blank window or the terminal will\n\
         exit manual control mode and switch to auto control mode, which\n\
         is where the fetching subsystem is used. In auto mode, more \n\
         outputs information about the state of the program, such as state, \n\
         will be written to {self.logfile}. The timing data visible in the\n\
         terminal during manual control mode will be visible, in auto control\n\
         mode, but only when the FSM is in the 'WAIT' state.\n\n\
         In order to completely end the program, press CTRL+C in the\n\
         terminal or 'q' in the 'Camera' window.\n\n")
        self.cam = cam
        self.cam.start_read()
        self.manual_setup()
    # NOTE: UNTESTED MICROCONTROLLER COMMS CODE (needs to be fully implemented)
    def callback_SIGUSR1(self,channel): 
        raise_signal(SIGUSR1)
    def callback_SIGUSR2(self,channel):
        raise_signal(SIGUSR2)
        # Show the camera view in a window while in manual control mode.
    def video_update(self):
        try:
            self.cam.update_goal_position('ball',time.time())
            self.root.after(25,self.video_update) # Call this function every 25ms
        except KeyboardInterrupt:
            self.manual = 0
            for i in range(len(self.pins)):
                self.setpin(i,0)
            writefile(self.logfile,"Exiting manual controls.\nFinal output: "+self.readall()+'\n')
            self.root.destroy()
            writefile(self.logfile,"\nManual control mode exited successfully!\n\n")
    ### MANUAL MOTOR CONTROLS: uses functions from MOTOR CONTROLS
    # Sets up manual motor controls
    def manual_setup(self):
        # TODO: MODIFY TO ALLOW THE 'SIGUSR1' AND 'SIGUSR2' SIGNALS TO BE GENERATED 
        # MANUALLY BY THE USER TO SIMPLIFY DEBUGGING OF THE HANDLERS FOR THE 
        # MICROCONTROLLER'S INPUT TO THE PI. 
        self.root = Tk()
        self.setpin(6,1)
        self.root.title("Motors GUI")
        self.root.geometry("64x64")
        self.app = Frame(self.root)
        self.app.grid()
        self.root.bind('c',self.camswitch)
        self.root.bind('<KeyRelease-c>',self.camswitch_)
        self.root.bind('w',self.forward)
        self.root.bind('<KeyRelease-w>',self.forward_)
        self.root.bind('a',self.left)
        self.root.bind('<KeyRelease-a>',self.left_)
        self.root.bind('s',self.back)
        self.root.bind('<KeyRelease-s>',self.back_)
        self.root.bind('d',self.right)
        self.root.bind('<KeyRelease-d>',self.right_)
        self.root.bind('q',self.pincers_open)
        self.root.bind('<KeyRelease-q>',self.pincers_off_open)
        self.root.bind('e',self.pincers_close)
        self.root.bind('<KeyRelease-e>',self.pincers_off_close)
        self.root.bind('<Control-c>',self.exit_)
        self.root.bind('<l>',self.clear_terminal)
        self.root.bind('<Key-1>',self.callback_SIGUSR1_helper)
        self.root.bind('<Key-2>',self.callback_SIGUSR2_helper)
        if self.demo:
            self.video_update()
        self.root.mainloop()
        return
    # Prove the ability to record response time data for the microcontroller
    # If time data isn't being collected, then this just changes self.DONE 
    # to 'True' and then back to 'False', which does nothing without the FSM.
    def callback_SIGUSR1_helper(self,channel):
        self.clear_terminal()
        self.callback_SIGUSR1(channel)
        self.DONE=False
        return
    # Change the proximity attribute (something is within range of the ultrasonic sensors)
    def callback_SIGUSR2_helper(self,channel):
        self.clear_terminal()
        self.callback_SIGUSR2(channel)
    def camswitch(self,event=None):
        if self.instruction['CAMSWITCH']==0:
            self.cam.camera_.camswitch()
        self.instruction['CAMSWITCH']=1
    def camswitch_(self,event=None):
        self.instruction['CAMSWITCH']=0
    # Make the car move forward
    def forward(self,event=None):
        if self.instruction['FORWARD']==1:
            return
        self.clear_terminal()
        if self.cam.index==0:
            self.left_move()
            self.right_move()
        else: 
            self.left_move(1)
            self.right_move(1)
        self.INT_start_time = time.time()
        self.setpin(7,1)
        if self.manual!=0 and self.instruction['FORWARD']==0:
            # writefile(self.logfile,self.readall()[:-3]+" "+self.read(7)+' ')
            print(self.readall()[:-3]+" "+self.read(7),end=' ')
        #time.sleep(0.005)
        self.setpin(7,0)
        if self.manual!=0 and self.instruction['FORWARD']==0:
            # writefile(self.logfile,self.read(7)+"\n")
            print(self.read(7))
        self.instruction['FORWARD'] = 1
        #raise_signal(SIGUSR1)
        return
    # Stop if the car isn't moving left OR right
    def forward_(self,event=None):
        # self.clear_terminal()
        self.setpin(7,0)
        self.instruction['FORWARD'] = 0
        if not self.instruction['RIGHT']:
            self.left_stop()
        if not self.instruction['LEFT']:
            self.right_stop()
        self.INT_start_time = time.time()
        self.setpin(7,1)
        if self.manual!=0 and self.instruction['FORWARD']==0:
            # writefile(self.logfile,self.readall()[:-3]+" "+self.read(7)+' ')
            print(self.readall()[:-3]+" "+self.read(7),end=' ')
        #time.sleep(0.005)
        self.setpin(7,0)
        if self.manual!=0 and self.instruction['FORWARD']==0:
            # writefile(self.logfile,self.read(7)+'\n')
            print(self.read(7))
        #raise_signal(SIGUSR1)
        return
    # Make the car turn right
    def right(self,event=None):
        if self.instruction['RIGHT']==1:
            return
        self.clear_terminal()
        if self.cam.index==0:
            if self.instruction['BACK'] and not self.instruction['LEFT']:
                self.right_stop()
                self.left_move(1) # only move the left motors backward
            else:
                self.left_move()
        else:
            if self.instruction['BACK'] and not self.instruction['LEFT']:
                self.left_stop()
                self.right_move() # only move the 'left' motors 'backward'
            else:
                self.right_move(1)            
        self.INT_start_time = time.time()
        self.setpin(7,1)
        if self.manual!=0 and self.instruction['RIGHT']==0:
            # writefile(self.logfile,self.readall()[:-3]+" "+self.read(7)+' ')
            print(self.readall()[:-3]+" "+self.read(7),end=' ')
        #time.sleep(0.005)
        self.setpin(7,0)
        if self.manual!=0 and self.instruction['RIGHT']==0:
            # writefile(self.logfile,self.read(7)+'\n')
            print(self.read(7))
        self.instruction['RIGHT'] = 1
        #raise_signal(SIGUSR1)
        return
    # Stop moving the left motors if the car isn't moving forward OR backward
    def right_(self,event=None):
        # self.clear_terminal()
        self.instruction['RIGHT'] = 0
        if not self.instruction['FORWARD'] and not self.instruction['BACK']:
            if self.cam.index==0:
                self.left_stop()
            else:
                self.right_stop()
            self.INT_start_time = time.time()
        self.setpin(7,1)
        if self.manual!=0 and self.instruction['RIGHT']==0:
            # writefile(self.logfile,self.readall()[:-3]+" "+self.read(7)+' ')
            print(self.readall()[:-3]+" "+self.read(7),end=' ')
        #time.sleep(0.005)
        self.setpin(7,0)
        if self.manual!=0 and self.instruction['RIGHT']==0:
            # writefile(self.logfile,self.read(7)+'\n')
            print(self.read(7))
        #raise_signal(SIGUSR1)
        return
    # Make the car turn left
    def left(self,event=None):
        if self.instruction['LEFT']==1:
            return
        self.clear_terminal()
        if self.cam.index==0:
            if self.instruction['BACK'] and not self.instruction['RIGHT']:
                self.left_stop()
                self.right_move(1) # only move the right motors backward
            else: 
                self.right_move()
        else:
            if self.instruction['BACK'] and not self.instruction['RIGHT']:
                self.right_stop()
                self.left_move() # only move the 'right' motors 'backward'
            else: 
                self.left_move(1)            
        self.INT_start_time = time.time()
        self.setpin(7,1)
        if self.manual!=0 and self.instruction['LEFT']==0:
            # writefile(self.logfile,self.readall()[:-3]+" "+self.read(7)+' ')
            print(self.readall()[:-3]+" "+self.read(7),end=' ')
        #time.sleep(0.005)
        self.setpin(7,0)
        if self.manual!=0 and self.instruction['LEFT']==0:
            # writefile(self.logfile,self.read(7)+'\n')
            print(self.read(7))
        self.instruction['LEFT'] = 1
        #raise_signal(SIGUSR1)
        return
    # Stop moving the right motors if the car isn't moving forward OR backward
    def left_(self,event=None):
        # self.clear_terminal()
        self.instruction['LEFT'] = 0
        if not self.instruction['FORWARD'] and not self.instruction['BACK']:
            if self.cam.index==0:
                self.right_stop()
            else:
                self.left_stop()
            self.INT_start_time = time.time()
        self.setpin(7,1)
        if self.manual!=0 and self.instruction['LEFT']==0:
            # writefile(self.logfile,self.readall()[:-3] + " " + self.read(7)+' ')
            print(self.readall()[:-3]+" "+self.read(7),end=' ')
        #time.sleep(0.005)
        self.setpin(7,0)
        if self.manual!=0 and self.instruction['LEFT']==0:
            # writefile(self.logfile,self.read(7)+'\n')
            print(self.read(7))
        #raise_signal(SIGUSR1)
        return
    # Make the car move backwards
    def back(self,event=None):
        if self.instruction['BACK']==1:
            return
        self.clear_terminal()
        if self.cam.index==0:
            if self.instruction['LEFT'] and not self.instruction['RIGHT']:
                self.right_move(1) # reverse only the right motors
            elif self.instruction['RIGHT'] and not self.instruction['LEFT']:
                self.left_move(1) # reverse only the left motors
            else:
                self.right_move(1)
                self.left_move(1)
        else:
            if self.instruction['LEFT'] and not self.instruction['RIGHT']:
                self.left_move() # 'reverse' only the 'right' motors
            elif self.instruction['RIGHT'] and not self.instruction['LEFT']:
                self.right_move() # 'reverse' only the 'left' motors
            else:
                self.right_move()
                self.left_move()            
        self.INT_start_time = time.time()
        self.setpin(7,1)
        if self.manual!=0 and self.instruction['BACK']==0:
            # writefile(self.logfile,self.readall()[:-3]+" "+self.read(7)+' ')
            print(self.readall()[:-3]+" "+self.read(7),end=' ')
        #time.sleep(0.005)
        self.setpin(7,0)
        if self.manual!=0 and self.instruction['BACK']==0:
            # writefile(self.logfile,self.read(7)+'\n')
            print(self.read(7))
        self.instruction['BACK'] = 1
        #raise_signal(SIGUSR1)
        return
    # Stop if the car isn't moving left OR right
    def back_(self,event=None):
        # self.clear_terminal()
        self.setpin(7,0)
        self.instruction['BACK'] = 0
        if not self.instruction['LEFT']:
            self.right_stop()
        if not self.instruction['RIGHT']:
            self.left_stop()
        self.INT_start_time = time.time()
        self.setpin(7,1)
        if self.manual!=0 and self.instruction['BACK']==0:
            # writefile(self.logfile,self.readall()[:-3]+" "+self.read(7)+' ')
            print(self.readall()[:-3]+" "+self.read(7),end=' ')
        #time.sleep(0.005)
        self.setpin(7,0)
        if self.manual!=0 and self.instruction['BACK']==0:
            # writefile(self.logfile,self.read(7)+'\n')
            print(self.read(7))
        #raise_signal(SIGUSR1)
        return
    # Open the pincers
    def pincers_open(self,event=None):
        if self.instruction['OPEN']==1:
            return
        self.clear_terminal()
        if self.instruction['CLOSE']==0:
            self.pincers_move(0)
            self.INT_start_time = time.time()
        self.setpin(7,1)
        if self.manual!=0 and self.instruction['OPEN']==0:
            # writefile(self.logfile,self.readall()[:-3]+" "+self.read(7)+' ')
            print(self.readall()[:-3]+" "+self.read(7),end=' ')
        #time.sleep(0.005)
        self.setpin(7,0)
        if self.manual!=0 and self.instruction['OPEN']==0:
            # writefile(self.logfile,self.read(7)+'\n')
            print(self.read(7))
        self.instruction['OPEN'] = 1
        #raise_signal(SIGUSR1)
        return
    # Close the pincers
    def pincers_close(self,event=None):
        if self.instruction['CLOSE']==1:
            return
        self.clear_terminal()
        if self.instruction['OPEN']==0:
            self.pincers_move(1)
            self.INT_start_time = time.time()
        self.setpin(7,1)
        if self.manual!=0 and self.instruction['CLOSE']==0:
            # writefile(self.logfile,self.readall()[:-3]+" "+self.read(7)+' ')
            print(self.readall()[:-3]+" "+self.read(7),end=' ')
        #time.sleep(0.005)
        self.setpin(7,0)
        if self.manual!=0 and self.instruction['CLOSE']==0:
            # writefile(self.logfile,self.read(7)+'\n')
            print(self.read(7))
        self.instruction['CLOSE'] = 1  
        #raise_signal(SIGUSR1)
        return
    # If the pincers are not being used, then set the control outputs to 0
    def pincers_off_open(self,event=None):
        # self.clear_terminal()
        self.instruction['OPEN'] = 0
        if self.instruction['CLOSE']==0:
            self.setpin(4,0)
            self.setpin(5,0)
        self.INT_start_time = time.time()
        self.setpin(7,1)
        if self.manual!=0:
            # writefile(self.logfile,self.readall()[:-3]+" "+self.read(7)+' ')
            print(self.readall()[:-3]+" "+self.read(7),end=' ')
        #time.sleep(0.005)
        self.setpin(7,0)
        if self.manual!=0:
            # writefile(self.logfile,self.read(7)+'\n')
            print(self.read(7))
        #raise_signal(SIGUSR1)
        return
    def pincers_off_close(self,event=None):
        # self.clear_terminal()
        self.instruction['CLOSE'] = 0
        if self.instruction['OPEN']==0:
            self.setpin(4,0)
            self.setpin(5,0)
        self.INT_start_time = time.time()
        self.setpin(7,1)
        if self.manual!=0:
            # writefile(self.logfile,self.readall()[:-3]+" "+self.read(7)+' ')
            print(self.readall()[:-3]+" "+self.read(7),end=' ')
        #time.sleep(0.005)
        self.setpin(7,0)
        if self.manual!=0:
            # writefile(self.logfile,self.read(7)+'\n')
            print(self.read(7))
        #raise_signal(SIGUSR1)
        return
    # If the user terminates manual control mode, return to auto control mode
    def exit_(self,event=None):
        self.manual = 0
        for i in range(len(self.pins)):
            self.setpin(i,0)
        writefile(self.logfile,"Exiting manual controls.\nFinal output: "+self.readall()+'\n')
        print("Exiting manual controls.\nFinal output: "+self.readall())
        self.root.destroy()
        writefile(self.logfile,"Manual control mode exited successfully!\n\n")
        print("Manual control mode exited successfully!\n\n")
        
    ### MOTOR CONTROLS: use functions from the GENERAL FUNCTIONS to set output signals
    # Make the left motors move forward (reverse=0) or backward (reverse=1).
    def pi_int(self):
        self.INT_start_time = time.time()
        self.setpin(7,1)
        # NOTE: Wait 5 ms for the microcontroller to handle the interrupt.
        # This value may need to be adjusted later.
        #time.sleep(0.005) 
        self.setpin(7,0)
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
    def pincers_move(self,direction=0):
        self.setpin(4,1)
        self.setpin(5,direction) 
    # Turn off the pincer motors
    def pincers_stop(self):
        self.setpin(4,0)
        self.setpin(5,0)
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
    def clear_terminal(self,event=None):
        clear()
        print(f"WARNING: YOU ARE CURRENTLY IN MANUAL CONTROL MODE.\n\
         While in manual control mode, the fetching subsystem is inactive.\n\
         However, the camera's input to the fetching subsystem is visible.\n\
         The small, blank window represents the input manual input to the \n\
         control subsystem. Click on this window and press the Q,W,E,A,S,D\n\
         keys in order to issue orders to the control subsystem. The region\n\
         currently occupied by the ball and the time that the ball has spent\n\
         in that region can be seen in the terminal. You can clear the text\n\
         in the terminal by pressing 'l', and you can switch cameras by\n\
         pressing 'c'. YOU MUST HAVE AT LEAST 2 CAMERAS CONNECTED TO YOUR\n\
         COMPUTER WHEN TRYING TO SWITCH CAMERAS, OR THE PROGRAM WILL CRASH.\n\n\
         Pressing CTRL+C in either the blank window or the terminal will\n\
         exit manual control mode and switch to auto control mode, which\n\
         is where the fetching subsystem is used. In auto mode, more \n\
         outputs information about the state of the program, such as state, \n\
         will be written to {self.logfile}. The timing data visible in the\n\
         terminal during manual control mode will be visible, in auto control\n\
         mode, but only when the FSM is in the 'WAIT' state.\n\n\
         In order to completely end the program, press CTRL+C in the\n\
         terminal or 'q' in the 'Camera' window.\n\n")


    

