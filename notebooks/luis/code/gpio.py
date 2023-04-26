import time,signal
from tkinter import *
from helpers.helpers import writefile,platform,clear,time_data,decode_signal
import RPi.GPIO as io
from numpy import inf
print("Imported gpio library")
# from helpers.helpers import  io
# print("imported helpers")
from signal import SIGUSR1, SIGUSR2, SIGINT, SIG_IGN, signal
from os import getpid, kill
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
    def __init__(self,gettimes,noprint,demo,manual,init_time,logfile,num_samples):
        self.cam=None
        self.gettimes=gettimes
        self.noprint=noprint
        self.demo=demo
        self.manual=manual
        self.init_time=init_time
        self.logfile = logfile
        self.pins = [17,27,12,13,4,25,5,6,16,26,18,24, 20,21]
        self.instruction=0
        self.INT_start_time = 0
        self.proximity = 0
        self.DONE = False
        self.flag_sent = 1
        io.setmode(io.BCM)
        io.setwarnings(False) # NOTE: COMMENT THIS OUT WHEN DEBUGGING THE GPIO PINS
        for pin in self.pins[:8]:
            if pin == self.pins[6]:
                io.setup(pin, io.OUT)
                io.output(pin,int(manual!=0))
            else:
                io.setup(pin, io.OUT)
                io.output(pin,0)
        self.setpin(7,1)
        time.sleep(0.05)
        self.setpin(7,0)
        io.setup(self.pins[8],io.IN)
        io.add_event_detect(self.pins[8],io.RISING,callback=self.callback_SIGUSR1)
        io.setup(self.pins[9],io.IN)
        io.add_event_detect(self.pins[9],io.RISING,callback=self.callback_SIGUSR2,bouncetime=2)
        io.setup(self.pins[10],io.OUT)
        io.setup(self.pins[11],io.IN)
        io.setup(self.pins[12],io.OUT)
        io.setup(self.pins[13],io.IN)
        return
    def send_flag(self):
        self.setpin(4,0)
        self.setpin(5,1)
        self.pi_int()
    def distance_front(self):    
        self.setpin(10,1)
        time.sleep(0.00001)
        self.setpin(10,0)
        t_0 = time.perf_counter()
        t_start = time.time()
        t0 = time.time()
        while io.input(self.pins[11])==0 and time.time()-t_start<0.0004:
            t0=time.time()
        t1 = time.time()
        while io.input(self.pins[11])==1 and time.time()-t_start<0.0004:
            t1=time.time()
        runtime = time.perf_counter()-t_0
        print(f"distance (front): {runtime:.4f}")
        return runtime
        # if t1-t_start>0.0004:
        #         return inf
        # dt = t1-t0
        # dist = (dt*34300)/2
        # return dist
    def distance_back(self):
        self.setpin(12,1)
        time.sleep(0.00001)
        self.setpin(12,0)
        t_0=time.perf_counter()
        t_start = time.time()
        t0=time.time()
        while io.input(self.pins[13])==0 and time.time()-t_start<0.0004:
            t0=time.time()
        t1=time.time()
        while io.input(self.pins[13])==1 and time.time()-t_start<0.0004:
            t1=time.time()
        runtime = time.perf_counter()-t_0
        print(f"distance (back): {runtime:.4f}\n")
        return runtime
        # if t1-t_start<0.0004:
        #       return inf
        # dt = t1-t0
        # dist = (dt*34300)/2
        # return dist
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
         will be written to {self.logfile}. The ti222ming data visible in the\n\
         terminal during manual control mode will be visible, in auto control\n\
         mode, but only when the FSM is in the 'WAIT' state.\n\n\
         In order to completely end the program, press CTRL+C in the\n\
         terminal or 'q' in the 'Camera' window.\n\n")
        self.cam = cam
        self.manual_setup()
    def callback_SIGUSR1(self,channel): 
        kill(getpid(),SIGUSR1)
    def callback_SIGUSR2(self,channel):
        kill(getpid(),SIGUSR2)
    # Show the camera view in a window while in manual control mode.
    def video_update(self):
        try:
            self.cam.update_goal_position('ball',time.time())
            self.root.after(25,self.video_update) # Call this function every 25ms
        except KeyboardInterrupt:
            self.manual = 0
            for i in range(len(self.pins[:8])):
                self.setpin(i,0)
            self.INT_start_time = time.time()
            self.setpin(7,1)
            time.sleep(0.05)
            self.setpin(7,0)
            writefile(self.logfile,"Exiting manual controls.\nFinal output: "+self.readall()+'\n')
            self.root.destroy()
            writefile(self.logfile,"\nManual control mode exited successfully!\n\n")
    ### MANUAL MOTOR CONTROLS: uses functions from MOTOR CONTROLS
    # Sets up manual motor controls
    def manual_setup(self):
        self.root = Tk()
        self.root.title("Motors GUI")
        self.root.geometry("64x64")
        self.app = Frame(self.root)
        self.app.grid()

        self.root.bind('w',self.forward)
        self.root.bind('a',self.left)
        self.root.bind('s',self.back)
        self.root.bind('d',self.right)
        self.root.bind('q',self.pincers_open)
        self.root.bind('e',self.pincers_close)
        self.root.bind('c',self.camswitch)
        self.root.bind('<space>',self.stop_all)
        self.root.bind('x',self.exit_)
        self.root.bind('<l>',self.clear_terminal)
        if self.gettimes is not None:
            self.root.bind('<Key-1>',self.callback_SIGUSR1_helper)
        self.root.bind('<Key-2>',self.callback_SIGUSR2_helper)
        if self.demo:
            self.video_update()
        self.setpin(6,1)
        self.root.mainloop()
        return
    def stop_all(self,event=None):
        if self.manual==1 and self.instruction==0:
            return
        for i in range(6):
            self.setpin(i,0)
        if self.manual==0:
            self.pi_int()
        else:
            self.INT_start_time = time.time()
            self.setpin(7,1)
            print(decode_signal(self.readall())+self.read(6)+self.read(7),end=' ')
            time.sleep(0.05)
            self.setpin(7,0)
            print(self.read(7))
            self.instruction=0
    # Prove the ability to record response time data for the microcontroller
    # If time data isn't being collected, then this just changes self.DONE 
    # to 'True' and then back to 'False', which does nothing without the FSM.
    def callback_SIGUSR1_helper(self,channel):
        if self.instruction==1:
            return
        self.instruction=1
        self.clear_terminal()
        self.callback_SIGUSR1(channel)
        self.DONE=False
        return
    # Change the proximity attribute (something is within range of the ultrasonic sensors)
    def callback_SIGUSR2_helper(self,channel):
        if self.instruction==1:
            return
        self.instruction=1
        self.clear_terminal()
        self.callback_SIGUSR2(channel)
    def camswitch(self,event=None):
        if self.instruction==1:
            return
        self.instruction=1
        self.cam.camera_.camswitch()
    # Make the car move forward
    def forward(self,event=None):
        if self.instruction==1:
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
        print(decode_signal(self.readall())+self.read(6)+self.read(7),end=' ')
        time.sleep(0.05)
        self.setpin(7,0)
        print(self.read(7))
        self.instruction = 1
        return
    # Make the car turn right
    def right(self,event=None):
        if self.instruction==1:
            return
        self.clear_terminal()
        if self.cam.index==0:
            self.left_move()
        else:
            self.right_move(1)            
        self.INT_start_time = time.time()
        self.setpin(7,1)
        print(decode_signal(self.readall())+self.read(6)+self.read(7),end=' ')
        time.sleep(0.05)
        self.setpin(7,0)
        print(self.read(7))
        self.instruction = 1
        return
    # Make the car turn left
    def left(self,event=None):
        if self.instruction==1:
            return
        self.clear_terminal()
        if self.cam.index==0:
            self.right_move()
        else:
            self.left_move(1)            
        self.INT_start_time = time.time()
        self.setpin(7,1)
        print(decode_signal(self.readall())+self.read(6)+self.read(7),end=' ')
        time.sleep(0.05)
        self.setpin(7,0)
        print(self.read(7))
        self.instruction = 1
        return
    # Make the car move backwards
    def back(self,event=None):
        if self.instruction==1:
            return
        self.clear_terminal()
        if self.cam.index==0:
            self.right_move(1)
            self.left_move(1)
        else:
            self.right_move()
            self.left_move()            
        self.INT_start_time = time.time()
        self.setpin(7,1)
        print(decode_signal(self.readall())+self.read(6)+self.read(7),end=' ')
        time.sleep(0.05)
        self.setpin(7,0)
        print(self.read(7))
        self.instruction = 1
        return
    # Open the pincers
    def pincers_open(self,event=None):
        if self.instruction==1:
            return
        self.clear_terminal()
        if self.instruction==0:
            self.pincers_move(0)
        self.INT_start_time = time.time()
        self.setpin(7,1)
        print(decode_signal(self.readall())+self.read(6)+self.read(7),end=' ')
        time.sleep(0.05)
        self.setpin(7,0)
        print(self.read(7))
        self.instruction = 1
        return
    # Close the pincers
    def pincers_close(self,event=None):
        if self.instruction==1:
            return
        self.clear_terminal()
        if self.instruction==0:
            self.pincers_move(1)
        self.INT_start_time = time.time()
        self.setpin(7,1)
        print(decode_signal(self.readall())+self.read(6)+self.read(7),end=' ')
        time.sleep(0.05)
        self.setpin(7,0)
        print(self.read(7))
        self.instruction = 1  
        return
    # If the user terminates manual control mode, return to auto control mode
    def exit_(self,event=None):
        self.instruction=1
        self.manual = 0
        for i in range(len(self.pins[:8])):
            self.setpin(i,0)
        self.pi_int()
        writefile(self.logfile,"Exiting manual controls.\nFinal output: "+self.readall()+'\n')
        print("Exiting manual controls.\nFinal output: "+self.readall())
        self.root.destroy()
        self.instruction=0
        writefile(self.logfile,"Manual control mode exited successfully!\n\n")
        print("Manual control mode exited successfully!\n\n")
        
    ### MOTOR CONTROLS: use functions from the GENERAL FUNCTIONS to set output signals
    # Make the left motors move forward (reverse=0) or backward (reverse=1).
    def pi_int(self):
        self.INT_start_time = time.time()
        self.setpin(7,1)
        # NOTE: Wait 50 ms for the microcontroller to handle the interrupt.
        # This value may need to be adjusted later.
        time.sleep(0.05) 
        self.setpin(7,0)
    def left_move(self,reverse=0):
        # if self.manual==0 and (int(self.read(0)) ^ reverse):
        #     self.left_stop()
        #     self.pi_int()
        self.setpin(0,reverse)
        self.setpin(1,1)
    # Make the left motors stop
    def left_stop(self):
        self.setpin(0,0)
        self.setpin(1,0)
    # Make the right motors move forward (reverse=0) or backward (reverse=1).
    def right_move(self,reverse=0):
        # if self.manual==0 and (int(self.read(2)) ^ reverse):
        #     self.right_stop()
        #     self.pi_int()
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
        for pin_idx in range(len(self.pins[:8])):
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
    def control_switch(self):
        self.manual = int(not self.manual)
        if self.cam is not None:
            self.cam.manual = self.manual
        if self.manual==0:
            self.init_manual_control(self.cam)
            self.manual = 0
            if self.cam is not None:
                self.cam.manual = 0
        else:
            self.exit_()
        print("Returning to 'auto control mode'...")
        self.manual=0
        if self.cam is not None:
            self.cam.manual=0
        return 0

    def __init__(self,gettimes,noprint,demo,manual,init_time,logfile,num_samples):

def gpio_main():
    ctrl = control(None,0,0,0,0,'init-err.txt',None)
    count=0
    try:
        while True:
            f_avg += ctrl.distance_front()
            b_avg += ctrl.distance_back()
            count+=1
    except KeyboardInterrupt:
        if count>0:
            print(f"Average (front): {f_avg/count:.4f}\nAverage (back): {b_avg/count:.4f}")

if __name__=='__main__':
    gpio_main()